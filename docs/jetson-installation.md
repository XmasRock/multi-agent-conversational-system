# 1. Flash JetPack 6.0 (si pas déjà fait)
# Utiliser SDK Manager depuis un PC Ubuntu

# 2. Préparation système
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv git cmake build-essential

# 3. Installer CUDA toolkit (si pas inclus dans JetPack)
# Normalement déjà présent avec JetPack 6.0

# 4. Cloner projet
cd ~
git clone https://github.com/votre-repo/multi-agent-system.git
cd multi-agent-system/jetson

# 5. Créer environnement virtuel
python3 -m venv venv
source venv/bin/activate

# 6. Installer dépendances
pip install --upgrade pip
pip install -r requirements.txt

# 7. Installer llama.cpp avec CUDA
cd ~
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
mkdir build && cd build
cmake .. -DLLAMA_CUDA=ON
make -j$(nproc)
cd ~/multi-agent-system/jetson

# 8. Installer Whisper.cpp
cd ~
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
make -j$(nproc)
# Télécharger modèle
bash ./models/download-ggml-model.sh medium
cd ~/multi-agent-system/jetson

# 9. Installer Piper TTS
pip install piper-tts
# Télécharger voix française
mkdir -p models/piper
cd models/piper
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx.json
cd ~/multi-agent-system/jetson

# 10. Télécharger modèles
mkdir -p models

# YOLOv11
python3 << EOF
from ultralytics import YOLO
model = YOLO('yolo11n.pt')
model.export(format='engine', device=0, half=True)
# Déplacer vers models/
EOF

# Llama 3.1 8B quantifié
# Télécharger depuis HuggingFace
wget -O models/llama-3.1-8b-q4.gguf \
  https://huggingface.co/TheBloke/Llama-3.1-8B-GGUF/resolve/main/llama-3.1-8b.Q4_K_M.gguf

# 11. Configuration
cp config.example.yml config.yml
nano config.yml  # Éditer avec IP Raspberry Pi

# 12. Test modules
python3 -c "from modules.vision_agent import VisionAgent; print('Vision OK')"
python3 -c "from modules.audio_agent import AudioAgent; print('Audio OK')"
python3 -c "from modules.llm_agent import LLMAgent; print('LLM OK')"

# 13. Démarrage
python3 main.py

# Créer service systemd
sudo nano /etc/systemd/system/jetson-agent.service

# Activer service
sudo systemctl daemon-reload
sudo systemctl enable jetson-agent
sudo systemctl start jetson-agent

# Vérifier statut
sudo systemctl status jetson-agent

# Voir logs
sudo journalctl -u jetson-agent -f

# Tests 
## 1. Test MCP Server
curl http://raspberry-pi-ip:8080/health

## 2. Test n8n
curl http://raspberry-pi-ip:5678

## 3. Test Jetson API
curl http://jetson-ip:8000/status

## 4. Test LLM Server
curl http://jetson-ip:8001/v1/models

## 5. Test workflow complet
curl -X POST http://raspberry-pi-ip:5678/webhook/agent-input \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Bonjour, qui suis-je ?",
    "user_identity": "Test User",
    "source": "test"
  }'
```

## Scénarios de Test

### Scénario 1: Reconnaissance et Conversation
```
1. Se placer devant la caméra du Jetson
2. Dire "Bonjour"
3. Le système devrait:
   - Détecter votre visage (vision)
   - Transcrire votre parole (STT)
   - Publier au MCP
   - n8n AI Agent génère réponse via Jetson LLM
   - Réponse synthétisée (TTS)
   - Conversation sauvegardée dans ChromaDB
```

### Scénario 2: Action Email
```
1. Dire "Envoie un email à test@example.com"
2. n8n AI Agent devrait:
   - Détecter intention email
   - Appeler Email Tool
   - Demander sujet et contenu (via Jetson TTS)
   - Envoyer email
   - Confirmer via parole
```

### Scénario 3: Recherche Web
```
1. Dire "Recherche les dernières nouvelles sur l'IA"
2. Le système devrait:
   - Appeler Web Search Tool
   - Récupérer résultats
   - Synthétiser réponse
   - Parler les résultats