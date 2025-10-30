# jetson/modules/llm_agent.py

import asyncio
import httpx
from typing import Dict, Any, Optional, List
import logging
import json

logger = logging.getLogger(__name__)

class LLMAgent:
    """Agent LLM utilisant Ollama"""
    
    def __init__(self, config: dict):
        self.config = config
        
        # Configuration Ollama
        ollama_config = config.get('ollama', {})
        self.host = ollama_config.get('host', 'localhost')
        self.port = ollama_config.get('port', 11434)
        self.base_url = f"http://{self.host}:{self.port}"
        
        self.model = ollama_config.get('model', 'llama3.1:8b')
        self.temperature = ollama_config.get('temperature', 0.7)
        self.top_p = ollama_config.get('top_p', 0.9)
        self.top_k = ollama_config.get('top_k', 40)
        self.num_ctx = ollama_config.get('num_ctx', 8192)
        self.repeat_penalty = ollama_config.get('repeat_penalty', 1.1)
        
        # HTTP Client
        self.client = httpx.AsyncClient(timeout=60.0)
        
        # Historique conversation
        self.conversation_history = []
        
        # Vérifier connexion
        asyncio.create_task(self.check_connection())
        
        logger.info(f"✅ LLM Agent initialisé (Ollama: {self.model})")
    
    async def check_connection(self):
        """Vérifier connexion Ollama"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                logger.info(f"📦 Modèles Ollama disponibles: {', '.join(model_names)}")
                
                # Vérifier si le modèle configuré existe
                if not any(self.model in name for name in model_names):
                    logger.warning(
                        f"⚠️  Modèle '{self.model}' non trouvé. "
                        f"Téléchargez-le: ollama pull {self.model}"
                    )
            else:
                logger.error("❌ Ollama non accessible")
        except Exception as e:
            logger.error(f"❌ Erreur connexion Ollama: {e}")
    
    async def generate(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Générer réponse avec Ollama"""
        
        # Construire prompt avec contexte
        full_prompt = self.build_prompt(prompt, context)
        
        # Paramètres
        temp = temperature if temperature is not None else self.temperature
        
        # Payload Ollama
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": stream,
            "options": {
                "temperature": temp,
                "top_p": self.top_p,
                "top_k": self.top_k,
                "num_ctx": self.num_ctx,
                "repeat_penalty": self.repeat_penalty,
                "num_predict": max_tokens or 512
            }
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=60.0
            )
            
            if response.status_code == 200:
                if stream:
                    # Streaming non implémenté ici
                    return await self._handle_stream(response)
                else:
                    result = response.json()
                    text = result.get('response', '').strip()
                    
                    # Sauvegarder historique
                    self.conversation_history.append({
                        "role": "user",
                        "content": prompt
                    })
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": text
                    })
                    
                    # Limiter historique
                    if len(self.conversation_history) > 20:
                        self.conversation_history = self.conversation_history[-20:]
                    
                    return {
                        "text": text,
                        "model": self.model,
                        "tokens": result.get('eval_count', 0),
                        "context": result.get('context', [])
                    }
            else:
                logger.error(f"❌ Ollama erreur: {response.status_code}")
                return {
                    "text": "Désolé, je rencontre un problème technique.",
                    "tokens": 0
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur génération LLM: {e}")
            return {
                "text": "Désolé, je rencontre un problème technique.",
                "tokens": 0
            }
    
    def build_prompt(self, user_input: str, context: Optional[Dict] = None) -> str:
        """Construire prompt avec contexte"""
        
        # System prompt
        system = """Tu es un assistant personnel intelligent et serviable nommé Claude. Tu coordonnes plusieurs agents spécialisés pour aider l'utilisateur.

Tu as accès aux capacités suivantes:
- Vision: détection et reconnaissance de personnes
- Audio: écoute et parole
- Actions: envoyer emails, rechercher sur internet, gérer calendrier

Réponds de manière naturelle, concise et utile en français."""
        
        # Contexte utilisateur
        context_str = ""
        if context:
            user_id = context.get("user_identity", "Inconnu")
            location = context.get("location", "")
            time = context.get("time", "")
            
            context_str = f"\n\nContexte actuel:\n- Utilisateur: {user_id}"
            if location:
                context_str += f"\n- Localisation: {location}"
            if time:
                context_str += f"\n- Heure: {time}"
        
        # Historique conversation (3 derniers échanges)
        history_str = ""
        if len(self.conversation_history) > 0:
            recent = self.conversation_history[-6:]
            history_str = "\n\nHistorique récent:\n"
            for msg in recent:
                role = "Utilisateur" if msg["role"] == "user" else "Assistant"
                history_str += f"{role}: {msg['content']}\n"
        
        # Prompt final
        full_prompt = f"""{system}{context_str}{history_str}

Utilisateur: {user_input}
Assistant:"""
        
        return full_prompt
    
    async def switch_model(self, model_name: str) -> bool:
        """Changer de modèle Ollama"""
        try:
            # Vérifier si modèle existe
            response = await self.client.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                
                if model_name in model_names or any(model_name in name for name in model_names):
                    self.model = model_name
                    logger.info(f"✅ Modèle changé: {model_name}")
                    
                    # Effacer historique (contexte différent)
                    self.conversation_history = []
                    return True
                else:
                    logger.error(f"❌ Modèle '{model_name}' non disponible")
                    logger.info(f"📦 Modèles disponibles: {', '.join(model_names)}")
                    return False
        except Exception as e:
            logger.error(f"❌ Erreur changement modèle: {e}")
            return False
    
    async def list_models(self) -> List[str]:
        """Lister modèles Ollama disponibles"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [m['name'] for m in models]
            return []
        except Exception as e:
            logger.error(f"❌ Erreur liste modèles: {e}")
            return []
    
    def is_loaded(self) -> bool:
        """Vérifier si modèle chargé (toujours vrai avec Ollama)"""
        return True
    
    def clear_history(self):
        """Effacer historique conversation"""
        self.conversation_history = []
    
    async def stop(self):
        """Arrêter agent LLM"""
        await self.client.aclose()
        logger.info("🛑 LLM Agent arrêté")