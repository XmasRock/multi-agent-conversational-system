# Raspberry Pi

# n8n
docker logs -f n8n

# MCP Server
docker logs -f mcp-server

# Tous les services
docker-compose logs -f

# Jetson

# Agent principal
tail -f ~/multi-agent-system/jetson/logs/agent.log

# Service systemd
sudo journalctl -u jetson-agent -f