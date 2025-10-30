# jetson/llm_server.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import httpx
import logging
import time
import uuid

logger = logging.getLogger(__name__)

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "llama3.1:8b"
    messages: List[Message]
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 512
    stream: bool = False

class LLMServer:
    """Serveur LLM API OpenAI-compatible utilisant Ollama"""
    
    def __init__(self, ollama_host: str = "localhost", ollama_port: int = 11434, port: int = 8001):
        self.ollama_url = f"http://{ollama_host}:{ollama_port}"
        self.port = port
        self.app = FastAPI(title="Jetson LLM API (Ollama)", version="1.0.0")
        
        self.client = httpx.AsyncClient(timeout=60.0)
        
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.post("/v1/chat/completions")
        async def chat_completions(request: ChatCompletionRequest):
            """Endpoint compatible OpenAI Chat Completions"""
            try:
                # Construire prompt depuis messages
                prompt = self.build_prompt_from_messages(request.messages)
                
                # Appeler Ollama
                payload = {
                    "model": request.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": request.temperature,
                        "top_p": request.top_p,
                        "num_predict": request.max_tokens
                    }
                }
                
                start_time = time.time()
                response = await self.client.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload
                )
                generation_time = time.time() - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get('response', '').strip()
                    
                    # Format OpenAI
                    return {
                        "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                        "object": "chat.completion",
                        "created": int(time.time()),
                        "model": request.model,
                        "choices": [
                            {
                                "index": 0,
                                "message": {
                                    "role": "assistant",
                                    "content": response_text
                                },
                                "finish_reason": "stop"
                            }
                        ],
                        "usage": {
                            "prompt_tokens": len(prompt.split()),
                            "completion_tokens": result.get('eval_count', 0),
                            "total_tokens": len(prompt.split()) + result.get('eval_count', 0)
                        }
                    }
                else:
                    raise HTTPException(500, f"Ollama error: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Erreur LLM: {e}")
                raise HTTPException(500, str(e))
        
        @self.app.get("/v1/models")
        async def list_models():
            """Liste modèles Ollama disponibles"""
            try:
                response = await self.client.get(f"{self.ollama_url}/api/tags")
                if response.status_code == 200:
                    models = response.json().get('models', [])
                    return {
                        "object": "list",
                        "data": [
                            {
                                "id": m['name'],
                                "object": "model",
                                "created": int(time.time()),
                                "owned_by": "ollama"
                            }
                            for m in models
                        ]
                    }
                return {"object": "list", "data": []}
            except Exception as e:
                logger.error(f"❌ Erreur liste modèles: {e}")
                return {"object": "list", "data": []}
        
        @self.app.get("/health")
        async def health():
            """Health check"""
            try:
                response = await self.client.get(f"{self.ollama_url}/api/tags", timeout=5.0)
                return {
                    "status": "healthy" if response.status_code == 200 else "degraded",
                    "ollama": "connected" if response.status_code == 200 else "disconnected"
                }
            except:
                return {"status": "unhealthy", "ollama": "disconnected"}
    
    def build_prompt_from_messages(self, messages: List[Message]) -> str:
        """Construire prompt depuis format OpenAI messages"""
        prompt_parts = []
        
        for msg in messages:
            if msg.role == "system":
                prompt_parts.append(f"System: {msg.content}")
            elif msg.role == "user":
                prompt_parts.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                prompt_parts.append(f"Assistant: {msg.content}")
        
        prompt_parts.append("Assistant:")
        return "\n\n".join(prompt_parts)
    
    async def start(self):
        """Démarrer serveur LLM"""
        import uvicorn
        config = uvicorn.Config(
            self.app,
            host="0.0.0.0",
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        logger.info(f"🧠 LLM Server (Ollama) démarré sur port {self.port}")
        await server.serve()