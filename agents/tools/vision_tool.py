"""
Vision Tool - Describe camera surroundings using multimodal LLM

Uses Gemini 2.0 Flash via OpenRouter for vision capabilities.
"""

import cv2
import base64
import logging
import os
from typing import Dict

logger = logging.getLogger(__name__)


class VisionTool:
    """Tool for describing camera surroundings using vision AI."""
    
    def __init__(self):
        self.camera_manager = None  # Will be set by orchestrator
        self.llm = None
        logger.info("Vision Tool initialized")
    
    async def describe_surroundings(self) -> Dict:
        """
        Capture camera frame and describe surroundings using multimodal LLM.
        
        Returns:
            Dictionary with success status and description
        """
        try:
            from agents.camera_manager import CameraManager
            
            # Get camera frame
            if self.camera_manager is None:
                self.camera_manager = CameraManager()
            
            frame = self.camera_manager.get_frame()
            
            if frame is None:
                return {
                    "success": False,
                    "error": "Could not capture camera frame"
                }
            
            # Encode frame to base64
            _, buffer = cv2.imencode('.jpg', frame)
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Call multimodal LLM
            description = await self._call_vision_llm(image_base64)
            
            logger.info(f"Vision description: {description[:100]}...")
            
            return {
                "success": True,
                "description": description,
                "image_base64": image_base64  # For potential display
            }
            
        except Exception as e:
            logger.error(f"Error in vision tool: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _call_vision_llm(self, image_base64: str) -> str:
        """Call OpenRouter with vision model."""
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage
            import asyncio
            
            # Initialize LLM if not already done
            if self.llm is None:
                api_key = os.getenv('OPENROUTER_API_KEY')
                if not api_key:
                    raise ValueError("OPENROUTER_API_KEY not found")
                
                self.llm = ChatOpenAI(
                    model="qwen/qwen3-vl-32b-instruct",  # Fast, reliable vision model
                    api_key=api_key,
                    base_url="https://openrouter.ai/api/v1",
                    temperature=0.7,
                    timeout=30,  # 30 second timeout
                    default_headers={
                        "HTTP-Referer": "https://github.com/jarvis-ai",
                        "X-Title": "Jarvis AI Assistant"
                    }
                )
                logger.info("✅ Vision LLM initialized (Gemini Flash 1.5)")
            
            # Create message with image
            message = HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": "Describe what you see in this image in detail. Include objects, people, setting, colors, and any notable features. Be concise but thorough."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            )
            
            # Get response with timeout
            logger.info("Calling vision LLM...")
            response = await asyncio.wait_for(
                self.llm.ainvoke([message]),
                timeout=30.0
            )
            logger.info("✅ Vision LLM response received")
            return response.content
            
        except asyncio.TimeoutError:
            logger.error("Vision LLM timed out after 30 seconds")
            raise Exception("Vision analysis timed out. Please try again.")
        except Exception as e:
            logger.error(f"Error calling vision LLM: {e}")
            raise
    
    def format_vision_response(self, result: Dict) -> str:
        """Format vision result into natural language response."""
        if not result.get('success'):
            return f"I'm sorry, I couldn't analyze the camera view. {result.get('error', '')}"
        
        description = result.get('description', 'No description available')
        return f"I can see: {description}"
