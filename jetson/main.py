# jetson/main.py
import asyncio
import signal
import sys
import yaml
import logging
from pathlib import Path

from api_server import APIServer
from llm_server import LLMServer
from mcp_client import MCPClient
from modules.vision_agent import VisionAgent
from modules.audio_agent import AudioAgent
from modules.llm_agent import LLMAgent
from modules.action_agent import ActionAgent
from modules.mqtt_client import MQTTClient
from utils.logger import setup_logger

class ConversationalAgent:
    def __init__(self, config_path: str = "config.yml"):
        # Charger config
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Setup logging
        self.logger = setup_logger(self.config['logging'])
        self.logger.info("🚀 Initialisation Agent Conversationnel...")
        
        # Initialiser composants
        self.mcp_client = MCPClient(
            agent_id=self.config['agent']['id'],
            agent_type=self.config['agent']['type'],
            mcp_host=self.config['network']['mcp_server']['host'],
            mcp_port=self.config['network']['mcp_server']['ws_port']
        )
        
        self.mqtt_client = MQTTClient(
            broker_host=self.config['network']['mqtt_broker']['host'],
            broker_port=self.config['network']['mqtt_broker']['port'],
            client_id=self.config['agent']['id']
        )
        
        # Modules
        if self.config['modules']['vision']['enabled']:
            self.vision = VisionAgent(self.config['modules']['vision'])
        else:
            self.vision = None
        
        if self.config['modules']['audio']['enabled']:
            self.audio = AudioAgent(self.config['modules']['audio'])
        else:
            self.audio = None
        
        if self.config['modules']['llm']['enabled']:
            self.llm = LLMAgent(self.config['modules']['llm'])
            # LLM Server pour n8n
            self.llm_server = LLMServer(
                llm_agent=self.llm,
                port=self.config['modules']['llm']['api_port']
            )
        else:
            self.llm = None
            self.llm_server = None
        
        self.actions = ActionAgent(self.config, self.mqtt_client)
        
        # API Server
        self.api_server = APIServer(
            agent=self,
            port=8000
        )
        
        # État
        self.running = False
        self.current_user = None
        
        self.logger.info("✅ Agent initialisé")
    
    async def start(self):
        """Démarrer agent avec gestion reconnexions"""
        self.logger.info("▶️  Démarrage agent...")
        self.running = True
        
        # Connexion MCP (blocking jusqu'à connexion)
        mcp_task = asyncio.create_task(self.mcp_client.connect())
        
        # Connexion MQTT avec retry
        mqtt_connected = await self.mqtt_client.connect()
        if mqtt_connected:
            await self.mqtt_client.subscribe("jetson/#")
            self.mqtt_client.on_message(self.handle_mqtt_message)
        else:
            self.logger.warning("⚠️  MQTT non connecté, fonctionnement dégradé")
        
        # Démarrer serveurs et boucles
        tasks = [
            mcp_task,  # Boucle de reconnexion MCP
            self.api_server.start(),
        ]
        
        if self.llm_server:
            tasks.append(self.llm_server.start())
        
        if self.vision:
            tasks.append(self.vision_loop())
        
        if self.audio:
            tasks.append(self.audio_loop())
        
        # Surveillance état connexions
        tasks.append(self.connection_monitor())
        
        # Exécuter
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def connection_monitor(self):
        """Surveiller état connexions et alerter"""
        while self.running:
            try:
                await asyncio.sleep(60)  # Vérifier chaque minute
                
                # État connexions
                mcp_status = "✅" if self.mcp_client.connected else "❌"
                mqtt_status = "✅" if self.mqtt_client.connected else "❌"
                
                self.logger.info(
                    f"🔍 État connexions: "
                    f"MCP {mcp_status} | "
                    f"MQTT {mqtt_status}"
                )
                
                # Alertes si problème persistant
                if not self.mcp_client.connected:
                    self.logger.warning(
                        f"⚠️  MCP déconnecté depuis "
                        f"{self.mcp_client.reconnect_attempts} tentatives"
                    )
                
            except Exception as e:
                self.logger.error(f"❌ Erreur monitor connexions: {e}")

    
    async def vision_loop(self):
        """Boucle vision continue"""
        self.logger.info("👁️  Boucle vision démarrée")
        
        while self.running:
            try:
                # Capturer et traiter frame
                results = await self.vision.process_frame()
                
                if results and len(results) > 0:
                    # Mise à jour utilisateur actuel
                    self.current_user = results[0].get('identity', 'Unknown')
                    
                    # Publier au MCP
                    await self.mcp_client.publish_context(
                        context_type="vision_perception",
                        data={
                            "detected_persons": len(results),
                            "identities": [r.get('identity') for r in results],
                            "bboxes": [r.get('bbox') for r in results],
                            "confidences": [r.get('confidence') for r in results]
                        },
                        priority=3
                    )
                
                await asyncio.sleep(1.0 / 15)  # 15 FPS
                
            except Exception as e:
                self.logger.error(f"❌ Erreur vision loop: {e}")
                await asyncio.sleep(1.0)
    
    async def audio_loop(self):
        """Boucle audio - écoute continue"""
        self.logger.info("🎤 Boucle audio démarrée")
        
        while self.running:
            try:
                # Écouter audio
                audio_data = await self.audio.listen()
                
                if audio_data is None:
                    continue
                
                # STT
                text = await self.audio.transcribe(audio_data)
                
                if not text or len(text.strip()) < 3:
                    continue
                
                self.logger.info(f"🗣️  Utilisateur: {text}")
                
                # Publier au MCP
                await self.mcp_client.publish_context(
                    context_type="user_speech",
                    data={
                        "text": text,
                        "user": self.current_user or "Unknown",
                        "language": "fr"
                    },
                    priority=5
                )
                
                # Traiter localement
                await self.process_user_input(text)
                
            except Exception as e:
                self.logger.error(f"❌ Erreur audio loop: {e}")
                await asyncio.sleep(0.5)
    
    async def process_user_input(self, text: str):
        """Traiter input utilisateur"""
        try:
            # Requérir contexte global
            # (le MCP répondra via callback)
            await self.mcp_client.query("get_current_context")
            
            # Attendre un peu pour recevoir contexte
            await asyncio.sleep(0.1)
            
            # Générer réponse LLM
            context_data = {
                "user_identity": self.current_user or "Unknown",
                "location": "Bureau",  # TODO: dynamique
                "time": datetime.now().isoformat()
            }
            
            response = await self.llm.generate(
                prompt=text,
                context=context_data
            )
            
            self.logger.info(f"🤖 Assistant: {response['text']}")
            
            # Détecter si action nécessaire
            action = self.detect_action(response['text'])
            
            if action:
                await self.execute_action(action)
            
            # TTS
            await self.audio.speak(response['text'])
            
            # Publier réponse au MCP
            await self.mcp_client.publish_context(
                context_type="agent_response",
                data={
                    "text": response['text'],
                    "to_user": self.current_user
                },
                priority=4
            )
            
        except Exception as e:
            self.logger.error(f"❌ Erreur traitement input: {e}")
    
    def detect_action(self, text: str) -> Optional[dict]:
        """Détecter si une action est requise dans le texte"""
        text_lower = text.lower()
        
        # Patterns simples (en production, utiliser function calling du LLM)
        if any(word in text_lower for word in ['email', 'mail', 'envoie', 'envoyer']):
            return {"type": "send_email", "text": text}
        
        if any(word in text_lower for word in ['recherche', 'cherche', 'google', 'trouve']):
            return {"type": "web_search", "text": text}
        
        if any(word in text_lower for word in ['calendrier', 'agenda', 'rendez-vous', 'réunion']):
            return {"type": "calendar", "text": text}
        
        return None
    
    async def execute_action(self, action: dict):
        """Exécuter une action (via n8n ou local)"""
        # Envoyer à n8n pour orchestration
        await self.actions.request_n8n_action(action)
    
    async def handle_mcp_action(self, data: dict):
        """Gérer action reçue du MCP"""
        action = data.get('action')
        params = data.get('parameters', {})
        
        self.logger.info(f"🎯 Action MCP reçue: {action}")
        
        if action == "speak":
            await self.audio.speak(params.get('text', ''))
        
        elif action == "analyze_vision":
            if self.vision:
                results = await self.vision.get_current_results()
                # Renvoyer via MCP
                await self.mcp_client.publish_context(
                    context_type="vision_analysis",
                    data={"results": results},
                    priority=4
                )
        
        elif action == "listen":
            # Déjà en écoute continue, mais on peut forcer une écoute
            pass
    
    async def handle_mcp_notification(self, data: dict):
        """Gérer notification contexte d'autres agents"""
        context = data.get('context', {})
        context_type = context.get('context_type')
        
        self.logger.info(f"📢 Notification MCP: {context_type}")
        
        # Exemples de réactions
        if context_type == "new_email":
            sender = context.get('data', {}).get('from', 'quelqu\'un')
            await self.audio.speak(f"Vous avez reçu un email de {sender}")
        
        elif context_type == "calendar_reminder":
            event = context.get('data', {}).get('event', 'un événement')
            await self.audio.speak(f"Rappel: {event}")
    
    async def handle_mqtt_message(self, topic: str, payload: str):
        """Gérer messages MQTT"""
        self.logger.debug(f"📨 MQTT reçu sur {topic}: {payload}")
        
        try:
            data = json.loads(payload)
            
            # Router selon topic
            if topic == "jetson/audio/speak":
                await self.audio.speak(data.get('text', ''))
            
            elif topic == "jetson/vision/analyze":
                if self.vision:
                    results = await self.vision.get_current_results()
                    await self.mqtt_client.publish(
                        "jetson/vision/results",
                        json.dumps(results)
                    )
            
            elif topic == "jetson/control/reboot":
                self.logger.warning("🔄 Redémarrage demandé via MQTT")
                await self.stop()
                # Relancer dans systemd
            
        except json.JSONDecodeError:
            self.logger.error(f"❌ Payload MQTT invalide: {payload}")
    
    async def heartbeat_loop(self):
        """Heartbeat périodique vers MCP"""
        while self.running:
            try:
                await self.mcp_client.send_heartbeat()
                await asyncio.sleep(30)  # Toutes les 30s
            except Exception as e:
                self.logger.error(f"❌ Erreur heartbeat: {e}")
                await asyncio.sleep(5)
    
    async def stop(self):
        """Arrêter agent proprement"""
        self.logger.info("🛑 Arrêt agent...")
        self.running = False
        
        # Déconnexions
        if self.mcp_client:
            await self.mcp_client.disconnect()
        
        if self.mqtt_client:
            await self.mqtt_client.disconnect()
        
        # Arrêt modules
        if self.vision:
            self.vision.stop()
        
        if self.audio:
            self.audio.stop()
        
        if self.llm:
            self.llm.stop()
        
        self.logger.info("✅ Agent arrêté")

async def main():
    # Charger agent
    agent = ConversationalAgent("config.yml")
    
    # Gestion signaux
    def signal_handler(signum, frame):
        print("\n🛑 Signal reçu, arrêt en cours...")
        asyncio.create_task(agent.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await agent.start()
    except KeyboardInterrupt:
        await agent.stop()
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        await agent.stop()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())