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
        self.reasoning_agent = None
        self.memory_agent = None
        self.weather_tool = None
        self.graph = None  # LangGraph workflow
        logger.info("Orchestrator Agent initialized")
    
    async def start(self):
        """Start the orchestrator and all sub-agents."""
        logger.info("🚀 Starting Orchestrator Agent...")
        self.is_active = True
        
        # Initialize agents and tools
        from agents.audio import AudioAgent
        from agents.reasoning import ReasoningAgent, Intent
        from agents.memory import MemoryAgent
        from agents.tools import WeatherTool
        from agents.graph import JarvisGraph
        
        self.reasoning_agent = ReasoningAgent()
        self.memory_agent = MemoryAgent()
        self.weather_tool = WeatherTool()
        
        # Initialize LangGraph workflow
        self.graph = JarvisGraph(
            reasoning_agent=self.reasoning_agent,
            memory_agent=self.memory_agent,
            weather_tool=self.weather_tool
        )
        
        self.audio_agent = AudioAgent(on_wake_word_detected=self.on_wake_word_detected)
        
        # Start wake word detection
        logger.info("Starting wake word detection...")
        await self.audio_agent.start_wake_word_detection()
    
    async def on_wake_word_detected(self):
        """Callback when wake word 'Hey Jarvis' is detected."""
        logger.info("🎯 Wake word callback triggered!")
        
        # Pause wake word detection during conversation
        self.audio_agent.pause_wake_word_detection()
        
        # Greet the user
        await self.audio_agent.text_to_speech("Hi, how can I assist you?")
        
        # Multi-turn conversation loop
        max_turns = 10  # Prevent infinite loops
        for turn in range(max_turns):
            # Get user's speech command
            transcription = await self.audio_agent.speech_to_text()
            
            if not transcription:
                print("\n⚠️  No speech detected or transcription failed\n")
                await self.audio_agent.text_to_speech("I didn't catch that. Please try again.")
                logger.warning("No transcription received")
                break  # Exit conversation loop
            
            print("\n" + "="*50)
            print(f"📝 You said: \"{transcription}\"")
            print("="*50 + "\n")
            
            # Add user message to memory
            self.memory_agent.add_message("user", transcription)
            
            # Run LangGraph workflow
            result = await self.graph.run(transcription)
            
            logger.info(f"Graph result: Intent={result['intent']}, Has followup={result['has_followup']}")
            
            # Handle based on workflow result
            if result['has_followup'] and result['followup_question']:
                # Ask followup question and continue loop
                response = result['followup_question']
                logger.info(f"Asking followup question: {response}")
                
                # Add to memory
                self.memory_agent.add_message("assistant", response, result['intent'])
                
                # Speak the followup question
                await self.audio_agent.text_to_speech(response)
                
                # Continue loop to listen for answer
                continue
                
            else:
                # No followup needed - provide final response
                response = result.get('final_response', 'I encountered an error processing your request.')
                
                logger.info(f"Final response: {response}")
                
                # Add to memory
                self.memory_agent.add_message("assistant", response, result['intent'])
                
                # Speak the response
                await self.audio_agent.text_to_speech(response)
                
                # End conversation and return to wake word detection
                logger.info(f"Conversation complete. Returning to wake word detection.")
                await self.audio_agent.resume_wake_word_detection()
                break  # Exit conversation loop
    
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
