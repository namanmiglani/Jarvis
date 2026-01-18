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
        logger.info("Orchestrator Agent initialized")
    
    async def start(self):
        """Start the orchestrator and all sub-agents."""
        logger.info("🚀 Starting Orchestrator Agent...")
        self.is_active = True
        
        # Initialize agents
        from agents.audio import AudioAgent
        from agents.reasoning import ReasoningAgent, Intent
        from agents.memory import MemoryAgent
        from agents.tools import WeatherTool
        
        self.reasoning_agent = ReasoningAgent()
        self.memory_agent = MemoryAgent()
        self.weather_tool = WeatherTool()
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
                # Resume wake word detection before exiting
                await self.audio_agent.resume_wake_word_detection()
                break  # Exit conversation loop
            
            print("\n" + "="*50)
            print(f"📝 You said: \"{transcription}\"")
            print("="*50 + "\n")
            
            # Add user message to memory
            self.memory_agent.add_message("user", transcription)
            
            # Get conversation context
            context = self.memory_agent.get_conversation_context()
            
            # Classify intent
            from agents.reasoning import Intent
            classification = await self.reasoning_agent.classify_intent(
                transcription,
                conversation_context=context
            )
            
            logger.info(f"Intent: {classification.intent}, Confidence: {classification.confidence}")
            logger.info(f"Entities: {classification.entities}")
            logger.info(f"Has followup: {classification.has_followup}")
            
            # Handle based on has_followup flag
            if classification.has_followup and classification.followup_question:
                # Ask followup question and continue loop
                response = classification.followup_question
                logger.info(f"Asking followup question: {response}")
                
                # Add to memory
                self.memory_agent.add_message("assistant", response, classification.intent.value)
                
                # Speak the followup question
                await self.audio_agent.text_to_speech(response)
                
                # Continue loop to listen for answer
                continue
                
            else:
                # No followup needed - provide final response
                if classification.response:
                    # Use LLM-generated response (for small talk, general questions)
                    response = classification.response
                elif classification.intent.value == "weather":
                    # Execute weather tool
                    location = classification.entities.get('location', '')
                    if location:
                        logger.info(f"Executing weather tool for: {location}")
                        weather_data = await self.weather_tool.get_weather(location)
                        response = self.weather_tool.format_weather_response(weather_data)
                    else:
                        response = "I need a location to check the weather."
                else:
                    # Tool-based intent with all required info (calendar, translation, etc.)
                    response = f"Understood. I'll help you with that {classification.intent.value} request."
                    # TODO Phase 5: Add calendar and translation tools
                
                logger.info(f"Final response: {response}")
                
                # Add to memory
                self.memory_agent.add_message("assistant", response, classification.intent.value)
                
                # Speak the response
                await self.audio_agent.text_to_speech(response)
                
                # End conversation and return to wake word detection
                logger.info(f"Conversation complete. Returning to wake word detection.")
                await asyncio.sleep(5)  # Prevent immediate re-trigger
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
