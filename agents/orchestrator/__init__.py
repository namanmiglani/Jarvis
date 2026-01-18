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
        self.hud_server = None  # HUD WebSocket server
        logger.info("Orchestrator Agent initialized")
    
    async def start(self):
        """Start the orchestrator and all sub-agents."""
        logger.info("🚀 Starting Orchestrator Agent...")
        self.is_active = True
        
        # Initialize agents and tools
        from agents.audio import AudioAgent
        from agents.reasoning import ReasoningAgent, Intent
        from agents.memory import MemoryAgent
        from agents.tools import WeatherTool, VisionTool, SnapshotTool, TranslationTool, MapsTool
        from agents.graph import JarvisGraph
        from agents.hud_server import HUDServer
        from agents.camera_manager import CameraManager
        
        self.reasoning_agent = ReasoningAgent()
        self.memory_agent = MemoryAgent()
        self.weather_tool = WeatherTool()
        self.vision_tool = VisionTool()
        self.snapshot_tool = SnapshotTool()
        self.translation_tool = TranslationTool()
        self.maps_tool = MapsTool()
        
        # Initialize camera manager
        self.camera_manager = CameraManager()
        self.camera_manager.start()
        self.vision_tool.camera_manager = self.camera_manager
        self.snapshot_tool.camera_manager = self.camera_manager
        self.translation_tool.camera_manager = self.camera_manager
        
        # Initialize LangGraph workflow
        self.graph = JarvisGraph(
            reasoning_agent=self.reasoning_agent,
            memory_agent=self.memory_agent,
            weather_tool=self.weather_tool,
            vision_tool=self.vision_tool,
            snapshot_tool=self.snapshot_tool,
            translation_tool=self.translation_tool,
            maps_tool=self.maps_tool
        )
        
        # Initialize HUD server
        self.hud_server = HUDServer()
        await self.hud_server.start()
        
        self.audio_agent = AudioAgent(on_wake_word_detected=self.on_wake_word_detected)
        
        # Start wake word detection
        logger.info("Starting wake word detection...")
        await self.audio_agent.start_wake_word_detection()
    
    async def on_wake_word_detected(self):
        """Callback when wake word 'Hey Jarvis' is detected."""
        logger.info("🎯 Wake word callback triggered!")
        
        # Broadcast wake word detection to HUD
        await self.hud_server.send_state("wake_word")
        
        # Pause wake word detection during conversation
        self.audio_agent.pause_wake_word_detection()
        
        # Greet the user
        await self.hud_server.send_state("speaking", {"text": "Hi, how can I assist you?"})
        await self.audio_agent.text_to_speech_elevenlabs("Hi, how can I assist you?")
        
        # Multi-turn conversation loop
        max_turns = 10  # Prevent infinite loops
        for turn in range(max_turns):
            # Broadcast listening state
            await self.hud_server.send_state("listening")
            
            # Get user's speech command
            transcription = await self.audio_agent.speech_to_text()
            
            if not transcription:
                print("\n⚠️  No speech detected or transcription failed\n")
                await self.audio_agent.text_to_speech_elevenlabs("I didn't catch that. Please try again.")
                logger.warning("No transcription received")
                break  # Exit conversation loop
            
            print("\n" + "="*50)
            print(f"📝 You said: \"{transcription}\"")
            print("="*50 + "\n")
            
            # Send transcription to HUD
            await self.hud_server.send_transcription(transcription)
            
            # Add user message to memory
            self.memory_agent.add_message("user", transcription)
            
            # Broadcast thinking state
            await self.hud_server.send_state("thinking")
            
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
                
                # Broadcast speaking state and response
                await self.hud_server.send_state("speaking", {"text": response})
                await self.hud_server.send_response(response)
                
                # Speak the followup question
                await self.audio_agent.text_to_speech_elevenlabs(response)
                
                # Continue loop to listen for answer
                continue
                
            else:
                # No followup needed - provide final response
                response = result.get('final_response', 'I encountered an error processing your request.')
                
                logger.info(f"Final response: {response}")
                
                # Send weather data to HUD if available
                if result.get('intent') == 'weather' and result.get('tool_result'):
                    if result['tool_result'].get('success'):
                        await self.hud_server.send_weather(result['tool_result'])
                
                # Send snapshot data to HUD if available
                if result.get('intent') == 'snapshot_retrieve' and result.get('tool_result'):
                    if result['tool_result'].get('success'):
                        # Remove numpy array before sending (not JSON serializable)
                        snapshot_data = {
                            'filepath': result['tool_result'].get('filepath'),
                            'filename': result['tool_result'].get('filename'),
                            'success': True
                        }
                        await self.hud_server.send_snapshot(snapshot_data)
                
                # Add to memory
                self.memory_agent.add_message("assistant", response, result['intent'])
                
                # Broadcast speaking state and response
                await self.hud_server.send_state("speaking", {"text": response})
                await self.hud_server.send_response(response)
                
                # Speak the response
                await self.audio_agent.text_to_speech_elevenlabs(response)
                
                # End conversation and return to wake word detection
                logger.info(f"Conversation complete. Returning to wake word detection.")
                await self.hud_server.send_state("idle")
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
