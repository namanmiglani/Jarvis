"""
WebSocket Server for Jarvis HUD

Broadcasts agent state changes to connected HUD clients.
"""

import asyncio
import json
import logging
from typing import Set
import websockets
from websockets.server import WebSocketServerProtocol

logger = logging.getLogger(__name__)


class HUDServer:
    """WebSocket server for HUD communication."""
    
    def __init__(self, host="localhost", port=8765):
        """
        Initialize HUD server.
        
        Args:
            host: Server host
            port: Server port
        """
        self.host = host
        self.port = port
        self.clients: Set[WebSocketServerProtocol] = set()
        self.server = None
        logger.info(f"HUD Server initialized on {host}:{port}")
    
    async def start(self):
        """Start the WebSocket server."""
        self.server = await websockets.serve(
            self._handle_client,
            self.host,
            self.port
        )
        logger.info(f"✅ HUD Server started on ws://{self.host}:{self.port}")
    
    async def _handle_client(self, websocket: WebSocketServerProtocol):
        """Handle new client connection."""
        self.clients.add(websocket)
        logger.info(f"HUD client connected. Total clients: {len(self.clients)}")
        
        try:
            # Send initial state
            await websocket.send(json.dumps({
                "type": "state",
                "state": "idle"
            }))
            
            # Keep connection alive
            async for message in websocket:
                # Handle incoming messages if needed
                logger.debug(f"Received from HUD: {message}")
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.remove(websocket)
            logger.info(f"HUD client disconnected. Total clients: {len(self.clients)}")
    
    async def broadcast(self, message: dict):
        """
        Broadcast message to all connected clients.
        
        Args:
            message: Dictionary to send as JSON
        """
        if not self.clients:
            return
        
        message_json = json.dumps(message)
        disconnected = set()
        
        for client in self.clients:
            try:
                await client.send(message_json)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
        
        # Remove disconnected clients
        self.clients -= disconnected
    
    async def send_state(self, state: str, data: dict = None):
        """
        Send agent state update.
        
        Args:
            state: Agent state (idle, wake_word, listening, thinking, speaking)
            data: Additional data
        """
        message = {
            "type": "state",
            "state": state
        }
        if data:
            message.update(data)
        
        await self.broadcast(message)
        logger.info(f"Sent state to HUD: {state}")
    
    async def send_weather(self, weather_data: dict):
        """
        Send weather data to HUD.
        
        Args:
            weather_data: Weather information
        """
        await self.broadcast({
            "type": "weather",
            "data": weather_data
        })
        logger.info("Sent weather data to HUD")
    
    async def send_transcription(self, text: str):
        """
        Send transcription to HUD.
        
        Args:
            text: Transcribed text
        """
        await self.broadcast({
            "type": "transcription",
            "text": text
        })
        logger.info(f"Sent transcription to HUD: {text}")
    
    async def send_response(self, text: str):
        """
        Send Jarvis response to HUD.
        
        Args:
            text: Response text
        """
        await self.broadcast({
            "type": "response",
            "text": text
        })
        logger.info(f"Sent response to HUD: {text}")
    
    async def stop(self):
        """Stop the WebSocket server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("HUD Server stopped")
