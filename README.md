# 🤖 Système Multi-Agents Conversationnel

Architecture distribuée open-source pour créer un agent conversationnel intelligent avec vision, audio, orchestration multi-agents et LLM interchangeables via Ollama.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Ollama](https://img.shields.io/badge/Ollama-Ready-blue)](https://ollama.com/)

## 🎯 Fonctionnalités

### 🤖 Intelligence Artificielle
- **🧠 LLM Interchangeables** : Ollama (Llama 3.1, Mistral, Phi-3, Gemma 2, Qwen)
- **🔄 Hot-swap Modèles** : Changez de LLM sans redémarrer
- **💾 Mémoire Longue Durée** : ChromaDB pour conversations persistantes
- **🎯 Contexte Partagé** : MCP (Model Context Protocol) pour coordination agents

### 👁️ Perception
- **📹 Vision par Ordinateur** : YOLOv11 pour détection temps réel
- **👤 Reconnaissance Faciale** : InsightFace avec base de visages personnalisable
- **🎤 Reconnaissance Vocale** : Whisper STT (français, multilingue)
- **🔊 Synthèse Vocale** : Piper TTS (voix naturelle française)

### 🔄 Orchestration
- **📊 n8n AI Agent** : Workflows visuels intelligents
- **🌐 Architecture Distribuée** : Raspberry Pi (hub) + Jetson (edge)
- **📡 Communication Temps Réel** : WebSocket, MQTT, REST API
- **🔌 Reconnexion Automatique** : Résilience réseau complète

### ⚡ Actions
- ✉️ Envoi d'emails
- 🔍 Recherches web
- 📅 Gestion calendrier
- 🏠 Contrôle domotique (extensible)

---

## 🏗️ Architecture
```
┌──────────────────────────────────────────────────────┐
│           RASPBERRY PI 5 (Hub Central)                │
│                                                        │
│  ┌──────────────────────────────────────────────┐   │
│  │  n8n AI Agent                                 │   │
│  │  - Orchestration workflows                    │   │
│  │  - Coordination agents                        │   │
│  │  - LLM via Ollama (Jetson)                    │   │
│  └──────────────────────────────────────────────┘   │
│                                                        │
│  ┌──────────────────────────────────────────────┐   │
│  │  MCP Server                                   │   │
│  │  - Contexte partagé                           │   │
│  │  - Mémoire conversationnelle                  │   │
│  │  - État global agents                         │   │
│  └──────────────────────────────────────────────┘   │
│                                                        │
│  [PostgreSQL] [Redis] [ChromaDB] [MQTT] [Grafana]    │
└──────────────────────────────────────────────────────┘
                         ↕ WebSocket/MQTT/REST
┌──────────────────────────────────────────────────────┐
│         JETSON ORIN NANO SUPER (Edge AI)              │
│                                                        │
│  ┌──────────────────────────────────────────────┐   │
│  │  Ollama Server                                │   │
│  │  - Llama 3.1 8B (défaut)                      │   │
│  │  - Mistral 7B, Phi-3, Gemma 2, Qwen          │   │
│  │  - API OpenAI-compatible                      │   │
│  │  - Hot-swap modèles                           │   │
│  └──────────────────────────────────────────────┘   │
│                         ↕                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │   Vision    │  │    Audio    │  │   Actions   │  │
│  │   Agent     │  │    Agent    │  │   Agent     │  │
│  │             │  │             │  │             │  │
│  │  YOLOv11    │  │  Whisper    │  │  Executor   │  │
│  │  InsightFace│  │  Piper TTS  │  │  Local      │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
│                                                        │
│  [MCP Client] [MQTT Client] [API Server]              │
└──────────────────────────────────────────────────────┘
```

---

## 📋 Prérequis

### 💻 Matériel Recommandé

| Composant | Spécification | Prix |
|-----------|---------------|------|
| **Jetson Orin Nano Super** | 8GB RAM, 1024 CUDA cores | Possédé ✅ |
| **Raspberry Pi 5** | 8GB RAM recommandé | ~100€ |
| **Caméra** | Raspberry Pi Camera (CSI) ou USB | Possédé ✅ |
| **Microphone** | USB (ReSpeaker recommandé) | ~25€ |
| **Enceinte** | Bluetooth/USB | Possédé ✅ |
| **SSD Jetson** | NVMe 512GB | ~45€ |
| **SSD Raspberry** | USB 3.0 256GB | ~35€ |

**Total additionnel : ~240€**

### 🖥️ Logiciel

**Jetson :**
- JetPack 6.0+
- Ubuntu 22.04
- Python 3.11+
- Ollama

**Raspberry Pi :**
- Raspberry Pi OS 64-bit ou Ubuntu 22.04
- Docker & Docker Compose
- Python 3.11+

---

## 🚀 Installation

### 📦 1. Raspberry Pi - Hub Central
```bash
# Cloner le projet
git clone https://github.com/VOTRE_USERNAME/multi-agent-system.git
cd multi-agent-system/raspberry-pi

# Configurer environnement
cp .env.example .env
nano .env
# Éditer :
# - RASPBERRY_PI_IP=192.168.1.XXX (votre IP)
# - JETSON_IP=192.168.1.XXX (IP du Jetson)
# - Mots de passe sécurisés

# Installer Docker (si nécessaire)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Déconnexion/reconnexion requise

# Lancer les services
docker-compose up -d

# Vérifier statut
docker-compose ps
docker-compose logs -f

# Accès aux interfaces :
# - n8n : http://raspberry-pi-ip:5678
# - MCP Server : http://raspberry-pi-ip:8080
# - Grafana : http://raspberry-pi-ip:3000
# - ChromaDB : http://raspberry-pi-ip:8000
```

### 🤖 2. Jetson Orin Nano - Agent Edge
```bash
# Mettre à jour le système
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv git

# Cloner le projet
cd ~
git clone https://github.com/VOTRE_USERNAME/multi-agent-system.git
cd multi-agent-system/jetson

# Installer Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Télécharger modèles LLM (choisir selon besoins)
# Llama 3.1 8B (Recommandé - équilibré)
ollama pull llama3.1:8b

# Ou alternatives :
# ollama pull mistral:7b        # Rapide et efficace
# ollama pull phi3:medium       # Ultra-léger (2.3GB)
# ollama pull gemma2:9b         # Google, excellent français
# ollama pull qwen2.5:7b        # Multilingue excellent

# Lister modèles installés
ollama list

# Créer environnement virtuel Python
python3 -m venv venv
source venv/bin/activate

# Installer dépendances Python
pip install --upgrade pip
pip install -r requirements.txt

# Installer llama.cpp (pour Whisper.cpp)
cd ~
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
mkdir build && cd build
cmake .. -DLLAMA_CUDA=ON
make -j$(nproc)

# Installer Whisper.cpp
cd ~
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
make -j$(nproc)
# Télécharger modèle Whisper
bash ./models/download-ggml-model.sh medium

# Installer Piper TTS
pip install piper-tts
# Télécharger voix française
mkdir -p ~/multi-agent-system/jetson/models/piper
cd ~/multi-agent-system/jetson/models/piper
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx.json

# Configuration
cd ~/multi-agent-system/jetson
cp config.example.yml config.yml
nano config.yml
# Éditer :
# - raspberry_pi_ip: "192.168.1.XXX"
# - jetson_ip: "192.168.1.XXX"
# - Choisir modèle Ollama

# Configurer Bluetooth (pour enceinte)
sudo apt install -y bluez pulseaudio-module-bluetooth
# Pairage enceinte :
bluetoothctl
# > power on
# > agent on
# > scan on
# > pair AA:BB:CC:DD:EE:FF
# > trust AA:BB:CC:DD:EE:FF
# > connect AA:BB:CC:DD:EE:FF
# > exit

# Télécharger YOLOv11
cd ~/multi-agent-system/jetson
python3 << EOF
from ultralytics import YOLO
model = YOLO('yolo11n.pt')
model.export(format='engine', device=0, half=True)
import shutil
shutil.move('yolo11n.engine', 'models/yolo11n.engine')
print("✅ YOLOv11 exporté")
EOF

# Test rapide
python3 -c "from modules.vision_agent import VisionAgent; print('✅ Vision OK')"
python3 -c "from modules.audio_agent import AudioAgent; print('✅ Audio OK')"
python3 -c "from modules.llm_agent import LLMAgent; print('✅ LLM OK')"

# Lancer l'agent
python3 main.py
```

### 🔧 3. Configuration n8n
```bash
# Accéder à n8n : http://raspberry-pi-ip:5678

# 1. Créer compte admin

# 2. Configurer Credentials :

# Credential: Jetson LLM (OpenAI compatible)
- Name: Jetson Ollama
- API Key: dummy-key
- Base URL: http://jetson-ip:8001/v1

# Credential: ChromaDB
- URL: http://chromadb:8000
- Auth Token: (votre CHROMA_TOKEN du .env)

# Credential: MQTT
- Protocol: mqtt://
- Host: mqtt
- Port: 1883

# Credential: SMTP (pour emails)
- Host: smtp.gmail.com
- Port: 587
- User: votre-email@gmail.com
- Password: app-password-gmail

# 3. Importer workflows
# Settings > Workflows > Import from File
# Importer les fichiers depuis raspberry-pi/n8n/workflows/
```

### 🔄 4. Configurer comme Service (Jetson)
```bash
# Créer service systemd
sudo nano /etc/systemd/system/jetson-agent.service
```
```ini
[Unit]
Description=Jetson Conversational Agent
After=network-online.target ollama.service
Wants=network-online.target

[Service]
Type=simple
User=jetson
WorkingDirectory=/home/jetson/multi-agent-system/jetson
Environment="PATH=/home/jetson/multi-agent-system/jetson/venv/bin"
ExecStart=/home/jetson/multi-agent-system/jetson/venv/bin/python main.py

Restart=always
RestartSec=10
StartLimitInterval=200
StartLimitBurst=5

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```
```bash
# Activer et démarrer
sudo systemctl daemon-reload
sudo systemctl enable jetson-agent
sudo systemctl start jetson-agent

# Vérifier statut
sudo systemctl status jetson-agent

# Voir logs
sudo journalctl -u jetson-agent -f
```

---

## 🎮 Utilisation

### 💬 Scénario 1 : Conversation Simple
```
Utilisateur : "Bonjour, qui suis-je ?"

Système :
1. 👁️ Vision détecte et reconnaît votre visage
2. 🎤 Audio transcrit votre voix (Whisper)
3. 📡 Contexte envoyé au MCP Server
4. 🧠 n8n AI Agent génère réponse (Ollama/Llama 3.1)
5. 🔊 Réponse synthétisée (Piper TTS)
6. 💾 Conversation sauvegardée (ChromaDB)

Agent : "Bonjour Pierre ! Comment puis-je vous aider ?"
```

### 📧 Scénario 2 : Envoi Email
```
Utilisateur : "Envoie un email à Jean"

Agent : "Quel est le sujet de l'email ?"

Utilisateur : "Réunion demain"

Agent : "Que voulez-vous dire dans le message ?"

Utilisateur : "Confirmer réunion 10h"

Système :
1. 🤖 n8n AI Agent détecte intention email
2. 🔍 Recherche contact "Jean" dans MCP
3. ✉️ Workflow Email Agent envoie le message
4. 📊 Action loguée dans MCP

Agent : "Email envoyé à Jean Dupont avec succès !"
```

### 🔄 Changer de Modèle LLM
```bash
# Méthode 1 : Ollama CLI
ollama pull mistral:7b
# Puis redémarrer agent ou via API

# Méthode 2 : API REST
curl -X POST http://jetson-ip:8000/switch-model \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral:7b"}'

# Méthode 3 : Commande vocale (si implémentée)
Utilisateur : "Change le modèle pour Mistral"
```

### 📊 Modèles LLM Disponibles

| Modèle | Taille | RAM | Vitesse | Usage |
|--------|--------|-----|---------|-------|
| **llama3.1:8b** | 4.7GB | ~6GB | Moyen | Recommandé - Équilibré |
| **mistral:7b** | 4.1GB | ~5GB | Rapide | Conversations rapides |
| **phi3:medium** | 2.3GB | ~3GB | Ultra-rapide | Réponses courtes |
| **gemma2:9b** | 5.4GB | ~7GB | Moyen | Excellent français |
| **qwen2.5:7b** | 4.4GB | ~6GB | Rapide | Multilingue |

---

## 🔧 Configuration

### 📝 Variables d'Environnement (Raspberry Pi)
```bash
# raspberry-pi/.env

# IPs
RASPBERRY_PI_IP=192.168.1.100
JETSON_IP=192.168.1.101

# n8n
N8N_USER=admin
N8N_PASSWORD=VotreMotDePasseSecurise123!

# PostgreSQL
POSTGRES_PASSWORD=VotreMotDePassePostgres456!

# ChromaDB
CHROMA_TOKEN=VotreTokenChroma789!

# Grafana
GRAFANA_PASSWORD=admin

# Timezone
TZ=Europe/Paris
```

### ⚙️ Configuration Jetson
```yaml
# jetson/config.yml

network:
  raspberry_pi_ip: "192.168.1.100"
  jetson_ip: "192.168.1.101"

modules:
  llm:
    enabled: true
    engine: "ollama"
    ollama:
      host: "localhost"
      port: 11434
      model: "llama3.1:8b"  # Modèle par défaut
      temperature: 0.7
      num_ctx: 8192
    api_server:
      enabled: true
      port: 8001

  vision:
    enabled: true
    camera:
      type: "csi"  # ou "usb"
      device: 0

  audio:
    enabled: true
    speaker:
      device: "pulse"  # Pour Bluetooth
```

---

## 🧪 Tests

### ✅ Test Complet du Système
```bash
# 1. Vérifier services Raspberry Pi
curl http://raspberry-pi-ip:8080/health  # MCP Server
curl http://raspberry-pi-ip:5678        # n8n

# 2. Vérifier Jetson
curl http://jetson-ip:8000/status       # Agent
curl http://jetson-ip:8001/health       # LLM Server
curl http://jetson-ip:11434/api/tags    # Ollama

# 3. Test LLM
curl -X POST http://jetson-ip:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "messages": [{"role": "user", "content": "Bonjour"}]
  }'

# 4. Test workflow complet
curl -X POST http://raspberry-pi-ip:5678/webhook/agent-input \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Bonjour, comment vas-tu ?",
    "user_identity": "Test User"
  }'
```

---

## 📊 Monitoring

### 🎛️ Dashboards Disponibles

- **Grafana** : http://raspberry-pi-ip:3000 (admin/admin)
- **n8n** : http://raspberry-pi-ip:5678
- **MCP Stats** : http://raspberry-pi-ip:8080/stats
- **Prometheus** : http://raspberry-pi-ip:9090

### 📝 Logs
```bash
# Raspberry Pi
docker logs -f mcp-server
docker logs -f n8n
docker-compose logs -f

# Jetson
tail -f ~/multi-agent-system/jetson/logs/agent.log
sudo journalctl -u jetson-agent -f
```

---

## 💰 Coûts

### 💵 Budget Total
```
MATÉRIEL POSSÉDÉ :
✅ Jetson Orin Nano Super : 0€
✅ Caméra Raspberry Pi : 0€
✅ Enceinte Bluetooth : 0€

MATÉRIEL À ACHETER :
- Raspberry Pi 5 (8GB) : ~100€
- SSD NVMe 512GB (Jetson) : ~45€
- SSD USB 256GB (RPi) : ~35€
- Microphone USB : ~25€
- Boîtier + accessoires : ~35€

TOTAL : ~240€

LOGICIELS : 0€ (100% open source)

ÉLECTRICITÉ :
- Jetson (15W moyen) : ~35€/an
- RPi 5 (10W moyen) : ~20€/an
- Total : ~55€/an

COMPARAISON CLOUD (5 ans) :
- OpenAI + APIs : 9000-28000€
- Notre solution : 240€ + 275€ = 515€
- ÉCONOMIE : 8485-27485€ ! 🎉
```

---

## 🔧 Dépannage

### ❌ Problèmes Courants

#### MCP Server ne démarre pas
```bash
docker logs mcp-server
docker-compose restart postgres redis mcp-server
```

#### Jetson ne se connecte pas au MCP
```bash
# Vérifier réseau
ping raspberry-pi-ip

# Vérifier config
cat ~/multi-agent-system/jetson/config.yml | grep raspberry_pi_ip

# Tester WebSocket
wscat -c ws://raspberry-pi-ip:8081/ws/agent/test
```

#### Ollama ne répond pas
```bash
# Redémarrer Ollama
sudo systemctl restart ollama

# Vérifier modèles
ollama list

# Télécharger à nouveau
ollama pull llama3.1:8b

# Tester directement
ollama run llama3.1:8b "Test"
```

#### Audio ne fonctionne pas
```bash
# Lister devices
arecord -l  # Microphones
aplay -l    # Speakers

# Tester micro
arecord -d 3 test.wav && aplay test.wav

# Tester TTS
echo "Test" | piper --model fr_FR-siwis-medium --output_file test.wav
paplay test.wav
```

---

## 🤝 Contribution

Les contributions sont bienvenues ! Pour contribuer :

1. Fork le projet
2. Créer une branche (`git checkout -b feature/amelioration`)
3. Commit (`git commit -m 'Ajout fonctionnalité'`)
4. Push (`git push origin feature/amelioration`)
5. Ouvrir une Pull Request

---

## 📝 License

MIT License - voir [LICENSE](LICENSE)

Vous êtes libre d'utiliser, modifier et distribuer ce projet.

---

## 🙏 Remerciements

Ce projet utilise ces excellents outils open source :

- [Ollama](https://ollama.com/) - Gestion LLM simplifiée
- [Ultralytics YOLOv11](https://github.com/ultralytics/ultralytics) - Détection objets
- [Whisper.cpp](https://github.com/ggerganov/whisper.cpp) - Speech-to-Text
- [Piper TTS](https://github.com/rhasspy/piper) - Text-to-Speech
- [n8n](https://github.com/n8n-io/n8n) - Orchestration workflows
- [InsightFace](https://github.com/deepinsight/insightface) - Reconnaissance faciale
- [ChromaDB](https://github.com/chroma-core/chroma) - Base vectorielle
- [FastAPI](https://github.com/tiangolo/fastapi) - Framework API

---

## 📞 Support

- 🐛 **Bugs** : [Ouvrir une issue](https://github.com/VOTRE_USERNAME/multi-agent-system/issues)
- 💬 **Questions** : [Discussions GitHub](https://github.com/VOTRE_USERNAME/multi-agent-system/discussions)
- 📖 **Documentation** : [Wiki](https://github.com/VOTRE_USERNAME/multi-agent-system/wiki)

---

## 🗺️ Roadmap

- [ ] Support multi-utilisateurs
- [ ] Interface web de configuration
- [ ] Support modèles vision (LLaVA, Qwen-VL)
- [ ] Integration Home Assistant
- [ ] Support langues supplémentaires
- [ ] Mobile app (contrôle à distance)
- [ ] RAG avancé avec documents personnels
- [ ] Fine-tuning modèles personnalisés

---

## ⭐ Statistiques

![GitHub stars](https://img.shields.io/github/stars/VOTRE_USERNAME/multi-agent-system?style=social)
![GitHub forks](https://img.shields.io/github/forks/VOTRE_USERNAME/multi-agent-system?style=social)
![GitHub issues](https://img.shields.io/github/issues/VOTRE_USERNAME/multi-agent-system)

---

**Construit avec ❤️ pour la communauté open source**

⭐ **Si ce projet vous aide, donnez-lui une étoile sur GitHub !**