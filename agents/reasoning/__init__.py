"""
Reasoning Agent

Handles intent classification, entity extraction, and decision-making using LangChain and Gemini.
Uses OpenRouter to access Gemini 2.0 Flash for cost-effective LLM inference.
"""

import logging
import os
from typing import Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


class Intent(str, Enum):
    """Supported intent types."""
    WEATHER = "weather"
    CALENDAR = "calendar"
    TRANSLATION = "translation"
    GENERAL_QUESTION = "general_question"
    SMALL_TALK = "small_talk"
    UNKNOWN = "unknown"


class IntentClassification(BaseModel):
    """Structured output for intent classification."""
    intent: Intent = Field(description="The classified intent")
    confidence: float = Field(description="Confidence score between 0 and 1", ge=0.0, le=1.0)
    entities: Dict[str, Any] = Field(default_factory=dict, description="Extracted entities")
    needs_clarification: bool = Field(description="Whether clarifying questions are needed")
    clarifying_question: Optional[str] = Field(default=None, description="Question to ask for clarification")


class ReasoningAgent:
    """Handles intent classification and reasoning using LangChain."""
    
    def __init__(self):
        """Initialize Reasoning Agent with LangChain and Gemini."""
        self.llm = None
        logger.info("Reasoning Agent initialized")
    
    def _get_llm(self) -> ChatOpenAI:
        """
        Get or create LLM instance.
        
        Returns:
            ChatOpenAI instance configured for OpenRouter/Gemini
        """
        if self.llm is None:
            api_key = os.getenv('OPENROUTER_API_KEY')
            if not api_key:
                raise ValueError("OPENROUTER_API_KEY not found in environment variables")
            
            self.llm = ChatOpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
                model="meta-llama/llama-4-maverick",  # Free tier for testing
                temperature=0.3,  # Lower temperature for consistent classification
                default_headers={
                    "HTTP-Referer": "https://github.com/jarvis-ai",
                    "X-Title": "Jarvis AI Assistant"
                }
            )
            logger.info("✅ LLM initialized with Gemini 2.0 Flash via OpenRouter")
        
        return self.llm
    
    async def classify_intent(
        self,
        user_message: str,
        conversation_context: Optional[str] = None
    ) -> IntentClassification:
        """
        Classify user intent and extract entities.
        
        Args:
            user_message: The user's message to classify
            conversation_context: Optional conversation history for context
            
        Returns:
            IntentClassification with intent, entities, and clarification needs
        """
        logger.info(f"Classifying intent for: {user_message}")
        
        try:
            llm = self._get_llm()
            
            # Build system prompt
            system_prompt = """You are an AI assistant that classifies user intents and extracts entities.

Supported intents:
- weather: Questions about weather conditions
- calendar: Scheduling, events, reminders
- translation: Translate text or speech
- general_question: General knowledge questions
- small_talk: Greetings, how are you, casual conversation
- unknown: Cannot determine intent

For each message:
1. Classify the intent
2. Extract relevant entities (location, date, time, etc.)
3. Determine if you need more information
4. If clarification needed, generate a natural question

Examples:
- "What's the weather?" → intent=weather, needs_clarification=True, question="Which city?"
- "Weather in Vancouver" → intent=weather, entities={location: "Vancouver"}
- "Schedule a meeting tomorrow at 2pm" → intent=calendar, entities={date: "tomorrow", time: "2pm"}
- "How are you?" → intent=small_talk

Respond with structured JSON."""

            # Add conversation context if available
            if conversation_context:
                system_prompt += f"\n\nRecent conversation:\n{conversation_context}"
            
            # Create messages
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Classify this message: {user_message}")
            ]
            
            # Get structured output
            structured_llm = llm.with_structured_output(IntentClassification)
            result = await structured_llm.ainvoke(messages)
            
            logger.info(f"Intent classified: {result.intent} (confidence: {result.confidence})")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error classifying intent: {e}")
            # Return unknown intent on error
            return IntentClassification(
                intent=Intent.UNKNOWN,
                confidence=0.0,
                entities={},
                needs_clarification=False
            )
    
    async def generate_response(
        self,
        intent: Intent,
        entities: Dict[str, Any],
        conversation_context: Optional[str] = None
    ) -> str:
        """
        Generate a response based on intent and entities.
        
        Args:
            intent: The classified intent
            entities: Extracted entities
            conversation_context: Optional conversation history
            
        Returns:
            Generated response text
        """
        logger.info(f"Generating response for intent: {intent}")
        
        try:
            llm = self._get_llm()
            
            # Build prompt based on intent
            if intent == Intent.SMALL_TALK:
                prompt = f"Respond naturally to this greeting or small talk: {conversation_context}"
            elif intent == Intent.GENERAL_QUESTION:
                prompt = f"Answer this question concisely: {conversation_context}"
            else:
                # For tool-based intents, acknowledge and indicate processing
                return f"I'll help you with that {intent.value} request."
            
            messages = [
                SystemMessage(content="You are Jarvis, a sophisticated AI assistant. Be concise and professional."),
                HumanMessage(content=prompt)
            ]
            
            response = await llm.ainvoke(messages)
            return response.content
            
        except Exception as e:
            logger.error(f"❌ Error generating response: {e}")
            return "I encountered an error processing your request."
