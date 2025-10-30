# jetson/modules/llm_agent.py
import asyncio
from typing import Dict, Any, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class LLMAgent:
    """Agent LLM - Llama 3.1 avec llama.cpp"""
    
    def __init__(self, config: dict):
        self.config = config
        
        # Lazy import llama-cpp-python
        try:
            from llama_cpp import Llama
            self.Llama = Llama
        except ImportError:
            logger.error("❌ llama-cpp-python non installé")
            raise
        
        # Charger modèle
        model_path = config['model']
        self.model = self.Llama(
            model_path=model_path,
            n_ctx=config['context_size'],
            n_gpu_layers=config['gpu_layers'],
            n_threads=4,
            verbose=False
        )
        
        self.temperature = config['temperature']
        self.top_p = config['top_p']
        self.max_tokens = 512
        
        # Historique conversation (en mémoire)
        self.conversation_history = []
        
        logger.info("✅ LLM Agent initialisé")
    
    async def generate(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Générer réponse LLM"""
        
        # Construire prompt complet avec contexte
        full_prompt = self.build_prompt(prompt, context)
        
        # Paramètres
        temp = temperature if temperature is not None else self.temperature
        tp = top_p if top_p is not None else self.top_p
        max_tok = max_tokens if max_tokens is not None else self.max_tokens
        
        # Génération
        try:
            response = await asyncio.to_thread(
                self.model,
                full_prompt,
                max_tokens=max_tok,
                temperature=temp,
                top_p=tp,
                stop=["User:", "Human:", "\n\n\n"]
            )
            
            # Extraire texte
            text = response['choices'][0]['text'].strip()
            
            # Sauvegarder dans historique
            self.conversation_history.append({
                "role": "user",
                "content": prompt
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": text
            })
            
            # Limiter taille historique (garder 10 derniers échanges)
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            return {
                "text": text,
                "tokens": response['usage']['total_tokens']
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
        system = """Tu es un assistant personnel intelligent et serviable. Tu coordonnes plusieurs agents spécialisés pour aider l'utilisateur.

Tu as accès aux capacités suivantes:
- Vision: détection et reconnaissance de personnes
- Audio: écoute et parole
- Actions: envoyer emails, rechercher sur internet, gérer calendrier

Réponds de manière naturelle, concise et utile."""
        
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
            recent = self.conversation_history[-6:]  # 3 échanges
            history_str = "\n\nHistorique récent:\n"
            for msg in recent:
                role = "User" if msg["role"] == "user" else "Assistant"
                history_str += f"{role}: {msg['content']}\n"
        
        # Prompt final
        full_prompt = f"""{system}{context_str}{history_str}

User: {user_input}
Assistant:"""
        
        return full_prompt
    
    def is_loaded(self) -> bool:
        """Vérifier si modèle chargé"""
        return self.model is not None
    
    def clear_history(self):
        """Effacer historique conversation"""
        self.conversation_history = []
    
    def stop(self):
        """Arrêter agent LLM"""
        # Libérer mémoire
        if self.model:
            del self.model
        logger.info("🛑 LLM Agent arrêté")