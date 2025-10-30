# jetson/llm_server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import logging
import time
import uuid

logger = logging.getLogger(__name__)

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "llama-3.1-8b"
    messages: List[Message]
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 512
    stream: bool = False

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]

class LLMServer:
    """
    Serveur LLM compatible API OpenAI
    Permet à n8n d'utiliser le LLM local du Jetson
    """
    def __init__(self, llm_agent, port: int = 8001):
        self.llm = llm_agent
        self.port = port
        self.app = FastAPI(title="Jetson LLM API", version="1.0.0")
        
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.post("/v1/chat/completions")
        async def chat_completions(request: ChatCompletionRequest):
            """Endpoint compatible OpenAI Chat Completions"""
            try:
                # Construire prompt depuis messages
                prompt = self.build_prompt_from_messages(request.messages)
                
                # Générer réponse
                start_time = time.time()
                response = await self.llm.generate(
                    prompt=prompt,
                    temperature=request.temperature,
                    top_p=request.top_p,
                    max_tokens=request.max_tokens
                )
                generation_time = time.time() - start_time
                
                # Format réponse OpenAI
                response_text = response['text']
                prompt_tokens = len(prompt.split())  # Approximation
                completion_tokens = len(response_text.split())
                
                return ChatCompletionResponse(
                    id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
                    created=int(time.time()),
                    model=request.model,
                    choices=[
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": response_text
                            },
                            "finish_reason": "stop"
                        }
                    ],
                    usage={
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": prompt_tokens + completion_tokens
                    }
                )
                
            except Exception as e:
                logger.error(f"❌ Erreur LLM: {e}")
                raise HTTPException(500, str(e))
        
        @self.app.get("/v1/models")
        async def list_models():
            """Liste modèles disponibles"""
            return {
                "object": "list",
                "data": [
                    {
                        "id": "llama-3.1-8b",
                        "object": "model",
                        "created": int(time.time()),
                        "owned_by": "local"
                    }
                ]
            }
        
        @self.app.get("/health")
        async def health():
            return {"status": "healthy", "model_loaded": self.llm.is_loaded()}
    
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
        
        logger.info(f"🧠 LLM Server démarré sur port {self.port}")
        await server.serve()