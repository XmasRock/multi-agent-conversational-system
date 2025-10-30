# raspberry-pi/init-db.sh
#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    -- Base de données n8n
    CREATE DATABASE n8n;
    CREATE USER n8n WITH PASSWORD '${POSTGRES_PASSWORD}';
    GRANT ALL PRIVILEGES ON DATABASE n8n TO n8n;
    
    -- Base de données MCP
    CREATE DATABASE mcp;
    CREATE USER mcpuser WITH PASSWORD '${POSTGRES_PASSWORD}';
    GRANT ALL PRIVILEGES ON DATABASE mcp TO mcpuser;
    
    -- Se connecter à la base MCP pour créer les tables
    \c mcp
    
    -- Table historique contexte
    CREATE TABLE IF NOT EXISTS context_history (
        id SERIAL PRIMARY KEY,
        agent_id VARCHAR(255) NOT NULL,
        context_type VARCHAR(100) NOT NULL,
        data JSONB NOT NULL,
        priority INTEGER DEFAULT 1,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_agent_timestamp (agent_id, timestamp DESC),
        INDEX idx_context_type (context_type),
        INDEX idx_priority (priority DESC)
    );
    
    -- Table agents enregistrés
    CREATE TABLE IF NOT EXISTS agents (
        agent_id VARCHAR(255) PRIMARY KEY,
        agent_type VARCHAR(100) NOT NULL,
        capabilities JSONB,
        metadata JSONB,
        status VARCHAR(50) DEFAULT 'active',
        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Table actions exécutées
    CREATE TABLE IF NOT EXISTS actions_log (
        id SERIAL PRIMARY KEY,
        agent_id VARCHAR(255) NOT NULL,
        action_type VARCHAR(100) NOT NULL,
        parameters JSONB,
        result JSONB,
        status VARCHAR(50),
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Permissions
    GRANT ALL ON ALL TABLES IN SCHEMA public TO mcpuser;
    GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO mcpuser;
EOSQL