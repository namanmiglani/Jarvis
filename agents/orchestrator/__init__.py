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
        logger.info("Orchestrator Agent initialized")
    
    async def start(self):
        """Start the orchestrator and all sub-agents."""
        logger.info("🚀 Starting Orchestrator Agent...")
        self.is_active = True
        
        # Initialize agents
        from agents.audio import AudioAgent
        from agents.reasoning import ReasoningAgent, Intent
        from agents.memory import MemoryAgent
        
        self.reasoning_agent = ReasoningAgent()
        self.memory_agent = MemoryAgent()
        self.audio_agent = AudioAgent(on_wake_word_detected=self.on_wake_word_detected)
        
        # Start wake word detection
        logger.info("Starting wake word detection...")
        await self.audio_agent.start_wake_word_detection()
    
    async def on_wake_word_detected(self):
        """Callback when wake word 'Hey Jarvis' is detected."""
        logger.info("🎯 Wake word callback triggered!")
        
        # Multi-turn conversation loop
        max_turns = 5  # Prevent infinite loops
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
            
            # Handle clarifying questions
            if classification.needs_clarification and classification.clarifying_question:
                response = classification.clarifying_question
                logger.info(f"Asking clarifying question: {response}")
                
                # Add to memory
                self.memory_agent.add_message("assistant", response, classification.intent.value)
                
                # Speak the clarifying question
                await self.audio_agent.text_to_speech(response)
                
                # Continue loop to listen for answer
                continue
                
            else:
                # Generate response based on intent
                if classification.intent == Intent.SMALL_TALK:
                    response = await self.reasoning_agent.generate_response(
                        classification.intent,
                        classification.entities,
                        transcription
                    )
                    # Don't end conversation after small talk - ask if they need anything else
                    should_continue = True
                elif classification.intent == Intent.GENERAL_QUESTION:
                    response = await self.reasoning_agent.generate_response(
                        classification.intent,
                        classification.entities,
                        transcription
                    )
                    should_continue = False  # End after answering question
                else:
                    # For tool-based intents (weather, calendar, translation)
                    response = f"Understood. I'll help you with that {classification.intent.value} request."
                    # TODO Phase 4: Call appropriate tool executor
                    should_continue = False  # End after acknowledging
                
                logger.info(f"Response: {response}")
                
                # Add to memory
                self.memory_agent.add_message("assistant", response, classification.intent.value)
                
                # Speak the response
                await self.audio_agent.text_to_speech(response)
                
                # Check if we should continue or end
                if should_continue and turn < max_turns - 1:
                    # For small talk, continue listening
                    logger.info("Continuing conversation after small talk...")
                    continue
                else:
                    # End conversation after providing answer
                    logger.info(f"Transcription received: {transcription}")
                    # Add delay to prevent wake word re-trigger
                    await asyncio.sleep(2)
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
