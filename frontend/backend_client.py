"""
Backend Client - WebSocket client for HUD

Connects to Jarvis backend and receives real-time state updates.
"""

import asyncio
import json
import logging
from typing import Callable, Optional
import websockets

logger = logging.getLogger(__name__)


class BackendClient:
    """WebSocket client for connecting to Jarvis backend."""
    
    def __init__(self, host="localhost", port=8765):
        """
        Initialize backend client.
        
        Args:
            host: Backend host
            port: Backend port
        """
        self.host = host
        self.port = port
        self.uri = f"ws://{host}:{port}"
        self.websocket = None
        self.running = False
        
        # Callbacks
        self.on_state_change: Optional[Callable] = None
        self.on_weather_update: Optional[Callable] = None
        self.on_snapshot_update: Optional[Callable] = None
        self.on_transcription: Optional[Callable] = None
        self.on_response: Optional[Callable] = None
    
    async def connect(self):
        """Connect to backend WebSocket server."""
        try:
            self.websocket = await websockets.connect(self.uri)
            self.running = True
            logger.info(f"✅ Connected to backend at {self.uri}")
            
            # Start listening for messages
            asyncio.create_task(self._listen())
        except Exception as e:
            logger.error(f"❌ Failed to connect to backend: {e}")
            self.running = False
    
    async def _listen(self):
        """Listen for messages from backend."""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self._handle_message(data)
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Connection to backend closed")
            self.running = False
        except Exception as e:
            logger.error(f"Error in listen loop: {e}")
            self.running = False
    
    async def _handle_message(self, data: dict):
        """Handle incoming message from backend."""
        msg_type = data.get("type")
        
        if msg_type == "state":
            state = data.get("state")
            logger.info(f"State update: {state}")
            if self.on_state_change:
                self.on_state_change(state, data)
        
        elif msg_type == "weather":
            weather_data = data.get("data")
            logger.info("Weather update received")
            if self.on_weather_update:
                self.on_weather_update(weather_data)
        
        elif msg_type == "snapshot":
            snapshot_data = data.get("data")
            logger.info("Snapshot update received")
            if self.on_snapshot_update:
                self.on_snapshot_update(snapshot_data)
        
        elif msg_type == "transcription":
            text = data.get("text")
            logger.info(f"Transcription: {text}")
            if self.on_transcription:
                self.on_transcription(text)
        
        elif msg_type == "response":
            text = data.get("text")
            logger.info(f"Response: {text}")
            if self.on_response:
                self.on_response(text)
    
    async def disconnect(self):
        """Disconnect from backend."""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            logger.info("Disconnected from backend")
    
    def is_connected(self):
        """Check if connected to backend."""
        return self.running and self.websocket is not None
