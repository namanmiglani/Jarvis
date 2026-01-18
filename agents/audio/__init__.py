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
        
        # Audio settings
        self.sample_rate = 16000
        self.chunk_size = 1280  # 80ms chunks at 16kHz
        
        logger.info("Audio Agent initialized")
    
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
    
    async def _listen_for_wake_word(self):
        """Continuous listening loop for wake word."""
        try:
            while self.is_listening:
                # Read audio chunk
                audio_data = self.audio_stream.read(
                    self.chunk_size,
                    exception_on_overflow=False
                )
                
                # Convert to numpy array
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                
                # Predict wake word
                prediction = self.wake_model.predict(audio_array)
                
                # Check if wake word detected (threshold: 0.5)
                for wake_word, score in prediction.items():
                    if score > 0.5:
                        logger.info(f"🎯 Wake word detected: '{wake_word}' (confidence: {score:.2f})")
                        await self.play_chime()
                        
                        # Trigger callback
                        if self.on_wake_word_detected:
                            await self.on_wake_word_detected()
                        
                        # Small delay to prevent multiple triggers
                        await asyncio.sleep(2)
                
                # Small delay to prevent CPU overload
                await asyncio.sleep(0.01)
                
        except Exception as e:
            logger.error(f"❌ Error in wake word listening loop: {e}")
            logger.error(f"Error type: {type(e).__name__}")
        finally:
            await self.stop()
    
    async def play_chime(self):
        """Play activation chime and greet user with TTS."""
        logger.info("🔔 *Chime sound* - Jarvis activated!")
        print("\n" + "="*50)
        print("🔔 Hi, how can I assist you?")
        print("="*50 + "\n")
        
        # Speak the greeting
        await self.text_to_speech("Hi, how can I assist you?")
    
    async def speech_to_text(self) -> str:
        """
        Record audio and convert speech to text using Whisper.
        
        Returns:
            Transcribed text from user speech
        """
        logger.info("🎤 Listening for your command...")
        print("\n🎤 Listening... (5 seconds)\n")
        
        try:
            # Load Whisper model if not already loaded
            if self.whisper_model is None:
                logger.info("Loading Whisper model (first time only)...")
                print("⏳ Loading Whisper model... (this may take a moment)")
                self.whisper_model = whisper.load_model("tiny")  # Fast, ~75MB
                logger.info("✅ Whisper model loaded")
            
            # Record audio for 5 seconds
            RECORD_SECONDS = 5
            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 16000  # Whisper expects 16kHz
            
            frames = []
            
            # Open audio stream for recording
            stream = self.pa.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
            
            logger.info(f"Recording for {RECORD_SECONDS} seconds...")
            
            # Record audio
            for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            
            logger.info("Recording complete, transcribing...")
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
                voice="onyx",  # Deep, sophisticated voice (most JARVIS-like)
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
