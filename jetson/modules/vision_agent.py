# jetson/modules/vision_agent.py
import cv2
import numpy as np
from ultralytics import YOLO
from insightface.app import FaceAnalysis
import pickle
from typing import List, Dict, Optional
import asyncio
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class VisionAgent:
    """Agent vision - YOLOv11 + InsightFace"""
    
    def __init__(self, config: dict):
        self.config = config

        # Détection type caméra
        camera_type = config['camera'].get('type', 'usb')
        
        if camera_type == 'csi':
            # Pipeline GStreamer pour caméra CSI
            self.gst_pipeline = self.build_csi_pipeline(config['camera'])
            self.cap = cv2.VideoCapture(self.gst_pipeline, cv2.CAP_GSTREAMER)
        else:
            # Caméra USB standard
            camera_id = config['camera']['device']
            self.cap = cv2.VideoCapture(camera_id)
        
        # Configuration résolution/FPS
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config['camera']['width'])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config['camera']['height'])
        self.cap.set(cv2.CAP_PROP_FPS, config['camera']['fps'])        
        # Camera
        camera_id = config['camera']['device']
        self.cap = cv2.VideoCapture(camera_id)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config['camera']['width'])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config['camera']['height'])
        self.cap.set(cv2.CAP_PROP_FPS, config['camera']['fps'])
        
        # YOLOv11
        yolo_model = config['yolo']['model']
        self.yolo = YOLO(yolo_model)
        self.conf_threshold = config['yolo']['conf_threshold']
        self.iou_threshold = config['yolo']['iou_threshold']
        
        # InsightFace
        self.face_app = FaceAnalysis(
            name=config['face_recognition']['model'],
            providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
        )
        self.face_app.prepare(ctx_id=0, det_size=(640, 640))
        
        # Base visages connus
        embeddings_file = config['face_recognition']['embeddings_file']
        self.known_faces = self.load_known_faces(embeddings_file)
        self.face_threshold = config['face_recognition']['threshold']
        
        # État
        self.current_frame = None
        self.current_results = []
        
        logger.info("✅ Vision Agent initialisé")
    
    def load_known_faces(self, filepath: str) -> dict:
        """Charger visages connus depuis fichier"""
        path = Path(filepath)
        if path.exists():
            with open(filepath, 'rb') as f:
                return pickle.load(f)
        return {}
    
    def save_known_faces(self, filepath: str):
        """Sauvegarder visages connus"""
        with open(filepath, 'wb') as f:
            pickle.dump(self.known_faces, f)
    
    async def process_frame(self) -> List[Dict]:
        """Capturer et traiter une frame"""
        # Capture
        ret, frame = self.cap.read()
        if not ret:
            logger.warning("⚠️  Échec capture frame")
            return []
        
        self.current_frame = frame
        
        # Détection personnes avec YOLO
        results = await asyncio.to_thread(
            self.yolo.predict,
            frame,
            classes=[0],  # Person class
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            verbose=False
        )
        
        persons = []
        
        if len(results) > 0 and results[0].boxes is not None:
            for box in results[0].boxes.data:
                x1, y1, x2, y2, conf, cls = box.cpu().numpy()
                
                # Crop personne
                person_crop = frame[int(y1):int(y2), int(x1):int(x2)]
                
                if person_crop.size == 0:
                    continue
                
                # Reconnaissance faciale
                identity = await self.recognize_face(person_crop)
                
                persons.append({
                    'bbox': [float(x1), float(y1), float(x2), float(y2)],
                    'confidence': float(conf),
                    'identity': identity
                })
        
        self.current_results = persons
        return persons
    
    async def recognize_face(self, image: np.ndarray) -> str:
        """Reconnaître visage dans image"""
        # Détection visage
        faces = await asyncio.to_thread(self.face_app.get, image)
        
        if not faces or len(faces) == 0:
            return "Unknown"
        
        # Prendre le visage le plus grand
        face = max(faces, key=lambda f: f.bbox[2] * f.bbox[3])
        embedding = face.embedding
        
        # Comparer avec base connue
        if not self.known_faces:
            return "Unknown"
        
        best_match = None
        best_score = self.face_threshold
        
        for name, known_emb in self.known_faces.items():
            # Similarité cosinus
            score = np.dot(embedding, known_emb) / (
                np.linalg.norm(embedding) * np.linalg.norm(known_emb)
            )
            
            if score > best_score:
                best_score = score
                best_match = name
        
        return best_match if best_match else "Unknown"
    
    async def register_new_face(self, name: str) -> bool:
        """Enregistrer nouveau visage depuis frame actuelle"""
        if self.current_frame is None:
            return False
        
        # Détecter visage
        faces = await asyncio.to_thread(self.face_app.get, self.current_frame)
        
        if not faces or len(faces) == 0:
            logger.warning("⚠️  Aucun visage détecté pour enregistrement")
            return False
        
        # Prendre le visage le plus grand
        face = max(faces, key=lambda f: f.bbox[2] * f.bbox[3])
        
        # Sauvegarder embedding
        self.known_faces[name] = face.embedding
        self.save_known_faces(self.config['face_recognition']['embeddings_file'])
        
        logger.info(f"✅ Visage enregistré: {name}")
        return True
    
    async def get_current_results(self) -> List[Dict]:
        """Récupérer derniers résultats"""
        return self.current_results
    
    def stop(self):
        """Arrêter agent vision"""
        if self.cap:
            self.cap.release()
        logger.info("🛑 Vision Agent arrêté")

    def build_csi_pipeline(self, camera_config: dict) -> str:
        """Construire pipeline GStreamer pour caméra CSI"""
        device = camera_config['device']
        width = camera_config['width']
        height = camera_config['height']
        fps = camera_config['fps']
        
        # Pipeline optimisé pour Jetson + caméra CSI
        pipeline = (
            f"nvarguscamerasrc sensor-id={device} ! "
            f"video/x-raw(memory:NVMM), width={width}, height={height}, "
            f"format=NV12, framerate={fps}/1 ! "
            f"nvvidconv flip-method=0 ! "
            f"video/x-raw, width={width}, height={height}, format=BGRx ! "
            f"videoconvert ! "
            f"video/x-raw, format=BGR ! "
            f"appsink"
        )
        
        logger.info(f"📹 Pipeline CSI: {pipeline}")
        return pipeline