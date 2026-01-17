"""
Audio Agent

Handles wake word detection, speech-to-text, and text-to-speech.
Uses OpenWakeWord for wake word detection (fully open source, no API key needed).
"""

import asyncio
import logging
import numpy as np
import pyaudio
from openwakeword.model import Model
from typing import Callable, Optional

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
        """Play activation chime (audio feedback)."""
        logger.info("🔔 *Chime sound* - Jarvis activated!")
        # TODO: Play actual audio file when we add TTS in Phase 2
        print("\n" + "="*50)
        print("🔔 *CHIME* - Yes, I'm listening.")
        print("="*50 + "\n")
    
    async def speech_to_text(self, audio_data):
        """Convert speech to text using Whisper (Phase 2)."""
        logger.info("Converting speech to text...")
        # TODO: Implement Whisper STT in Phase 2
        pass
    
    async def text_to_speech(self, text: str):
        """Convert text to speech (Phase 2)."""
        logger.info(f"Speaking: {text}")
        # TODO: Implement Google Cloud TTS in Phase 2
        pass
    
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
