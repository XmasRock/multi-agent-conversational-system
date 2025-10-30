# jetson/modules/audio_agent.py
import asyncio
import pyaudio
import wave
import numpy as np
from pathlib import Path
import logging
import subprocess
import tempfile

logger = logging.getLogger(__name__)

class AudioAgent:
    """Agent audio - Whisper STT + Piper TTS"""
    
    def __init__(self, config: dict):
        self.config = config
        
        # PyAudio
        self.audio = pyaudio.PyAudio()
        
        # Configuration speaker
        speaker_device = config['speaker']['device']
        
        # Trouver index device Bluetooth
        if speaker_device == "pulse":
            # PulseAudio gère automatiquement Bluetooth
            self.speaker_index = None  # Utilise default
        else:
            self.speaker_index = self.find_device_index(speaker_device)

        # Microphone
        mic_config = config['microphone']
        self.sample_rate = mic_config['sample_rate']
        self.channels = mic_config['channels']
        self.chunk_duration_ms = 1000  # 1 seconde
        self.chunk_size = int(self.sample_rate * self.chunk_duration_ms / 1000)
        
        self.mic_stream = None
        
        # Speaker
        self.speaker_device = config['speaker']['device']
        
        # Whisper
        self.whisper_model = config['stt']['model']
        self.whisper_language = config['stt']['language']
        
        # Piper TTS
        self.tts_model = config['tts']['model']
        self.tts_rate = config['tts']['rate']
        
        # État
        self.is_listening = False
        
        self.open_microphone()
        
        logger.info("✅ Audio Agent initialisé")
    
    def open_microphone(self):
        """Ouvrir stream microphone"""
        try:
            self.mic_stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            self.is_listening = True
            logger.info("🎤 Microphone ouvert")
        except Exception as e:
            logger.error(f"❌ Erreur ouverture micro: {e}")
    
    async def listen(self) -> Optional[bytes]:
        """Écouter un chunk audio"""
        if not self.mic_stream or not self.is_listening:
            return None
        
        try:
            # Lire chunk
            data = await asyncio.to_thread(
                self.mic_stream.read,
                self.chunk_size,
                exception_on_overflow=False
            )
            
            # Vérifier si audio contient de la parole (simple VAD)
            audio_array = np.frombuffer(data, dtype=np.int16)
            volume = np.abs(audio_array).mean()
            
            if volume < 500:  # Seuil silence
                return None
            
            return data
            
        except Exception as e:
            logger.error(f"❌ Erreur écoute: {e}")
            return None
    
    async def transcribe(self, audio_data: bytes) -> str:
        """Transcrire audio avec Whisper"""
        try:
            # Sauvegarder audio temporaire
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                # Écrire WAV
                wf = wave.open(tmp.name, 'wb')
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_data)
                wf.close()
                
                # Whisper.cpp
                result = await asyncio.to_thread(
                    subprocess.run,
                    [
                        './whisper.cpp/main',
                        '-m', self.whisper_model,
                        '-l', self.whisper_language,
                        '-f', tmp.name,
                        '--no-timestamps'
                    ],
                    capture_output=True,
                    text=True
                )
                
                # Parser sortie
                text = result.stdout.strip()
                
                # Nettoyer
                Path(tmp.name).unlink()
                
                return text
                
        except Exception as e:
            logger.error(f"❌ Erreur transcription: {e}")
            return ""
    
    async def speak(self, text: str):
        """Synthèse vocale avec Piper"""
        if not text:
            return
        
        try:
            logger.info(f"🔊 TTS: {text}")
            
            # Générer audio avec Piper
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                process = await asyncio.create_subprocess_exec(
                    'piper',
                    '--model', self.tts_model,
                    '--output_file', tmp.name,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                await process.communicate(input=text.encode())
                
                # Jouer audio
                await asyncio.to_thread(
                    subprocess.run,
                    ['aplay', tmp.name],
                    check=True
                )
                
                # Nettoyer
                Path(tmp.name).unlink()
                
        except Exception as e:
            logger.error(f"❌ Erreur TTS: {e}")
    
    def stop(self):
        """Arrêter agent audio"""
        self.is_listening = False
        if self.mic_stream:
            self.mic_stream.stop_stream()
            self.mic_stream.close()
        if self.audio:
            self.audio.terminate()
        logger.info("🛑 Audio Agent arrêté")

    def find_device_index(self, device_name: str) -> int:
        """Trouver index device audio par nom"""
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if device_name.lower() in info['name'].lower():
                logger.info(f"🔊 Device trouvé: {info['name']} (index {i})")
                return i
        
        logger.warning(f"⚠️  Device '{device_name}' non trouvé, utilisation default")
        return None
    
    async def speak(self, text: str):
        """Synthèse vocale avec Piper → Bluetooth"""
        if not text:
            return
        
        try:
            logger.info(f"🔊 TTS: {text}")
            
            # Générer audio avec Piper
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                # Piper génère WAV
                process = await asyncio.create_subprocess_exec(
                    'piper',
                    '--model', self.tts_model,
                    '--output_file', tmp.name,
                    stdin=asyncio.subprocess.PIPE
                )
                await process.communicate(input=text.encode())
                
                # Jouer via PulseAudio (Bluetooth)
                if self.speaker_device == "pulse":
                    # Utiliser paplay (PulseAudio)
                    await asyncio.to_thread(
                        subprocess.run,
                        ['paplay', tmp.name],
                        check=True
                    )
                else:
                    # Ou aplay avec device spécifique
                    await asyncio.to_thread(
                        subprocess.run,
                        ['aplay', '-D', self.speaker_device, tmp.name],
                        check=True
                    )
                
                Path(tmp.name).unlink()
                
        except Exception as e:
            logger.error(f"❌ Erreur TTS Bluetooth: {e}")