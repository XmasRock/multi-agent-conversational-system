# jetson/api_server.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import logging

logger = logging.getLogger(__name__)

class ActionRequest(BaseModel):
    action: str
    params: Dict[str, Any]
    priority: int = 1

class StatusResponse(BaseModel):
    status: str
    vision_enabled: bool
    audio_enabled: bool
    llm_enabled: bool
    current_user: Optional[str]
    uptime_seconds: float

class APIServer:
    def __init__(self, agent, port: int = 8000):
        self.agent = agent
        self.port = port
        self.app = FastAPI(title="Jetson Agent API", version="1.0.0")
        
        # CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Routes
        self.setup_routes()
        
        self.start_time = None
    
    def setup_routes(self):
        @self.app.get("/")
        async def root():
            return {
                "service": "Jetson Conversational Agent",
                "version": "1.0.0",
                "agent_id": self.agent.config['agent']['id']
            }
        
        @self.app.get("/health")
        async def health():
            return {"status": "healthy"}
        
        @self.app.get("/status")
        async def status():
            import time
            uptime = time.time() - self.start_time if self.start_time else 0
            
            return StatusResponse(
                status="running" if self.agent.running else "stopped",
                vision_enabled=self.agent.vision is not None,
                audio_enabled=self.agent.audio is not None,
                llm_enabled=self.agent.llm is not None,
                current_user=self.agent.current_user,
                uptime_seconds=uptime
            )
        
        @self.app.post("/action")
        async def handle_action(request: ActionRequest, background_tasks: BackgroundTasks):
            """Endpoint pour actions depuis n8n"""
            logger.info(f"📥 Action reçue: {request.action}")
            
            if request.action == "speak":
                text = request.params.get("text", "")
                if self.agent.audio:
                    background_tasks.add_task(self.agent.audio.speak, text)
                    return {"status": "queued", "action": "speak"}
                else:
                    raise HTTPException(400, "Audio module désactivé")
            
            elif request.action == "analyze_vision":
                if self.agent.vision:
                    results = await self.agent.vision.get_current_results()
                    return {
                        "status": "success",
                        "action": "analyze_vision",
                        "results": results
                    }
                else:
                    raise HTTPException(400, "Vision module désactivé")
            
            elif request.action == "listen":
                if self.agent.audio:
                    # Déjà en écoute continue
                    return {"status": "listening", "action": "listen"}
                else:
                    raise HTTPException(400, "Audio module désactivé")
            
            elif request.action == "generate_text":
                prompt = request.params.get("prompt", "")
                if self.agent.llm:
                    response = await self.agent.llm.generate(
                        prompt=prompt,
                        context=request.params.get("context", {})
                    )
                    return {
                        "status": "success",
                        "action": "generate_text",
                        "response": response
                    }
                else:
                    raise HTTPException(400, "LLM module désactivé")
            
            else:
                raise HTTPException(400, f"Action inconnue: {request.action}")
        
        @self.app.post("/user-detected")
        async def user_detected(user_identity: str, confidence: float):
            """Notification détection utilisateur"""
            self.agent.current_user = user_identity
            
            # Publier au MCP
            await self.agent.mcp_client.publish_context(
                context_type="user_presence",
                data={
                    "user_identity": user_identity,
                    "confidence": confidence
                },
                priority=4
            )
            
            return {"status": "acknowledged"}
        
        @self.app.get("/vision/current")
        async def get_vision_current():
            """Récupérer état actuel vision"""
            if not self.agent.vision:
                raise HTTPException(400, "Vision désactivée")
            
            results = await self.agent.vision.get_current_results()
            return {"results": results}
        
        @self.app.post("/vision/register-face")
        async def register_face(name: str):
            """Enregistrer un nouveau visage"""
            if not self.agent.vision:
                raise HTTPException(400, "Vision désactivée")
            
            success = await self.agent.vision.register_new_face(name)
            
            if success:
                return {"status": "success", "name": name}
            else:
                raise HTTPException(500, "Échec enregistrement visage")
    
    async def start(self):
        """Démarrer serveur API"""
        import time
        self.start_time = time.time()
        
        import uvicorn
        config = uvicorn.Config(
            self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        logger.info(f"🌐 API Server démarré sur port {self.port}")
        await server.serve()