# jetson/modules/mqtt_client.py

import asyncio
from typing import Callable, Optional
import logging
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)

class MQTTClient:
    """Client MQTT avec reconnexion automatique robuste"""
    
    def __init__(self, broker_host: str, broker_port: int = 1883, client_id: str = "jetson"):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id
        
        self.client = mqtt.Client(client_id=client_id)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        
        self.connected = False
        self.should_reconnect = True
        self.message_callback: Optional[Callable] = None
        
        # Topics souscrits (pour réabonnement)
        self.subscribed_topics = set()
        
        # Reconnexion automatique native Paho
        self.client.reconnect_delay_set(min_delay=1, max_delay=60)
        
        logger.info("✅ MQTT Client initialisé")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback connexion avec codes d'erreur"""
        if rc == 0:
            self.connected = True
            logger.info("✅ MQTT connecté")
            
            # Réabonner à tous les topics
            if self.subscribed_topics:
                logger.info(f"🔄 Réabonnement à {len(self.subscribed_topics)} topics...")
                for topic in self.subscribed_topics:
                    self.client.subscribe(topic)
                    logger.info(f"📬 Réabonné à: {topic}")
        else:
            error_messages = {
                1: "Protocol version incorrect",
                2: "Client ID invalide",
                3: "Serveur indisponible",
                4: "Username/password incorrect",
                5: "Non autorisé"
            }
            logger.error(
                f"❌ MQTT connexion échouée: "
                f"{error_messages.get(rc, f'Code {rc}')}"
            )
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback déconnexion avec gestion auto-reconnect"""
        self.connected = False
        
        if rc == 0:
            logger.info("✅ MQTT déconnecté proprement")
        else:
            logger.warning(
                f"⚠️  MQTT déconnecté (code {rc}), "
                f"reconnexion automatique..."
            )
            # Paho MQTT gère la reconnexion automatiquement
    
    def _on_message(self, client, userdata, msg):
        """Callback message reçu"""
        if self.message_callback:
            try:
                asyncio.create_task(
                    self.message_callback(msg.topic, msg.payload.decode())
                )
            except Exception as e:
                logger.error(f"❌ Erreur callback message: {e}")
    
    async def connect(self):
        """Connexion au broker avec retry"""
        max_attempts = 5
        attempt = 0
        
        while attempt < max_attempts and self.should_reconnect:
            try:
                attempt += 1
                logger.info(f"🔌 Connexion MQTT (tentative {attempt}/{max_attempts})...")
                
                self.client.connect(
                    self.broker_host,
                    self.broker_port,
                    keepalive=60
                )
                self.client.loop_start()
                
                # Attendre connexion
                for _ in range(20):  # 10 secondes max
                    if self.connected:
                        logger.info("✅ MQTT connecté avec succès")
                        return True
                    await asyncio.sleep(0.5)
                
                logger.warning("⚠️  Timeout connexion MQTT")
                
            except Exception as e:
                logger.error(f"❌ Erreur connexion MQTT: {e}")
                
                if attempt < max_attempts:
                    delay = min(2 ** attempt, 30)
                    logger.info(f"♻️  Nouvelle tentative dans {delay}s...")
                    await asyncio.sleep(delay)
        
        if not self.connected:
            logger.error("❌ Échec connexion MQTT après toutes les tentatives")
            return False
        
        return True
    
    async def disconnect(self):
        """Déconnexion propre"""
        self.should_reconnect = False
        self.client.loop_stop()
        self.client.disconnect()
        self.connected = False
        logger.info("🔌 MQTT déconnecté")
    
    async def subscribe(self, topic: str, qos: int = 0):
        """S'abonner à un topic avec mémorisation"""
        self.subscribed_topics.add(topic)
        
        if self.connected:
            self.client.subscribe(topic, qos=qos)
            logger.info(f"📬 Abonné à: {topic}")
        else:
            logger.warning(f"⚠️  Topic mémorisé (abonnement lors de reconnexion): {topic}")
    
    async def publish(self, topic: str, payload: str, qos: int = 0, retain: bool = False):
        """Publier message avec retry"""
        if not self.connected:
            logger.warning(f"⚠️  Publication impossible (non connecté): {topic}")
            return False
        
        try:
            result = self.client.publish(topic, payload, qos=qos, retain=retain)
            
            # Attendre confirmation si QoS > 0
            if qos > 0:
                result.wait_for_publish(timeout=5)
            
            logger.debug(f"📤 MQTT publié: {topic}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur publication MQTT: {e}")
            return False
    
    def on_message(self, callback: Callable):
        """Enregistrer callback pour messages"""
        self.message_callback = callback