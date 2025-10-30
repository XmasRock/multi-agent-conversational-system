# raspberry-pi/mcp-server/connection_manager.py

from fastapi import WebSocket
from typing import Dict, Optional
import logging
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.agent_metadata: Dict[str, dict] = {}
        self.last_heartbeat: Dict[str, datetime] = {}
        
        # Timeout heartbeat
        self.heartbeat_timeout = 60  # 60 secondes
        
        # Démarrer surveillance heartbeat
        asyncio.create_task(self._monitor_heartbeats())
    
    async def connect(self, agent_id: str, websocket: WebSocket):
        """Accepter connexion agent"""
        await websocket.accept()
        self.active_connections[agent_id] = websocket
        self.last_heartbeat[agent_id] = datetime.utcnow()
        logger.info(f"✅ WebSocket ouvert: {agent_id}")
    
    def disconnect(self, agent_id: str):
        """Déconnecter agent"""
        if agent_id in self.active_connections:
            del self.active_connections[agent_id]
        if agent_id in self.agent_metadata:
            # Garder metadata pour reconnexion
            self.agent_metadata[agent_id]["status"] = "disconnected"
            self.agent_metadata[agent_id]["disconnected_at"] = datetime.utcnow().isoformat()
        if agent_id in self.last_heartbeat:
            del self.last_heartbeat[agent_id]
        logger.info(f"❌ WebSocket fermé: {agent_id}")
    
    def update_heartbeat(self, agent_id: str):
        """Mettre à jour timestamp heartbeat"""
        self.last_heartbeat[agent_id] = datetime.utcnow()
    
    async def _monitor_heartbeats(self):
        """Surveiller heartbeats et détecter agents morts"""
        while True:
            try:
                await asyncio.sleep(30)  # Vérifier toutes les 30s
                
                now = datetime.utcnow()
                timeout = timedelta(seconds=self.heartbeat_timeout)
                
                # Vérifier chaque agent connecté
                disconnected = []
                for agent_id, last_hb in list(self.last_heartbeat.items()):
                    if now - last_hb > timeout:
                        logger.warning(
                            f"⚠️  Agent {agent_id} timeout "
                            f"(dernier heartbeat il y a {(now - last_hb).seconds}s)"
                        )
                        
                        # Fermer connexion
                        if agent_id in self.active_connections:
                            try:
                                await self.active_connections[agent_id].close()
                            except:
                                pass
                        
                        disconnected.append(agent_id)
                
                # Nettoyer agents timeout
                for agent_id in disconnected:
                    self.disconnect(agent_id)
                    
                    # Broadcast déconnexion
                    await self.broadcast({
                        "type": "agent_timeout",
                        "agent_id": agent_id,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
            except Exception as e:
                logger.error(f"❌ Erreur monitor heartbeats: {e}")
    
    def register_agent(self, agent_id: str, metadata: dict):
        """Enregistrer métadonnées agent"""
        # Si agent existait déjà (reconnexion)
        if agent_id in self.agent_metadata:
            old_metadata = self.agent_metadata[agent_id]
            logger.info(
                f"🔄 Reconnexion agent {agent_id} "
                f"(hors ligne depuis {old_metadata.get('disconnected_at', 'inconnu')})"
            )
        
        self.agent_metadata[agent_id] = {
            **metadata,
            "status": "connected",
            "connected_at": datetime.utcnow().isoformat(),
            "reconnected": agent_id in self.agent_metadata
        }
        
    def register_agent(self, agent_id: str, metadata: dict):
        """Enregistrer métadonnées agent"""
        self.agent_metadata[agent_id] = {
            **metadata,
            "connected_at": datetime.utcnow().isoformat()
        }
    
    def is_agent_connected(self, agent_id: str) -> bool:
        """Vérifier si agent connecté"""
        return agent_id in self.active_connections
    
    def get_agent_metadata(self, agent_id: str) -> Optional[dict]:
        """Récupérer métadonnées agent"""
        return self.agent_metadata.get(agent_id)
    
    async def send_to_agent(self, agent_id: str, message: dict):
        """Envoyer message à un agent spécifique"""
        if agent_id in self.active_connections:
            try:
                await self.active_connections[agent_id].send_json(message)
                logger.debug(f"📤 Message envoyé à {agent_id}")
            except Exception as e:
                logger.error(f"❌ Erreur envoi à {agent_id}: {e}")
                self.disconnect(agent_id)
    
    async def broadcast(self, message: dict, exclude: Optional[str] = None):
        """Broadcast à tous les agents sauf exclude"""
        disconnected = []
        
        for agent_id, connection in self.active_connections.items():
            if agent_id != exclude:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"❌ Erreur broadcast à {agent_id}: {e}")
                    disconnected.append(agent_id)
        
        # Nettoyer connexions mortes
        for agent_id in disconnected:
            self.disconnect(agent_id)
        
        logger.debug(
            f"📢 Broadcast à {len(self.active_connections) - (1 if exclude else 0)} agents"
        )