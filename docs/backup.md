# Raspberry Pi - Backup bases de données
docker exec postgres pg_dump -U postgres n8n > backup_n8n.sql
docker exec postgres pg_dump -U postgres mcp > backup_mcp.sql

# Backup ChromaDB
docker cp chromadb:/chroma/chroma ./backup_chromadb

# Jetson - Backup visages enregistrés
cp ~/multi-agent-system/jetson/models/face_embeddings.pkl ~/backup/