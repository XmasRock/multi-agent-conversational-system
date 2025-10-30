# raspberry-pi/mcp-server/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import asyncio
import json
import logging
from datetime import datetime
import uuid

from connection_manager import ConnectionManager
from storage import StorageManager
from models import (
    AgentRegistration,
    ContextUpdate,
    AgentQuery,
    ActionRequest,
    ActionResponse
)

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="MCP Server",
    description="Model Context Protocol - Hub Central Multi-Agents",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Managers globaux
connection_manager = ConnectionManager()
storage_manager = StorageManager()

# ============================================================================
# LIFECYCLE
# ============================================================================

@app.on_event("startup")
async def startup():
    """Initialisation au démarrage"""
    logger.info("🚀 Démarrage MCP Server...")
    await storage_manager.connect()
    logger.info("✅ MCP Server prêt")

@app.on_event("shutdown")
async def shutdown():
    """Nettoyage à l'arrêt"""
    logger.info("🛑 Arrêt MCP Server...")
    await storage_manager.disconnect()
    logger.info("✅ MCP Server arrêté proprement")

# ============================================================================
# WEBSOCKET - Communication Agents
# ============================================================================

@app.websocket("/ws/agent/{agent_id}")
async def agent_websocket(websocket: WebSocket, agent_id: str):
    """
    WebSocket endpoint pour connexion agents.
    Permet communication bidirectionnelle temps réel.
    """
    await connection_manager.connect(agent_id, websocket)
    logger.info(f"✅ Agent connecté: {agent_id}")
    
    try:
        # Envoyer confirmation
        await websocket.send_json({
            "type": "connection_established",
            "agent_id": agent_id,
            "server_time": datetime.utcnow().isoformat(),
            "message": "Connexion MCP établie"
        })
        
        # Boucle écoute messages
        while True:
            data = await websocket.receive_json()
            await handle_agent_message(agent_id, data)
            
    except WebSocketDisconnect:
        connection_manager.disconnect(agent_id)
        logger.info(f"❌ Agent déconnecté: {agent_id}")
        
        # Notifier autres agents
        await connection_manager.broadcast({
            "type": "agent_left",
            "agent_id": agent_id,
            "timestamp": datetime.utcnow().isoformat()
        }, exclude=agent_id)
        
        # Mettre à jour statut en DB
        await storage_manager.update_agent_status(agent_id, "offline")
        
    except Exception as e:
        logger.error(f"❌ Erreur WebSocket {agent_id}: {e}")
        connection_manager.disconnect(agent_id)

async def handle_agent_message(agent_id: str, data: dict):
    """Router les messages agents selon leur type"""
    message_type = data.get("type")
    
    handlers = {
        "register": handle_registration,
        "context_update": handle_context_update,
        "query": handle_query,
        "action_request": handle_action_request,
        "heartbeat": handle_heartbeat
    }
    
    handler = handlers.get(message_type)
    if handler:
        await handler(agent_id, data)
    else:
        logger.warning(f"⚠️ Type de message inconnu: {message_type}")

# ============================================================================
# HANDLERS
# ============================================================================

async def handle_registration(agent_id: str, data: dict):
    """Enregistrer un nouvel agent"""
    registration = AgentRegistration(
        agent_id=agent_id,
        agent_type=data.get("agent_type"),
        capabilities=data.get("capabilities", []),
        metadata=data.get("metadata", {})
    )
    
    # Stocker métadonnées
    connection_manager.register_agent(agent_id, registration.dict())
    
    # Persister en DB
    await storage_manager.register_agent(registration)
    
    logger.info(f"📝 Agent enregistré: {agent_id} ({registration.agent_type})")
    
    # Notifier autres agents
    await connection_manager.broadcast({
        "type": "agent_joined",
        "agent_id": agent_id,
        "agent_type": registration.agent_type,
        "capabilities": registration.capabilities,
        "timestamp": datetime.utcnow().isoformat()
    }, exclude=agent_id)

async def handle_context_update(agent_id: str, data: dict):
    """Traiter mise à jour de contexte"""
    context = ContextUpdate(
        agent_id=agent_id,
        context_type=data["context_type"],
        data=data["data"],
        timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
        priority=data.get("priority", 1)
    )
    
    # Stocker en cache Redis (TTL 1h)
    await storage_manager.cache_context(context)
    
    # Persister en PostgreSQL
    await storage_manager.store_context(context)
    
    logger.info(
        f"📊 Contexte mis à jour: {agent_id} - {context.context_type} "
        f"(priorité {context.priority})"
    )
    
    # Broadcast si haute priorité
    if context.priority >= 3:
        await connection_manager.broadcast({
            "type": "context_notification",
            "from_agent": agent_id,
            "context": context.dict()
        }, exclude=agent_id)

async def handle_query(agent_id: str, data: dict):
    """Traiter requête contexte"""
    query = AgentQuery(
        requesting_agent=agent_id,
        query_type=data["query_type"],
        parameters=data.get("parameters", {})
    )
    
    # Router selon type de requête
    if query.query_type == "get_current_context":
        response = await get_current_context(query)
    elif query.query_type == "search_memory":
        response = await search_memory(query)
    elif query.query_type == "get_agent_state":
        response = await get_agent_state(query)
    elif query.query_type == "get_conversation_history":
        response = await get_conversation_history(query)
    else:
        response = {
            "type": "query_response",
            "error": f"Type de requête inconnu: {query.query_type}"
        }
    
    # Renvoyer réponse à l'agent
    await connection_manager.send_to_agent(agent_id, response)

async def handle_action_request(agent_id: str, data: dict):
    """Router demande d'action vers agent cible"""
    action = ActionRequest(
        requesting_agent=agent_id,
        target_agent=data["target_agent"],
        action=data["action"],
        parameters=data.get("parameters", {}),
        request_id=data.get("request_id", str(uuid.uuid4()))
    )
    
    # Vérifier que l'agent cible existe
    if not connection_manager.is_agent_connected(action.target_agent):
        await connection_manager.send_to_agent(agent_id, {
            "type": "action_response",
            "request_id": action.request_id,
            "status": "error",
            "error": f"Agent cible non connecté: {action.target_agent}"
        })
        return
    
    # Logger action
    await storage_manager.log_action(action)
    
    # Transmettre à l'agent cible
    await connection_manager.send_to_agent(action.target_agent, {
        "type": "action_request",
        "from_agent": agent_id,
        "action": action.action,
        "parameters": action.parameters,
        "request_id": action.request_id
    })
    
    logger.info(
        f"🎯 Action routée: {agent_id} → {action.target_agent} "
        f"({action.action})"
    )


async def handle_heartbeat(agent_id: str, data: dict):
    """Heartbeat agent (mise à jour last_seen)"""
    connection_manager.update_heartbeat(agent_id)
    await storage_manager.update_agent_last_seen(agent_id)
    
    # Optionnel: répondre avec pong
    await connection_manager.send_to_agent(agent_id, {
        "type": "pong",
        "server_time": datetime.utcnow().isoformat()
    })

# ============================================================================
# QUERY HANDLERS
# ============================================================================

async def get_current_context(query: AgentQuery) -> dict:
    """Récupérer contexte actuel de tous les agents"""
    contexts = await storage_manager.get_all_current_contexts()
    
    return {
        "type": "query_response",
        "query_type": "get_current_context",
        "data": contexts,
        "timestamp": datetime.utcnow().isoformat()
    }

async def search_memory(query: AgentQuery) -> dict:
    """Rechercher dans l'historique de contexte"""
    search_term = query.parameters.get("search", "")
    agent_filter = query.parameters.get("agent_id")
    context_type_filter = query.parameters.get("context_type")
    limit = query.parameters.get("limit", 10)
    
    results = await storage_manager.search_context_history(
        search_term=search_term,
        agent_id=agent_filter,
        context_type=context_type_filter,
        limit=limit
    )
    
    return {
        "type": "query_response",
        "query_type": "search_memory",
        "data": results,
        "count": len(results),
        "timestamp": datetime.utcnow().isoformat()
    }

async def get_agent_state(query: AgentQuery) -> dict:
    """Récupérer état d'un agent spécifique"""
    target_agent = query.parameters.get("agent_id")
    
    if not target_agent:
        return {
            "type": "query_response",
            "error": "agent_id requis"
        }
    
    metadata = connection_manager.get_agent_metadata(target_agent)
    state = await storage_manager.get_agent_info(target_agent)
    
    return {
        "type": "query_response",
        "query_type": "get_agent_state",
        "data": {
            "agent_id": target_agent,
            "connected": connection_manager.is_agent_connected(target_agent),
            "metadata": metadata,
            "database_info": state
        },
        "timestamp": datetime.utcnow().isoformat()
    }

async def get_conversation_history(query: AgentQuery) -> dict:
    """Récupérer historique de conversation"""
    user_id = query.parameters.get("user_id")
    limit = query.parameters.get("limit", 50)
    
    history = await storage_manager.get_conversation_history(user_id, limit)
    
    return {
        "type": "query_response",
        "query_type": "get_conversation_history",
        "data": history,
        "count": len(history),
        "timestamp": datetime.utcnow().isoformat()
    }

# ============================================================================
# REST API - Pour n8n et outils externes
# ============================================================================

@app.get("/")
async def root():
    """Info API"""
    return {
        "service": "MCP Server",
        "version": "1.0.0",
        "status": "running",
        "agents_connected": len(connection_manager.active_connections),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check"""
    redis_ok = await storage_manager.check_redis()
    postgres_ok = await storage_manager.check_postgres()
    
    return {
        "status": "healthy" if (redis_ok and postgres_ok) else "degraded",
        "redis": "ok" if redis_ok else "error",
        "postgres": "ok" if postgres_ok else "error",
        "agents_connected": len(connection_manager.active_connections),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/agents")
async def list_agents():
    """Liste tous les agents (connectés + DB)"""
    connected_agents = [
        {
            "agent_id": aid,
            "status": "connected",
            **metadata
        }
        for aid, metadata in connection_manager.agent_metadata.items()
    ]
    
    db_agents = await storage_manager.get_all_agents()
    
    return {
        "connected": connected_agents,
        "all_registered": db_agents,
        "count_connected": len(connected_agents),
        "count_total": len(db_agents)
    }

@app.post("/context/update")
async def update_context_rest(update: ContextUpdate):
    """API REST pour mise à jour contexte (utilisé par n8n)"""
    await handle_context_update(update.agent_id, update.dict())
    return {"status": "success", "timestamp": datetime.utcnow().isoformat()}

@app.post("/query")
async def query_context_rest(query: AgentQuery):
    """API REST pour requêtes (utilisé par n8n)"""
    if query.query_type == "get_current_context":
        response = await get_current_context(query)
    elif query.query_type == "search_memory":
        response = await search_memory(query)
    elif query.query_type == "get_agent_state":
        response = await get_agent_state(query)
    elif query.query_type == "get_conversation_history":
        response = await get_conversation_history(query)
    else:
        raise HTTPException(400, "Type de requête invalide")
    
    return response

@app.post("/action/request")
async def request_action_rest(action: ActionRequest):
    """API REST pour demander une action (utilisé par n8n)"""
    await handle_action_request(action.requesting_agent, action.dict())
    return {
        "status": "queued",
        "request_id": action.request_id,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/broadcast")
async def broadcast_message(message: dict, exclude: Optional[str] = None):
    """Broadcast message à tous les agents"""
    await connection_manager.broadcast(message, exclude=exclude)
    return {
        "status": "broadcasted",
        "recipients": len(connection_manager.active_connections) - (1 if exclude else 0),
        "timestamp": datetime.utcnow().isoformat()
    }

# ============================================================================
# STATS & MONITORING
# ============================================================================

@app.get("/stats")
async def get_stats():
    """Statistiques système"""
    stats = await storage_manager.get_stats()
    
    return {
        "agents": {
            "connected": len(connection_manager.active_connections),
            "registered": stats.get("total_agents", 0)
        },
        "contexts": {
            "total_stored": stats.get("total_contexts", 0),
            "last_24h": stats.get("contexts_24h", 0)
        },
        "actions": {
            "total_executed": stats.get("total_actions", 0),
            "last_hour": stats.get("actions_1h", 0)
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/agents/status")
async def agents_status():
    """Status détaillé agents avec historique reconnexions"""
    agents_info = []
    
    for agent_id, metadata in connection_manager.agent_metadata.items():
        connected = connection_manager.is_agent_connected(agent_id)
        
        # Dernière activité
        last_hb = connection_manager.last_heartbeat.get(agent_id)
        seconds_since_hb = None
        if last_hb:
            seconds_since_hb = (datetime.utcnow() - last_hb).seconds
        
        agents_info.append({
            "agent_id": agent_id,
            "agent_type": metadata.get("agent_type"),
            "status": "connected" if connected else "disconnected",
            "connected_at": metadata.get("connected_at"),
            "disconnected_at": metadata.get("disconnected_at"),
            "reconnected": metadata.get("reconnected", False),
            "last_heartbeat_seconds_ago": seconds_since_hb,
            "reconnect_attempts": metadata.get("reconnect_attempts", 0)
        })
    
    return {
        "agents": agents_info,
        "total": len(agents_info),
        "connected": sum(1 for a in agents_info if a["status"] == "connected"),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/metrics")
async def prometheus_metrics():
    """Métriques format Prometheus"""
    stats = await storage_manager.get_stats()
    
    metrics = f"""
# HELP mcp_agents_connected Number of connected agents
# TYPE mcp_agents_connected gauge
mcp_agents_connected {len(connection_manager.active_connections)}

# HELP mcp_contexts_total Total contexts stored
# TYPE mcp_contexts_total counter
mcp_contexts_total {stats.get("total_contexts", 0)}

# HELP mcp_actions_total Total actions executed
# TYPE mcp_actions_total counter
mcp_actions_total {stats.get("total_actions", 0)}
"""
    
    return metrics

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        log_level="info"
    )