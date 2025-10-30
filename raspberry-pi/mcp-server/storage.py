# raspberry-pi/mcp-server/storage.py
import redis.asyncio as redis
import asyncpg
import json
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging
import os

from models import AgentRegistration, ContextUpdate, ActionRequest

logger = logging.getLogger(__name__)

class StorageManager:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.pg_pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Connexion Redis et PostgreSQL"""
        # Redis
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        self.redis_client = await redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=5
        )
        logger.info("✅ Redis connecté")
        
        # PostgreSQL
        postgres_url = os.getenv(
            "POSTGRES_URL",
            "postgresql://mcpuser:password@postgres:5432/mcp"
        )
        self.pg_pool = await asyncpg.create_pool(
            postgres_url,
            min_size=2,
            max_size=10,
            timeout=30
        )
        logger.info("✅ PostgreSQL connecté")
    
    async def disconnect(self):
        """Fermeture connexions"""
        if self.redis_client:
            await self.redis_client.close()
        if self.pg_pool:
            await self.pg_pool.close()
        logger.info("✅ Connexions fermées")
    
    async def check_redis(self) -> bool:
        """Vérifier connexion Redis"""
        try:
            await self.redis_client.ping()
            return True
        except:
            return False
    
    async def check_postgres(self) -> bool:
        """Vérifier connexion PostgreSQL"""
        try:
            async with self.pg_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except:
            return False
    
    # ========================================================================
    # AGENTS
    # ========================================================================
    
    async def register_agent(self, registration: AgentRegistration):
        """Enregistrer agent en DB"""
        async with self.pg_pool.acquire() as conn:
            await conn.execute(
                '''
                INSERT INTO agents (agent_id, agent_type, capabilities, metadata, status)
                VALUES ($1, $2, $3, $4, 'active')
                ON CONFLICT (agent_id) DO UPDATE
                SET agent_type = $2, capabilities = $3, metadata = $4, 
                    status = 'active', last_seen = CURRENT_TIMESTAMP
                ''',
                registration.agent_id,
                registration.agent_type,
                json.dumps(registration.capabilities),
                json.dumps(registration.metadata)
            )
    
    async def update_agent_status(self, agent_id: str, status: str):
        """Mettre à jour statut agent"""
        async with self.pg_pool.acquire() as conn:
            await conn.execute(
                "UPDATE agents SET status = $1, last_seen = CURRENT_TIMESTAMP WHERE agent_id = $2",
                status,
                agent_id
            )
    
    async def update_agent_last_seen(self, agent_id: str):
        """Mettre à jour last_seen (heartbeat)"""
        async with self.pg_pool.acquire() as conn:
            await conn.execute(
                "UPDATE agents SET last_seen = CURRENT_TIMESTAMP WHERE agent_id = $1",
                agent_id
            )
    
    async def get_agent_info(self, agent_id: str) -> Optional[dict]:
        """Récupérer info agent depuis DB"""
        async with self.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM agents WHERE agent_id = $1",
                agent_id
            )
            return dict(row) if row else None
    
    async def get_all_agents(self) -> List[dict]:
        """Liste tous les agents enregistrés"""
        async with self.pg_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM agents ORDER BY created_at DESC")
            return [dict(row) for row in rows]
    
    # ========================================================================
    # CONTEXTE
    # ========================================================================
    
    async def cache_context(self, context: ContextUpdate):
        """Mettre en cache contexte (Redis, TTL 1h)"""
        cache_key = f"context:{context.agent_id}:{context.context_type}"
        await self.redis_client.setex(
            cache_key,
            3600,  # 1 heure
            json.dumps(context.dict())
        )
    
    async def store_context(self, context: ContextUpdate):
        """Persister contexte (PostgreSQL)"""
        async with self.pg_pool.acquire() as conn:
            await conn.execute(
                '''
                INSERT INTO context_history (agent_id, context_type, data, priority, timestamp)
                VALUES ($1, $2, $3, $4, $5)
                ''',
                context.agent_id,
                context.context_type,
                json.dumps(context.data),
                context.priority,
                datetime.fromisoformat(context.timestamp)
            )
    
    async def get_all_current_contexts(self) -> Dict[str, Any]:
        """Récupérer tous les contextes en cache"""
        contexts = {}
        
        # Scanner toutes les clés context:*
        cursor = 0
        while True:
            cursor, keys = await self.redis_client.scan(
                cursor,
                match="context:*",
                count=100
            )
            
            for key in keys:
                value = await self.redis_client.get(key)
                if value:
                    contexts[key] = json.loads(value)
            
            if cursor == 0:
                break
        
        return contexts
    
    async def search_context_history(
        self,
        search_term: str = "",
        agent_id: Optional[str] = None,
        context_type: Optional[str] = None,
        limit: int = 10
    ) -> List[dict]:
        """Rechercher dans historique contexte"""
        query = "SELECT * FROM context_history WHERE 1=1"
        params = []
        param_count = 0
        
        if search_term:
            param_count += 1
            query += f" AND data::text ILIKE ${param_count}"
            params.append(f"%{search_term}%")
        
        if agent_id:
            param_count += 1
            query += f" AND agent_id = ${param_count}"
            params.append(agent_id)
        
        if context_type:
            param_count += 1
            query += f" AND context_type = ${param_count}"
            params.append(context_type)
        
        query += " ORDER BY timestamp DESC"
        
        param_count += 1
        query += f" LIMIT ${param_count}"
        params.append(limit)
        
        async with self.pg_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    
    async def get_conversation_history(
        self,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[dict]:
        """Récupérer historique conversations"""
        query = """
            SELECT * FROM context_history 
            WHERE context_type IN ('user_speech', 'agent_response')
        """
        params = []
        
        if user_id:
            query += " AND data->>'user' = $1"
            params.append(user_id)
        
        query += " ORDER BY timestamp DESC LIMIT $" + str(len(params) + 1)
        params.append(limit)
        
        async with self.pg_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    
    # ========================================================================
    # ACTIONS
    # ========================================================================
    
    async def log_action(self, action: ActionRequest, result: Optional[dict] = None):
        """Logger action exécutée"""
        async with self.pg_pool.acquire() as conn:
            await conn.execute(
                '''
                INSERT INTO actions_log (agent_id, action_type, parameters, result, status)
                VALUES ($1, $2, $3, $4, $5)
                ''',
                action.requesting_agent,
                action.action,
                json.dumps(action.parameters),
                json.dumps(result) if result else None,
                "success" if result else "pending"
            )
    
    # ========================================================================
    # STATS
    # ========================================================================
    
    async def get_stats(self) -> dict:
        """Récupérer statistiques système"""
        async with self.pg_pool.acquire() as conn:
            # Total agents
            total_agents = await conn.fetchval("SELECT COUNT(*) FROM agents")
            
            # Total contextes
            total_contexts = await conn.fetchval("SELECT COUNT(*) FROM context_history")
            
            # Contextes 24h
            contexts_24h = await conn.fetchval(
                "SELECT COUNT(*) FROM context_history WHERE timestamp > NOW() - INTERVAL '24 hours'"
            )
            
            # Total actions
            total_actions = await conn.fetchval("SELECT COUNT(*) FROM actions_log")
            
            # Actions 1h
            actions_1h = await conn.fetchval(
                "SELECT COUNT(*) FROM actions_log WHERE timestamp > NOW() - INTERVAL '1 hour'"
            )
        
        return {
            "total_agents": total_agents,
            "total_contexts": total_contexts,
            "contexts_24h": contexts_24h,
            "total_actions": total_actions,
            "actions_1h": actions_1h
        }