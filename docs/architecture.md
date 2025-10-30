┌────────────────────────────────────────────────────────────────┐
│              RASPBERRY PI 5 (Hub Orchestration)                │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  n8n AI Agent (Orchestrateur Principal)                  │ │
│  │  - Décisions intelligentes                               │ │
│  │  - Coordination workflows                                │ │
│  │  - Tool calling → agents spécialisés                     │ │
│  │  - LLM déporté vers Jetson (via API)                     │ │
│  └──────────────────────────────────────────────────────────┘ │
│                            ↕                                   │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  MCP Server (Hub de Contexte Central)                    │ │
│  │  - State management global                               │ │
│  │  - Mémoire partagée agents                               │ │
│  │  - WebSocket hub                                         │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                 │
│  [PostgreSQL] [Redis Cache] [ChromaDB] [MQTT Broker]          │
└────────────────────────────────────────────────────────────────┘
                     ↕ REST/WebSocket/MQTT ↕
┌────────────────────────────────────────────────────────────────┐
│           JETSON ORIN NANO (Perception & Intelligence)         │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  LLM Server (Llama 3.1 8B)                               │ │
│  │  - API compatible OpenAI                                 │ │
│  │  - Utilisé par n8n AI Agent                              │ │
│  │  - Inference optimisée TensorRT                          │ │
│  └──────────────────────────────────────────────────────────┘ │
│                            ↕                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   Vision    │  │    Audio    │  │   Actions   │          │
│  │   Agent     │  │    Agent    │  │   Agent     │          │
│  │             │  │             │  │             │          │
│  │  YOLOv11    │  │  Whisper    │  │  Executor   │          │
│  │  InsightFace│  │  Piper TTS  │  │  Local      │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  MCP Client (Connexion au Hub)                           │ │
│  │  - Publie perceptions                                    │ │
│  │  - Consomme contexte global                              │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
                            ↕
┌────────────────────────────────────────────────────────────────┐
│              AGENTS SPÉCIALISÉS (Extensibles)                  │
│                                                                 │
│  [Email Agent] [Web Search Agent] [Calendar Agent]            │
│  [IoT Agent] [Home Automation] [Custom Agents...]             │
└────────────────────────────────────────────────────────────────┘
```

---

## 📁 Structure du Projet Complète
```
multi-agent-system/
├── raspberry-pi/
│   ├── docker-compose.yml          # Stack complète RPi
│   ├── .env                         # Variables d'environnement
│   ├── .env.example
│   ├── init-db.sh                   # Init PostgreSQL
│   ├── mcp-server/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── main.py                  # MCP Server principal
│   │   ├── models.py                # Modèles Pydantic
│   │   ├── connection_manager.py   # Gestion WebSocket
│   │   ├── storage.py               # PostgreSQL/Redis
│   │   └── config.py
│   ├── n8n/
│   │   ├── workflows/
│   │   │   ├── master-ai-agent.json
│   │   │   ├── email-agent.json
│   │   │   ├── web-search-agent.json
│   │   │   ├── jetson-control.json
│   │   │   ├── mcp-context.json
│   │   │   └── calendar-agent.json
│   │   └── custom-nodes/           # Nodes n8n custom
│   ├── mosquitto/
│   │   └── config/
│   │       └── mosquitto.conf
│   ├── prometheus/
│   │   └── prometheus.yml
│   └── grafana/
│       └── dashboards/
│
├── jetson/
│   ├── requirements.txt
│   ├── config.yml                   # Configuration Jetson
│   ├── config.example.yml
│   ├── main.py                      # Entry point
│   ├── api_server.py                # FastAPI server
│   ├── llm_server.py                # LLM API (compatible OpenAI)
│   ├── mcp_client.py                # Client MCP
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── vision_agent.py          # YOLOv11 + InsightFace
│   │   ├── audio_agent.py           # Whisper + Piper
│   │   ├── llm_agent.py             # Llama 3.1 local
│   │   ├── action_agent.py          # Exécuteur actions
│   │   └── mqtt_client.py           # Client MQTT
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   ├── gpu_monitor.py
│   │   └── helpers.py
│   └── models/                      # Stockage modèles
│       ├── yolo11n.engine
│       ├── whisper-medium.bin
│       ├── llama-3.1-8b-q4.gguf
│       └── face_embeddings.pkl
│
├── agents/                          # Agents externes optionnels
│   ├── email-agent/
│   ├── web-search-agent/
│   └── iot-agent/
│
├── docs/
│   ├── architecture.md
│   ├── installation.md
│   └── workflows.md
│
└── README.md