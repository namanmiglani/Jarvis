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
    """Supported intents for user commands."""
    WEATHER = "weather"
    SMALL_TALK = "small_talk"
    GENERAL_QUESTION = "general_question"
    VISION = "vision"  # Describe camera surroundings
    SNAPSHOT_SAVE = "snapshot_save"  # Save camera snapshot
    SNAPSHOT_RETRIEVE = "snapshot_retrieve"  # Retrieve saved snapshot
    TRANSLATE = "translate"  # OCR and translate text from camera
    DISTANCE = "distance"  # Proximity search
    SELF_DESTRUCT = "self_destruct"  # Terminate system
    UNKNOWN = "unknown"


class IntentClassification(BaseModel):
    """Structured output for intent classification."""
    intent: Intent = Field(description="The classified intent")
    confidence: float = Field(description="Confidence score between 0 and 1", ge=0.0, le=1.0)
    entities: Dict[str, Any] = Field(default_factory=dict, description="Extracted entities")
    has_followup: bool = Field(description="Whether a followup question is needed to continue the conversation")
    followup_question: Optional[str] = Field(default=None, description="The followup question to ask, if has_followup is True")
    response: Optional[str] = Field(default=None, description="Direct response for small talk or general questions, if no followup needed")


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
                model="openai/gpt-oss-20b",  # Fast model optimized for structured tasks
                temperature=0.3,  # Lower temperature for consistent classification
                default_headers={
                    "HTTP-Referer": "https://github.com/jarvis-ai",
                    "X-Title": "Jarvis AI Assistant"
                }
            )
            logger.info("✅ LLM initialized with gpt oss 20b via OpenRouter")
        
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
            IntentClassification with intent, entities, and followup information
        """
        logger.info(f"Classifying intent for: {user_message}")
        
        try:
            llm = self._get_llm()
            
            # Build comprehensive system prompt
            system_prompt = """You are an AI assistant that classifies user intents and manages conversation flow.

**Supported Intents:**
- weather: Questions about weather conditions
- vision: Describe camera surroundings, "what do you see", "describe my surroundings"
- snapshot_save: Save a camera snapshot, "save a snapshot", "take a picture"
- snapshot_retrieve: Retrieve saved snapshot, "show my snapshot", "pull up my snapshot"
- translate: OCR and translate text, "translate this to Spanish", "what does this say in French"
- distance: Find distance/location, "how close is the nearest Starbucks", "where is the closest gym"
- self_destruct: Terminate system, "self destruct", "initiate self destruct sequence"
- general_question: General knowledge questions
- small_talk: Greetings, how are you, casual conversation
- unknown: Cannot determine intent

**Your Task:**
Analyze the user's message and return a structured JSON response with:

1. **intent**: The classified intent (one of the above)
2. **confidence**: Float between 0 and 1
3. **entities**: Dictionary of extracted entities (location, date, time, etc.)
4. **has_followup**: Boolean - TRUE if you need to ask a followup question to continue the conversation, FALSE if you can provide a final response
5. **followup_question**: String - The followup question to ask (ONLY if has_followup is TRUE)
6. **response**: String - Direct response for small talk or general questions (ONLY if has_followup is FALSE AND intent is small_talk or general_question)

**CRITICAL: The 'response' field should ONLY be populated for small_talk and general_question intents. For tool-based intents (weather, vision, snapshot_save, snapshot_retrieve), the response field must be null/empty as the tool will generate the response.**

**Followup Logic:**
- Set has_followup=TRUE when:
  * Missing required information (e.g., "What's the weather?" needs location)
  * Need clarification on ambiguous input
  * Tool-based intents (weather) that need more details
  
- Set has_followup=FALSE when:
  * Small talk (respond directly in 'response' field)
  * General questions (respond directly in 'response' field)
  * Have all required information for tool execution
  * User says goodbye/thank you (respond politely in 'response' field)
  * VISION requests - camera is always available, execute immediately
  * SNAPSHOT requests - camera is always available, execute immediately
  * TRANSLATE requests - camera is always available, execute immediately (extract target language from user message)
  * DISTANCE requests - execute immediately (extract query from user message)
  * **SELF_DESTRUCT requests** - execute immediately (no followup)

**Examples:**

User: "What's the weather?"
→ {
  "intent": "weather",
  "confidence": 1.0,
  "entities": {},
  "has_followup": true,
  "followup_question": "Which city or location would you like to know the weather for?",
  "response": null
}

User: "Weather in Boston"
→ {
  "intent": "weather",
  "confidence": 1.0,
  "entities": {"location": "Boston"},
  "has_followup": false,
  "followup_question": null,
  "response": null
}

User: "Hey Jarvis"
→ {
  "intent": "small_talk",
  "confidence": 1.0,
  "entities": {},
  "has_followup": false,
  "followup_question": null,
  "response": "Hello! How can I assist you today?"
}

User: "Translate this to Spanish"
→ {
  "intent": "translate",
  "confidence": 1.0,
  "entities": {"language": "es"},
  "has_followup": false,
  "followup_question": null,
  "response": null
}

User: "What does this say in French?"
→ {
  "intent": "translate",
  "confidence": 1.0,
  "entities": {"language": "fr"},
  "has_followup": false,
  "followup_question": null,
  "response": null
}

User: "How close is the nearest Starbucks?"
→ {
  "intent": "distance",
  "confidence": 1.0,
  "entities": {"query": "Starbucks"},
  "has_followup": false,
  "followup_question": null,
  "response": null
}

User: "How are you?"
→ {
  "intent": "small_talk",
  "confidence": 1.0,
  "entities": {},
  "has_followup": false,
  "followup_question": null,
  "response": "I'm functioning optimally, thank you for asking. How may I assist you today?"
}

User: "What is 2+2?"
→ {
  "intent": "general_question",
  "confidence": 1.0,
  "entities": {},
  "has_followup": false,
  "followup_question": null,
  "response": "2 plus 2 equals 4."
}

User: "Thank you"
→ {
  "intent": "small_talk",
  "confidence": 1.0,
  "entities": {},
  "has_followup": false,
  "followup_question": null,
  "response": "You're welcome. Is there anything else I can help you with?"
}

**CRITICAL:** Always set has_followup correctly to control conversation flow."""

            # Add conversation context if available
            if conversation_context:
                system_prompt += f"\n\n**Recent Conversation Context:**\n{conversation_context}"
            
            # Create messages
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Classify this message: {user_message}")
            ]
            
            # Get structured output
            structured_llm = llm.with_structured_output(IntentClassification)
            result = await structured_llm.ainvoke(messages)
            
            logger.info(f"Intent classified: {result.intent} (confidence: {result.confidence})")
            logger.info(f"Has followup: {result.has_followup}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error classifying intent: {e}")
            # Return unknown intent on error
            return IntentClassification(
                intent=Intent.UNKNOWN,
                confidence=0.0,
                entities={},
                has_followup=False,
                response="I encountered an error processing your request."
            )
