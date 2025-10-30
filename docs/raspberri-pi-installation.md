# 1. Préparation système
sudo apt update && sudo apt upgrade -y
sudo apt install -y git docker.io docker-compose python3-pip

# 2. Cloner projet
cd ~
git clone https://github.com/votre-repo/multi-agent-system.git
cd multi-agent-system/raspberry-pi

# 3. Configuration
cp .env.example .env
nano .env  # Éditer avec vos IPs et mots de passe

# 4. Permissions
sudo usermod -aG docker $USER
# Déconnexion/reconnexion nécessaire

# 5. Démarrage services
docker-compose up -d

# 6. Vérifier services
docker-compose ps
docker-compose logs -f

# 7. Accès interfaces
# n8n: http://raspberry-pi-ip:5678
# MCP Server: http://raspberry-pi-ip:8080
# ChromaDB: http://raspberry-pi-ip:8000
# Grafana: http://raspberry-pi-ip:3000