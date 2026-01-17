"""
Orchestrator Agent

Central coordinator that manages all other agents and conversation flow.
"""

import asyncio
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """Central hub that coordinates all agents."""
    
    def __init__(self):
        self.is_active = False
        self.current_intent = None
        self.audio_agent = None
        logger.info("Orchestrator Agent initialized")
    
    async def start(self):
        """Start the orchestrator and all sub-agents."""
        logger.info("🚀 Starting Orchestrator Agent...")
        self.is_active = True
        
        # Initialize Audio Agent with wake word callback
        from agents.audio import AudioAgent
        self.audio_agent = AudioAgent(on_wake_word_detected=self.on_wake_word_detected)
        
        # TODO: Initialize other agents in future phases
        # self.reasoning_agent = ReasoningAgent()
        # self.tool_executor = ToolExecutorAgent()
        # self.memory_agent = MemoryAgent()
        # self.vision_agent = VisionAgent()
        
        # Start wake word detection
        logger.info("Starting wake word detection...")
        await self.audio_agent.start_wake_word_detection()
    
    async def on_wake_word_detected(self):
        """Callback when wake word 'Hey Jarvis' is detected."""
        logger.info("🎯 Wake word callback triggered!")
        
        # TODO Phase 2: Start listening for user command (STT)
        # TODO Phase 3: Send to Reasoning Agent for intent classification
        # TODO Phase 4+: Execute appropriate action
        
        print("✅ Jarvis is now listening for your command...")
        print("(Phase 2 will add speech-to-text here)\n")
    
    async def process_input(self, source: str, data: Dict[str, Any]):
        """Process input from any agent."""
        logger.info(f"Processing input from {source}: {data}")
        
        # TODO: Route to appropriate agent based on source and data
        pass
    
    async def stop(self):
        """Stop the orchestrator and cleanup."""
        logger.info("Stopping Orchestrator Agent...")
        self.is_active = False
        
        if self.audio_agent:
            await self.audio_agent.stop()

