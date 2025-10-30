# multi-agent-conversational-system
Distributed multi-agent system with vision, audio, and LLM orchestration 

# 🤖 Système Multi-Agents Conversationnel

Architecture distribuée open-source pour créer un agent conversationnel intelligent avec vision, audio et orchestration multi-agents.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## 🎯 Fonctionnalités

- **🎤 Reconnaissance vocale** : Whisper STT (français)
- **🔊 Synthèse vocale** : Piper TTS (voix naturelle)
- **👁️ Vision par ordinateur** : YOLOv11 + reconnaissance faciale (InsightFace)
- **🧠 Intelligence** : LLM local (Llama 3.1 8B) optimisé pour edge
- **🔄 Orchestration** : n8n AI Agent avec workflows visuels
- **💾 Mémoire longue** : ChromaDB pour conversations persistantes
- **🌐 Architecture distribuée** : MCP (Model Context Protocol) pour coordination agents
- **📡 Communication temps réel** : WebSocket, MQTT, REST API

## 🏗️ Architecture
```
┌─────────────────────────────────┐
│   Raspberry Pi 5 (Hub)          │
│   - n8n (orchestrateur)         │
│   - MCP Server (contexte)       │
│   - PostgreSQL, Redis, ChromaDB │
└─────────────────────────────────┘
              ↕
┌─────────────────────────────────┐
│   Jetson Orin Nano              │
│   - Vision (YOLOv11)            │
│   - Audio (Whisper + Piper)     │
│   - LLM (Llama 3.1 8B)          │
└─────────────────────────────────┘
```

## 📋 Prérequis

### Matériel
- **Jetson Orin Nano Super** (ou Nano 8GB)
- **Raspberry Pi 5** (8GB recommandé) ou Raspberry Pi 4 8GB
- **Caméra** : Raspberry Pi Camera (CSI) ou USB
- **Audio** : Microphone USB + Enceinte (USB/Bluetooth)
- **Stockage** : SSD NVMe 512GB (Jetson) + SSD USB 256GB (RPi)

### Logiciel
- JetPack 6.0+ (Jetson)
- Ubuntu 22.04 ou Raspberry Pi OS 64-bit (RPi)
- Docker & Docker Compose
- Python 3.11+

## 🚀 Installation Rapide

### Raspberry Pi
```bash
cd raspberry-pi
cp .env.example .env
nano .env  # Configurer IPs et mots de passe
docker-compose up -d
```

### Jetson Orin Nano
```bash
cd jetson
cp config.example.yml config.yml
nano config.yml  # Configurer IP Raspberry Pi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

## 📖 Documentation

- [Architecture Détaillée](docs/architecture.md)
- [Guide d'Installation](docs/installation.md)
- [Configuration Workflows n8n](docs/workflows.md)
- [Dépannage](docs/troubleshooting.md)

## 💰 Coûts

- **Matériel** : ~400-700€ (one-time)
- **Logiciels** : 0€ (100% open source)
- **Électricité** : ~55€/an
- **Économie vs Cloud** : 8000-28000€ sur 5 ans ! 🎉

## 🔧 Configuration

Voir les fichiers d'exemple :
- [`raspberry-pi/.env.example`](raspberry-pi/.env.example)
- [`jetson/config.example.yml`](jetson/config.example.yml)

## 🤝 Contribution

Les contributions sont bienvenues ! Consultez notre guide de contribution.

## 📝 License

MIT License - voir [LICENSE](LICENSE)

## 🙏 Remerciements

Projet basé sur :
- [Ultralytics YOLOv11](https://github.com/ultralytics/ultralytics)
- [Whisper.cpp](https://github.com/ggerganov/whisper.cpp)
- [llama.cpp](https://github.com/ggerganov/llama.cpp)
- [n8n](https://github.com/n8n-io/n8n)
- [InsightFace](https://github.com/deepinsight/insightface)
- [Piper TTS](https://github.com/rhasspy/piper)

## 📧 Contact

Pour questions et support, ouvrez une issue sur GitHub.

---

⭐ Si ce projet vous aide, n'hésitez pas à lui donner une étoile !
