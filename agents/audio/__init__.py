"""
Audio Agent

Handles wake word detection, speech-to-text, and text-to-speech.
Uses OpenWakeWord for wake word detection (fully open source, no API key needed).
Uses OpenAI Whisper for speech-to-text (local, offline).
"""

import asyncio
import logging
import ssl
import numpy as np
import pyaudio
import whisper
import webrtcvad
from openwakeword.model import Model
from typing import Callable, Optional

# Disable SSL verification for Whisper model download (macOS certificate issue)
ssl._create_default_https_context = ssl._create_unverified_context

logger = logging.getLogger(__name__)


class AudioAgent:
    """Manages all audio input and output."""
    
    def __init__(self, on_wake_word_detected: Optional[Callable] = None):
        """
        Initialize Audio Agent.
        
        Args:
            on_wake_word_detected: Callback function when wake word is detected
        """
        self.state = "IDLE"  # IDLE, ACTIVE, TRANSLATION_MODE
        self.on_wake_word_detected = on_wake_word_detected
        self.wake_model = None
        self.whisper_model = None
        self.audio_stream = None
        self.pa = None
        self.is_listening = False
        self.in_conversation = False  # Flag to pause wake word detection during conversations
        
        # Voice Activity Detection
        self.vad = webrtcvad.Vad(3)  # Aggressiveness: 0-3 (3 = most aggressive)
        
        # TTS clients
        self.openai_client = None
        self.elevenlabs_api_key = None
        
        # Audio settings
        self.sample_rate = 16000
        self.chunk_size = 1280  # 80ms chunks at 16kHz
        
        logger.info("Audio Agent initialized")
        logger.info("✅ VAD initialized with aggressiveness: 3")
    
    async def start_wake_word_detection(self):
        """Start listening for wake word 'Hey Jarvis'."""
        logger.info("🎤 Starting wake word detection with OpenWakeWord...")
        
        try:
            # Download models on first run
            logger.info("Checking for wake word models...")
            import openwakeword
            try:
                openwakeword.utils.download_models()
                logger.info("✅ Wake word models ready")
            except Exception as e:
                logger.warning(f"Model download check: {e}")
            
            # Initialize OpenWakeWord model
            logger.info("Loading wake word model...")
            self.wake_model = Model(
                wakeword_models=["hey_jarvis"]
            )
            logger.info("✅ Wake word model loaded successfully")
            
            # Pre-load Whisper model to avoid delay on first transcription
            logger.info("Pre-loading Whisper model...")
            self.whisper_model = whisper.load_model("small")
            logger.info("✅ Whisper model pre-loaded")
            
            # Initialize PyAudio
            self.pa = pyaudio.PyAudio()
            
            # Open audio stream
            self.audio_stream = self.pa.open(
                rate=self.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            self.is_listening = True
            logger.info("✅ Wake word detection active. Say 'Hey Jarvis' to activate!")
            
            # Start listening loop
            await self._listen_for_wake_word()
            
        except Exception as e:
            logger.error(f"❌ Error starting wake word detection: {e}")
            logger.error(f"Error details: {type(e).__name__}")
            await self.stop()
    
    def pause_wake_word_detection(self):
        """Pause wake word detection during active conversation."""
        logger.info("⏸️  Pausing wake word detection")
        self.in_conversation = True
    
    async def resume_wake_word_detection(self):
        """Resume wake word detection after conversation ends."""
        logger.info("▶️  Resuming wake word detection...")
        
        # Wait for TTS to complete and audio to settle
        await asyncio.sleep(2)
        
        # Clear any remaining audio buffer
        self._clear_audio_buffer()
        
        # Reset wake word model's internal state by feeding silent audio
        # OpenWakeWord maintains ~32k sample buffer that needs flushing
        self._reset_wake_word_model_state()
        
        # Resume detection
        self.in_conversation = False
        logger.info("✅ Wake word detection resumed")
    
    def _reset_wake_word_model_state(self):
        """Reset the wake word model's internal state by feeding silent audio."""
        if not self.wake_model:
            return
        
        try:
            # Feed ~32,000 samples of silence to flush model's internal buffer
            # At 1280 samples per chunk, need ~25 chunks
            silent_chunk = np.zeros(self.chunk_size, dtype=np.int16)
            
            for i in range(30):  # Extra margin for safety
                self.wake_model.predict(silent_chunk)
            
            logger.info("🔄 Wake word model state reset")
        except Exception as e:
            logger.warning(f"Error resetting wake word model state: {e}")
    
    def _clear_audio_buffer(self):
        """Clear accumulated audio data from the stream buffer."""
        if not self.audio_stream:
            return
        
        try:
            # Read and discard all buffered audio chunks
            chunks_cleared = 0
            while self.audio_stream.get_read_available() > 0:
                self.audio_stream.read(
                    self.audio_stream.get_read_available(),
                    exception_on_overflow=False
                )
                chunks_cleared += 1
            
            if chunks_cleared > 0:
                logger.info(f"🧹 Cleared {chunks_cleared} audio buffer chunks")
        except Exception as e:
            logger.warning(f"Error clearing audio buffer: {e}")
    
    async def _listen_for_wake_word(self):
        """Continuous listening loop for wake word."""
        try:
            while self.is_listening:
                # Always read audio chunk to prevent buffer accumulation
                audio_data = self.audio_stream.read(
                    self.chunk_size,
                    exception_on_overflow=False
                )
                
                # Skip wake word detection if in active conversation
                if self.in_conversation:
                    await asyncio.sleep(0.01)
                    continue
                
                # Convert to numpy array
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                
                # Predict wake word
                prediction = self.wake_model.predict(audio_array)
                
                # Check if wake word detected (threshold: 0.9)
                for wake_word, score in prediction.items():
                    if score > 0.9:
                        logger.info(f"🎯 Wake word detected: '{wake_word}' (confidence: {score:.2f})")
                        
                        await self.play_chime()
                        
                        # Trigger callback (orchestrator will handle pausing)
                        if self.on_wake_word_detected:
                            await self.on_wake_word_detected()
                
                # Small delay to prevent CPU overload
                await asyncio.sleep(0.01)
                
        except Exception as e:
            logger.error(f"❌ Error in wake word listening loop: {e}")
            logger.error(f"Error type: {type(e).__name__}")
        finally:
            await self.stop()
    
    async def play_chime(self):
        """Play activation chime (visual feedback only)."""
        logger.info("🔔 *Chime sound* - Jarvis activated!")
        print("\n" + "="*50)
        print("🔔 Jarvis activated")
        print("="*50 + "\n")
    
    async def speech_to_text(self) -> str:
        """
        Record audio using VAD and convert speech to text using Whisper.
        
        Uses WebRTC VAD to dynamically detect when user stops speaking.
        Recording stops after 1.5 seconds of continuous silence or 10 seconds max.
        
        Returns:
            Transcribed text from user speech
        """
        logger.info("🎤 Listening for your command...")
        print("\n🎤 Listening... (speak now)\n")
        
        try:
            # Load Whisper model if not already loaded
            if self.whisper_model is None:
                logger.info("Loading Whisper model (first time only)...")
                print("⏳ Loading Whisper model... (this may take a moment)")
                self.whisper_model = whisper.load_model("tiny")  # Fast, ~75MB
                logger.info("✅ Whisper tiny model loaded")
            
            # VAD parameters
            MAX_RECORDING_TIME = 10  # Maximum seconds to record
            SILENCE_DURATION_TO_STOP = 1.5  # Seconds of silence before stopping
            FRAME_DURATION_MS = 30  # Frame duration for VAD (10, 20, or 30ms)
            SAMPLE_RATE = 16000  # Whisper expects 16kHz
            
            # Calculate frame size
            frame_size = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)
            
            # Open audio stream for recording
            stream = self.pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=frame_size
            )
            
            logger.info("Recording with VAD (will stop after silence)...")
            
            # Recording state
            frames = []
            silence_frames = 0
            max_silence_frames = int(SILENCE_DURATION_TO_STOP * 1000 / FRAME_DURATION_MS)
            max_frames = int(MAX_RECORDING_TIME * 1000 / FRAME_DURATION_MS)
            speech_detected = False
            
            import time
            start_time = time.time()
            
            # Record until silence or max time
            while len(frames) < max_frames:
                try:
                    # Read frame
                    frame_data = stream.read(frame_size, exception_on_overflow=False)
                    frames.append(frame_data)
                    
                    # Check if frame contains speech
                    is_speech = self.vad.is_speech(frame_data, SAMPLE_RATE)
                    
                    if is_speech:
                        silence_frames = 0  # Reset silence counter
                        speech_detected = True
                    else:
                        silence_frames += 1
                        
                        # Only stop on silence if we've detected speech first
                        if speech_detected and silence_frames >= max_silence_frames:
                            recording_time = time.time() - start_time
                            logger.info(f"✅ Recording stopped after {recording_time:.1f}s (VAD detected silence)")
                            break
                
                except Exception as e:
                    logger.warning(f"Error reading frame: {e}")
                    continue
            
            # Check if we hit max timeout
            if len(frames) >= max_frames:
                logger.info(f"✅ Recording stopped after {MAX_RECORDING_TIME}s (max timeout)")
            
            stream.stop_stream()
            stream.close()
            
            # Check if we recorded anything
            if not frames:
                logger.warning("No audio recorded")
                return ""
            
            logger.info(f"Recorded {len(frames)} frames, transcribing...")
            print("⏳ Transcribing...")
            
            # Convert audio data to numpy array
            audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
            audio_data = audio_data.astype(np.float32) / 32768.0  # Normalize to [-1, 1]
            
            # Transcribe with Whisper
            result = self.whisper_model.transcribe(
                audio_data,
                language="en",  # Can auto-detect by removing this
                fp16=False  # Use FP32 for CPU
            )
            
            transcription = result["text"].strip()
            logger.info(f"Transcription: {transcription}")
            
            return transcription
            
        except Exception as e:
            logger.error(f"❌ Error in speech-to-text: {e}")
            return ""
    
    async def text_to_speech(self, text: str):
        """
        Convert text to speech using OpenAI TTS and play it.
        
        Args:
            text: Text to convert to speech
        """
        logger.info(f"Speaking: {text}")
        
        try:
            from openai import AsyncOpenAI
            from openai.helpers import LocalAudioPlayer
            import os
            
            # Initialize OpenAI client if not already done
            if not hasattr(self, 'openai_client'):
                api_key = os.getenv('OPENAI_API_KEY')
                if not api_key:
                    raise ValueError("OPENAI_API_KEY not found in environment variables")
                self.openai_client = AsyncOpenAI(api_key=api_key)
                logger.info("✅ OpenAI TTS client initialized")
            
            # Generate and play speech with streaming
            logger.info("Generating speech with OpenAI TTS...")
            
            async with self.openai_client.audio.speech.with_streaming_response.create(
                model="gpt-4o-mini-tts",
                voice="cedar",
                input=text,
                instructions="Speak in a sophisticated, professional British accent like an advanced AI assistant.",
                response_format="pcm"
            ) as response:
                await LocalAudioPlayer().play(response)
            
            logger.info("✅ Audio playback complete")
            
        except Exception as e:
            logger.error(f"❌ Error in text-to-speech: {e}")
            logger.warning("Falling back to console output")
            print(f"\n🔊 Jarvis: {text}\n")
    
    async def text_to_speech_elevenlabs(self, text: str, voice_id: str = "JBFqnCBsd6RMkjVDRZzb"):
        """
        Convert text to speech using ElevenLabs WebSocket API and play it.
        
        Args:
            text: Text to convert to speech
            voice_id: ElevenLabs voice ID (default: Rachel - natural, expressive)
        """
        logger.info(f"Speaking with ElevenLabs: {text}")
        
        try:
            import websockets
            import json
            import base64
            import os
            
            # Get API key
            if not self.elevenlabs_api_key:
                self.elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')
                if not self.elevenlabs_api_key:
                    raise ValueError("ELEVENLABS_API_KEY not found in environment variables")
            
            # WebSocket URL - using pcm_44100 for CD-quality audio
            uri = f"wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input?model_id=eleven_turbo_v2_5&output_format=pcm_24000"
            
            # Initialize PyAudio for playback (44.1kHz for higher quality)
            stream = self.pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=24000,  # CD-quality sample rate
                output=True,
                frames_per_buffer=2048  # Larger buffer for 44.1kHz
            )
            
            logger.info("Connecting to ElevenLabs WebSocket...")
            
            # Create SSL context that doesn't verify certificates (macOS issue)
            import ssl
            ssl_context = ssl._create_unverified_context()
            
            async with websockets.connect(uri, ssl=ssl_context) as websocket:
                # Send initial connection message with API key
                init_message = {
                    "text": " ",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.8,
                        "speed": 1.0,
                    },
                    "xi-api-key": self.elevenlabs_api_key
                }
                await websocket.send(json.dumps(init_message))
                
                # Send the actual text
                text_message = {
                    "text": text + " ",
                    "try_trigger_generation": True
                }
                await websocket.send(json.dumps(text_message))
                
                # Send flush to ensure all audio is generated
                flush_message = {
                    "text": "",
                }
                await websocket.send(json.dumps(flush_message))
                
                logger.info("Receiving and playing audio...")
                
                # Receive and play audio chunks
                async for message in websocket:
                    data = json.loads(message)
                    
                    # Check if this is the final message
                    if data.get("isFinal"):
                        logger.info("✅ ElevenLabs audio generation complete")
                        break
                    
                    # Decode and play audio chunk
                    if "audio" in data:
                        audio_chunk = base64.b64decode(data["audio"])
                        stream.write(audio_chunk)
            
            # Cleanup
            stream.stop_stream()
            stream.close()
            
            logger.info("✅ Audio playback complete")
            
        except Exception as e:
            logger.error(f"❌ Error in ElevenLabs TTS: {e}")
            logger.warning("Falling back to console output")
            print(f"\n🔊 Jarvis: {text}\n")
    
    async def stop(self):
        """Stop wake word detection and cleanup resources."""
        logger.info("Stopping Audio Agent...")
        self.is_listening = False
        
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
        
        if self.pa:
            self.pa.terminate()
        
        logger.info("✅ Audio Agent stopped")
