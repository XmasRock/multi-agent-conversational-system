# jetson/modules/action_agent.py
import asyncio
import httpx
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ActionAgent:
    """Agent actions - Interface avec n8n et autres services"""
    
    def __init__(self, config: dict, mqtt_client):
        self.config = config
        self.mqtt = mqtt_client
        
        self.n8n_url = f"http://{config['network']['n8n_server']['host']}:{config['network']['n8n_server']['port']}"
        
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        logger.info("✅ Action Agent initialisé")
    
    async def request_n8n_action(self, action: dict):
        """Envoyer action à n8n pour traitement"""
        try:
            # Webhook n8n
            webhook_url = f"{self.n8n_url}/webhook/agent-input"
            
            response = await self.http_client.post(
                webhook_url,
                json={
                    "action_request": True,
                    "action": action
                }
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Action envoyée à n8n: {action['type']}")
                return response.json()
            else:
                logger.error(f"❌ Erreur n8n: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur requête n8n: {e}")
            return None
    
    async def send_email(self, to: str, subject: str, body: str):
        """Envoyer email via n8n"""
        action = {
            "type": "send_email",
            "params": {
                "to": to,
                "subject": subject,
                "body": body
            }
        }
        return await self.request_n8n_action(action)
    
    async def web_search(self, query: str):
        """Recherche web via n8n"""
        action = {
            "type": "web_search",
            "params": {
                "query": query
            }
        }
        return await self.request_n8n_action(action)
    
    async def calendar_event(self, event_data: dict):
        """Créer événement calendrier via n8n"""
        action = {
            "type": "calendar_event",
            "params": event_data
        }
        return await self.request_n8n_action(action)
    
    def stop(self):
        """Arrêter agent actions"""
        # Fermer client HTTP
        asyncio.create_task(self.http_client.aclose())
        logger.info("🛑 Action Agent arrêté")