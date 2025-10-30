# jetson/mcp_client.py

import asyncio
import websockets
import json
from typing import Callable, Dict, Optional
import logging
from datetime import datetime
import random

logger = logging.getLogger(__name__)

class MCPClient:
    """Client MCP avec reconnexion automatique robuste"""
    
    def __init__(self, agent_id: str, agent_type: str, mcp_host: str, mcp_port: int = 8081):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.mcp_url = f"ws://{mcp_host}:{mcp_port}/ws/agent/{agent_id}"
        
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.callbacks: Dict[str, Callable] = {}
        self.connected = False
        
        # Reconnexion avec backoff exponentiel
        self.reconnect_delay = 1  # Démarre à 1s
        self.max_reconnect_delay = 60  # Maximum 60s
        self.reconnect_attempts = 0
        
        # Heartbeat
        self.heartbeat_interval = 30  # 30 secondes
        self.heartbeat_task = None
        
        # Flag pour arrêt propre
        self.should_reconnect = True
        
    async def connect(self):
        """Connexion avec reconnexion automatique infinie"""
        while self.should_reconnect:
            try:
                logger.info(f"🔌 Tentative connexion MCP ({self.reconnect_attempts + 1})...")
                
                self.websocket = await websockets.connect(
                    self.mcp_url,
                    ping_interval=20,
                    ping_timeout=10,
                    close_timeout=10
                )
                
                self.connected = True
                self.reconnect_delay = 1  # Reset délai
                self.reconnect_attempts = 0
                
                logger.info("✅ MCP connecté")
                
                # Enregistrer agent
                await self.register()
                
                # Démarrer heartbeat
                self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
                
                # Démarrer écoute
                await self._listen()
                
            except websockets.exceptions.WebSocketException as e:
                logger.error(f"❌ Erreur WebSocket: {e}")
                await self._handle_disconnection()
                
            except Exception as e:
                logger.error(f"❌ Erreur connexion MCP: {e}")
                await self._handle_disconnection()
    
    async def _handle_disconnection(self):
        """Gérer déconnexion et préparer reconnexion"""
        self.connected = False
        
        # Annuler heartbeat
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
        
        if not self.should_reconnect:
            logger.info("🛑 Reconnexion désactivée, arrêt...")
            return
        
        # Backoff exponentiel avec jitter
        self.reconnect_attempts += 1
        jitter = random.uniform(0, 1)
        delay = min(
            self.reconnect_delay * (2 ** min(self.reconnect_attempts - 1, 5)) + jitter,
            self.max_reconnect_delay
        )
        
        logger.warning(
            f"♻️  Reconnexion dans {delay:.1f}s "
            f"(tentative {self.reconnect_attempts})..."
        )
        await asyncio.sleep(delay)
    
    async def disconnect(self):
        """Déconnexion propre (désactive reconnexion)"""
        logger.info("🔌 Déconnexion MCP...")
        self.should_reconnect = False
        self.connected = False
        
        # Annuler heartbeat
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        
        # Fermer WebSocket
        if self.websocket:
            await self.websocket.close()
        
        logger.info("✅ MCP déconnecté")
    
    async def register(self):
        """Enregistrer/réenregistrer agent auprès du MCP"""
        await self.send({
            "type": "register",
            "agent_type": self.agent_type,
            "capabilities": self.get_capabilities(),
            "metadata": self.get_metadata()
        })
        logger.info("📝 Agent (ré)enregistré sur MCP")
    
    async def _listen(self):
        """Écouter messages du serveur avec gestion erreurs"""
        try:
            async for message in self.websocket:
                await self._handle_message(message)
                
        except websockets.exceptions.ConnectionClosedOK:
            logger.info("✅ Connexion fermée proprement")
            
        except websockets.exceptions.ConnectionClosedError as e:
            logger.warning(f"⚠️  Connexion fermée avec erreur: {e}")
            
        except asyncio.CancelledError:
            logger.info("🛑 Écoute annulée")
            raise
            
        except Exception as e:
            logger.error(f"❌ Erreur écoute MCP: {e}")
        
        finally:
            self.connected = False
    
    async def _handle_message(self, message: str):
        """Traiter message reçu"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            # Messages système
            if message_type == "ping":
                await self.send({"type": "pong"})
                return
            
            # Callbacks utilisateur
            if message_type in self.callbacks:
                try:
                    await self.callbacks[message_type](data)
                except Exception as e:
                    logger.error(f"❌ Erreur callback {message_type}: {e}")
            else:
                logger.debug(f"📨 Message MCP non géré: {message_type}")
                
        except json.JSONDecodeError:
            logger.error(f"❌ Message MCP invalide: {message}")
        except Exception as e:
            logger.error(f"❌ Erreur traitement message: {e}")
    
    async def _heartbeat_loop(self):
        """Boucle heartbeat pour maintenir connexion"""
        try:
            while self.connected:
                await asyncio.sleep(self.heartbeat_interval)
                
                if self.connected:
                    try:
                        await self.send({"type": "heartbeat"})
                        logger.debug("💓 Heartbeat envoyé")
                    except Exception as e:
                        logger.error(f"❌ Erreur heartbeat: {e}")
                        # Ne pas lever l'erreur, laisser _listen gérer
                        
        except asyncio.CancelledError:
            logger.debug("🛑 Heartbeat annulé")
    
    def on(self, message_type: str, callback: Callable):
        """Enregistrer callback pour type de message"""
        self.callbacks[message_type] = callback
    
    async def send(self, data: dict):
        """Envoyer message au serveur avec gestion erreurs"""
        if not self.websocket or not self.connected:
            logger.warning("⚠️  Impossible d'envoyer: non connecté")
            return False
        
        try:
            await self.websocket.send(json.dumps(data))
            return True
        except websockets.exceptions.ConnectionClosed:
            logger.warning("⚠️  Connexion fermée pendant envoi")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"❌ Erreur envoi MCP: {e}")
            return False
    
    async def publish_context(self, context_type: str, data: dict, priority: int = 1):
        """Publier contexte avec retry"""
        success = await self.send({
            "type": "context_update",
            "context_type": context_type,
            "data": data,
            "priority": priority,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        if not success:
            logger.warning(
                f"⚠️  Échec publication contexte {context_type}, "
                f"sera réessayé après reconnexion"
            )
    
    async def query(self, query_type: str, parameters: dict = None):
        """Requête au serveur MCP"""
        await self.send({
            "type": "query",
            "query_type": query_type,
            "parameters": parameters or {}
        })
    
    async def request_action(self, target_agent: str, action: str, parameters: dict = None):
        """Demander action à un autre agent"""
        await self.send({
            "type": "action_request",
            "target_agent": target_agent,
            "action": action,
            "parameters": parameters or {}
        })
    
    def get_capabilities(self) -> list:
        """Retourner capacités de l'agent"""
        return [
            "vision",
            "face_recognition",
            "speech_recognition",
            "text_to_speech",
            "natural_language_understanding",
            "llm_inference"
        ]
    
    def get_metadata(self) -> dict:
        """Retourner métadonnées"""
        return {
            "platform": "Jetson Orin Nano Super",
            "location": "Bureau",
            "version": "1.0.0",
            "reconnect_attempts": self.reconnect_attempts
        }