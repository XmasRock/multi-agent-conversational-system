# 1. Accéder n8n: http://raspberry-pi-ip:5678
# 2. Créer compte admin
# 3. Configurer credentials:

# Credential: Jetson LLM API (OpenAI)
- Name: Jetson LLM API
- API Key: dummy-key-not-used
- Base URL: http://jetson-ip:8001/v1

# Credential: ChromaDB
- URL: http://chromadb:8000
- Auth Token: (votre CHROMA_TOKEN)

# Credential: MQTT
- Protocol: mqtt://
- Host: mqtt
- Port: 1883

# Credential: SMTP (pour emails)
- Host: smtp.gmail.com
- Port: 587
- User: votre-email@gmail.com
- Password: app-password

# 4. Importer workflows
# Settings > Workflows > Import from File
# Importer tous les fichiers .json