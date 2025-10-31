# 🤖 Multi-Agent Conversational System

Open-source distributed architecture for building an intelligent conversational agent with vision, audio, multi-agent orchestration, and swappable LLMs via Ollama.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Ollama](https://img.shields.io/badge/Ollama-Ready-blue)](https://ollama.com/)

## 🎯 Features

### 🤖 Artificial Intelligence
- **🧠 Swappable LLMs** : Ollama (Llama 3.1, Mistral, Phi-3, Gemma 2, Qwen)
- **🔄 Hot-swap Models** : Change LLM without restarting
- **💾 Long-term Memory** : ChromaDB for persistent conversations
- **🎯 Shared Context** : MCP (Model Context Protocol) for agent coordination

### 👁️ Perception
- **📹 Computer Vision** : YOLOv11 for real-time detection
- **👤 Face Recognition** : InsightFace with customizable face database
- **🎤 Speech Recognition** : Whisper STT (multilingual support)
- **🔊 Text-to-Speech** : Piper TTS (natural voice synthesis)

### 🔄 Orchestration
- **📊 n8n AI Agent** : Visual intelligent workflows
- **🌐 Distributed Architecture** : Raspberry Pi (hub) + Jetson (edge)
- **📡 Real-time Communication** : WebSocket, MQTT, REST API
- **🔌 Auto-reconnection** : Full network resilience

### ⚡ Actions
- ✉️ Email sending
- 🔍 Web searches
- 📅 Calendar management
- 🏠 Home automation (extensible)

---

## 🏗️ Architecture
```
┌──────────────────────────────────────────────────────┐
│           RASPBERRY PI 5 (Central Hub)                │
│                                                        │
│  ┌──────────────────────────────────────────────┐   │
│  │  n8n AI Agent                                 │   │
│  │  - Workflow orchestration                     │   │
│  │  - Agent coordination                         │   │
│  │  - LLM via Ollama (Jetson)                    │   │
│  └──────────────────────────────────────────────┘   │
│                                                        │
│  ┌──────────────────────────────────────────────┐   │
│  │  MCP Server                                   │   │
│  │  - Shared context                             │   │
│  │  - Conversational memory                      │   │
│  │  - Global agent state                         │   │
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
│  │  - Llama 3.1 8B (default)                     │   │
│  │  - Mistral 7B, Phi-3, Gemma 2, Qwen          │   │
│  │  - OpenAI-compatible API                      │   │
│  │  - Hot-swap models                            │   │
│  └──────────────────────────────────────────────┘   │
│                         ↕                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │   Vision    │  │    Audio    │  │   Actions   │  │
│  │   Agent     │  │    Agent    │  │   Agent     │  │
│  │             │  │             │  │             │  │
│  │  YOLOv11    │  │  Whisper    │  │  Local      │  │
│  │  InsightFace│  │  Piper TTS  │  │  Executor   │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
│                                                        │
│  [MCP Client] [MQTT Client] [API Server]              │
└──────────────────────────────────────────────────────┘
```

---

## 📋 Prerequisites

### 💻 Recommended Hardware

| Component | Specification | Price |
|-----------|---------------|-------|
| **Jetson Orin Nano Super** | 8GB RAM, 1024 CUDA cores | Owned ✅ |
| **Raspberry Pi 5** | 8GB RAM recommended | ~$110 |
| **Camera** | Raspberry Pi Camera (CSI) or USB | Owned ✅ |
| **Microphone** | USB (ReSpeaker recommended) | ~$30 |
| **Speaker** | Bluetooth/USB | Owned ✅ |
| **Jetson SSD** | NVMe 512GB | ~$50 |
| **Raspberry SSD** | USB 3.0 256GB | ~$40 |

**Additional Total: ~$260**

### 🖥️ Software

**Jetson:**
- JetPack 6.0+
- Ubuntu 22.04
- Python 3.11+
- Ollama

**Raspberry Pi:**
- Raspberry Pi OS 64-bit or Ubuntu 22.04
- Docker & Docker Compose
- Python 3.11+

---

## 🚀 Installation

### 📦 1. Raspberry Pi - Central Hub
```bash
# Clone the project
git clone https://github.com/YOUR_USERNAME/multi-agent-system.git
cd multi-agent-system/raspberry-pi

# Configure environment
cp .env.example .env
nano .env
# Edit:
# - RASPBERRY_PI_IP=192.168.1.XXX (your IP)
# - JETSON_IP=192.168.1.XXX (Jetson IP)
# - Secure passwords

# Install Docker (if needed)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Logout/login required

# Start services
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f

# Access interfaces:
# - n8n: http://raspberry-pi-ip:5678
# - MCP Server: http://raspberry-pi-ip:8080
# - Grafana: http://raspberry-pi-ip:3000
# - ChromaDB: http://raspberry-pi-ip:8000
```

### 🤖 2. Jetson Orin Nano - Edge Agent
```bash
# Update system
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv git

# Clone project
cd ~
git clone https://github.com/YOUR_USERNAME/multi-agent-system.git
cd multi-agent-system/jetson

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Download LLM models (choose based on needs)
# Llama 3.1 8B (Recommended - balanced)
ollama pull llama3.1:8b

# Or alternatives:
# ollama pull mistral:7b        # Fast and efficient
# ollama pull phi3:medium       # Ultra-light (2.3GB)
# ollama pull gemma2:9b         # Google, excellent
# ollama pull qwen2.5:7b        # Multilingual excellent

# List installed models
ollama list

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install llama.cpp (for Whisper.cpp)
cd ~
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
mkdir build && cd build
cmake .. -DLLAMA_CUDA=ON
make -j$(nproc)

# Install Whisper.cpp
cd ~
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
make -j$(nproc)
# Download Whisper model
bash ./models/download-ggml-model.sh medium

# Install Piper TTS
pip install piper-tts
# Download voice model
mkdir -p ~/multi-agent-system/jetson/models/piper
cd ~/multi-agent-system/jetson/models/piper
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json

# Configuration
cd ~/multi-agent-system/jetson
cp config.example.yml config.yml
nano config.yml
# Edit:
# - raspberry_pi_ip: "192.168.1.XXX"
# - jetson_ip: "192.168.1.XXX"
# - Choose Ollama model

# Configure Bluetooth (for speaker)
sudo apt install -y bluez pulseaudio-module-bluetooth
# Pair speaker:
bluetoothctl
# > power on
# > agent on
# > scan on
# > pair AA:BB:CC:DD:EE:FF
# > trust AA:BB:CC:DD:EE:FF
# > connect AA:BB:CC:DD:EE:FF
# > exit

# Download YOLOv11
cd ~/multi-agent-system/jetson
python3 << EOF
from ultralytics import YOLO
model = YOLO('yolo11n.pt')
model.export(format='engine', device=0, half=True)
import shutil
shutil.move('yolo11n.engine', 'models/yolo11n.engine')
print("✅ YOLOv11 exported")
EOF

# Quick test
python3 -c "from modules.vision_agent import VisionAgent; print('✅ Vision OK')"
python3 -c "from modules.audio_agent import AudioAgent; print('✅ Audio OK')"
python3 -c "from modules.llm_agent import LLMAgent; print('✅ LLM OK')"

# Launch agent
python3 main.py
```

### 🔧 3. Configure n8n
```bash
# Access n8n: http://raspberry-pi-ip:5678

# 1. Create admin account

# 2. Configure Credentials:

# Credential: Jetson LLM (OpenAI compatible)
- Name: Jetson Ollama
- API Key: dummy-key
- Base URL: http://jetson-ip:8001/v1

# Credential: ChromaDB
- URL: http://chromadb:8000
- Auth Token: (your CHROMA_TOKEN from .env)

# Credential: MQTT
- Protocol: mqtt://
- Host: mqtt
- Port: 1883

# Credential: SMTP (for emails)
- Host: smtp.gmail.com
- Port: 587
- User: your-email@gmail.com
- Password: gmail-app-password

# 3. Import workflows
# Settings > Workflows > Import from File
# Import files from raspberry-pi/n8n/workflows/
```

### 🔄 4. Configure as Service (Jetson)
```bash
# Create systemd service
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
# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable jetson-agent
sudo systemctl start jetson-agent

# Check status
sudo systemctl status jetson-agent

# View logs
sudo journalctl -u jetson-agent -f
```

---

## 🎮 Usage

### 💬 Scenario 1: Simple Conversation
```
User: "Hello, who am I?"

System:
1. 👁️ Vision detects and recognizes your face
2. 🎤 Audio transcribes your voice (Whisper)
3. 📡 Context sent to MCP Server
4. 🧠 n8n AI Agent generates response (Ollama/Llama 3.1)
5. 🔊 Response synthesized (Piper TTS)
6. 💾 Conversation saved (ChromaDB)

Agent: "Hello Peter! How can I help you?"
```

### 📧 Scenario 2: Send Email
```
User: "Send an email to John"

Agent: "What's the subject of the email?"

User: "Meeting tomorrow"

Agent: "What would you like to say in the message?"

User: "Confirm meeting at 10am"

System:
1. 🤖 n8n AI Agent detects email intent
2. 🔍 Searches for contact "John" in MCP
3. ✉️ Email Agent workflow sends message
4. 📊 Action logged in MCP

Agent: "Email sent to John Doe successfully!"
```

### 🔄 Switch LLM Model
```bash
# Method 1: Ollama CLI
ollama pull mistral:7b
# Then restart agent or via API

# Method 2: REST API
curl -X POST http://jetson-ip:8000/switch-model \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral:7b"}'

# Method 3: Voice command (if implemented)
User: "Switch to Mistral model"
```

### 📊 Available LLM Models

| Model | Size | RAM | Speed | Use Case |
|-------|------|-----|-------|----------|
| **llama3.1:8b** | 4.7GB | ~6GB | Medium | Recommended - Balanced |
| **mistral:7b** | 4.1GB | ~5GB | Fast | Quick conversations |
| **phi3:medium** | 2.3GB | ~3GB | Ultra-fast | Short responses |
| **gemma2:9b** | 5.4GB | ~7GB | Medium | Excellent quality |
| **qwen2.5:7b** | 4.4GB | ~6GB | Fast | Multilingual |

---

## 🔧 Configuration

### 📝 Environment Variables (Raspberry Pi)
```bash
# raspberry-pi/.env

# IPs
RASPBERRY_PI_IP=192.168.1.100
JETSON_IP=192.168.1.101

# n8n
N8N_USER=admin
N8N_PASSWORD=YourSecurePassword123!

# PostgreSQL
POSTGRES_PASSWORD=YourPostgresPassword456!

# ChromaDB
CHROMA_TOKEN=YourChromaToken789!

# Grafana
GRAFANA_PASSWORD=admin

# Timezone
TZ=UTC
```

### ⚙️ Jetson Configuration
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
      model: "llama3.1:8b"  # Default model
      temperature: 0.7
      num_ctx: 8192
    api_server:
      enabled: true
      port: 8001

  vision:
    enabled: true
    camera:
      type: "csi"  # or "usb"
      device: 0

  audio:
    enabled: true
    speaker:
      device: "pulse"  # For Bluetooth
```

---

## 🧪 Testing

### ✅ Full System Test
```bash
# 1. Check Raspberry Pi services
curl http://raspberry-pi-ip:8080/health  # MCP Server
curl http://raspberry-pi-ip:5678        # n8n

# 2. Check Jetson
curl http://jetson-ip:8000/status       # Agent
curl http://jetson-ip:8001/health       # LLM Server
curl http://jetson-ip:11434/api/tags    # Ollama

# 3. Test LLM
curl -X POST http://jetson-ip:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "messages": [{"role": "user", "content": "Hello"}]
  }'

# 4. Test complete workflow
curl -X POST http://raspberry-pi-ip:5678/webhook/agent-input \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, how are you?",
    "user_identity": "Test User"
  }'
```

---

## 📊 Monitoring

### 🎛️ Available Dashboards

- **Grafana**: http://raspberry-pi-ip:3000 (admin/admin)
- **n8n**: http://raspberry-pi-ip:5678
- **MCP Stats**: http://raspberry-pi-ip:8080/stats
- **Prometheus**: http://raspberry-pi-ip:9090

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

## 💰 Costs

### 💵 Total Budget
```
OWNED HARDWARE:
✅ Jetson Orin Nano Super: $0
✅ Raspberry Pi Camera: $0
✅ Bluetooth Speaker: $0

HARDWARE TO BUY:
- Raspberry Pi 5 (8GB): ~$110
- NVMe SSD 512GB (Jetson): ~$50
- USB SSD 256GB (RPi): ~$40
- USB Microphone: ~$30
- Case + accessories: ~$40

TOTAL: ~$270

SOFTWARE: $0 (100% open source)

ELECTRICITY:
- Jetson (15W avg): ~$40/year
- RPi 5 (10W avg): ~$25/year
- Total: ~$65/year

CLOUD COMPARISON (5 years):
- OpenAI + APIs: $10,000-$30,000
- Our solution: $270 + $325 = $595
- SAVINGS: $9,405-$29,405! 🎉
```

---

## 🔧 Troubleshooting

### ❌ Common Issues

#### MCP Server won't start
```bash
docker logs mcp-server
docker-compose restart postgres redis mcp-server
```

#### Jetson can't connect to MCP
```bash
# Check network
ping raspberry-pi-ip

# Check config
cat ~/multi-agent-system/jetson/config.yml | grep raspberry_pi_ip

# Test WebSocket
wscat -c ws://raspberry-pi-ip:8081/ws/agent/test
```

#### Ollama not responding
```bash
# Restart Ollama
sudo systemctl restart ollama

# Check models
ollama list

# Re-download
ollama pull llama3.1:8b

# Test directly
ollama run llama3.1:8b "Test"
```

#### Audio not working
```bash
# List devices
arecord -l  # Microphones
aplay -l    # Speakers

# Test microphone
arecord -d 3 test.wav && aplay test.wav

# Test TTS
echo "Test" | piper --model en_US-lessac-medium --output_file test.wav
paplay test.wav
```

---

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the project
2. Create a branch (`git checkout -b feature/improvement`)
3. Commit (`git commit -m 'Add feature'`)
4. Push (`git push origin feature/improvement`)
5. Open a Pull Request

---

## 📝 License

MIT License - see [LICENSE](LICENSE)

You are free to use, modify, and distribute this project.

---

## 🙏 Acknowledgments

This project uses these excellent open-source tools:

- [Ollama](https://ollama.com/) - Simplified LLM management
- [Ultralytics YOLOv11](https://github.com/ultralytics/ultralytics) - Object detection
- [Whisper.cpp](https://github.com/ggerganov/whisper.cpp) - Speech-to-Text
- [Piper TTS](https://github.com/rhasspy/piper) - Text-to-Speech
- [n8n](https://github.com/n8n-io/n8n) - Workflow orchestration
- [InsightFace](https://github.com/deepinsight/insightface) - Face recognition
- [ChromaDB](https://github.com/chroma-core/chroma) - Vector database
- [FastAPI](https://github.com/tiangolo/fastapi) - API framework

---

## 📞 Support

- 🐛 **Bugs**: [Open an issue](https://github.com/YOUR_USERNAME/multi-agent-system/issues)
- 💬 **Questions**: [GitHub Discussions](https://github.com/YOUR_USERNAME/multi-agent-system/discussions)
- 📖 **Documentation**: [Wiki](https://github.com/YOUR_USERNAME/multi-agent-system/wiki)

---

## 🗺️ Roadmap

- [ ] Multi-user support
- [ ] Web configuration interface
- [ ] Vision model support (LLaVA, Qwen-VL)
- [ ] Home Assistant integration
- [ ] Additional language support
- [ ] Mobile app (remote control)
- [ ] Advanced RAG with personal documents
- [ ] Custom model fine-tuning

---

## ⭐ Stats

![GitHub stars](https://img.shields.io/github/stars/YOUR_USERNAME/multi-agent-system?style=social)
![GitHub forks](https://img.shields.io/github/forks/YOUR_USERNAME/multi-agent-system?style=social)
![GitHub issues](https://img.shields.io/github/issues/YOUR_USERNAME/multi-agent-system)

---

**Built with ❤️ for the open-source community**

⭐ **If this project helps you, give it a star on GitHub!**