"""
Memory Agent

Maintains conversation context and user preferences.
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class MemoryAgent:
    """Manages conversation history and user preferences."""
    
    def __init__(self):
        self.conversation_history: List[Dict[str, str]] = []
        self.current_intent = None
        self.pending_entities: Dict[str, Any] = {}
        self.user_preferences = {
            "default_language": "en",
            "location": "San Francisco, CA",
            "calendar_id": "primary"
        }
        logger.info("Memory Agent initialized")
    
    def add_message(self, role: str, content: str):
        """Add a message to conversation history."""
        self.conversation_history.append({"role": role, "content": content})
        
        # Keep only last 10 exchanges
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
    
    def get_context(self) -> List[Dict[str, str]]:
        """Get recent conversation context."""
        return self.conversation_history
    
    def set_pending_intent(self, intent: str, entities: Dict[str, Any]):
        """Store pending intent and partial entities."""
        self.current_intent = intent
        self.pending_entities = entities
        logger.info(f"Stored pending intent: {intent}")
    
    def update_entity(self, entity_name: str, value: Any):
        """Update a pending entity."""
        self.pending_entities[entity_name] = value
        logger.info(f"Updated entity {entity_name}: {value}")
    
    def clear_session(self):
        """Clear current session data."""
        self.conversation_history = []
        self.current_intent = None
        self.pending_entities = {}
        logger.info("Session cleared")
