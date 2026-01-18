"""
Memory Agent

Manages conversation history and context for multi-turn conversations.
Stores messages in-memory (no database persistence for MVP).
"""

import logging
from datetime import datetime
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)


class MemoryAgent:
    """Manages conversation history and context."""
    
    def __init__(self, max_messages: int = 50):
        """
        Initialize Memory Agent.
        
        Args:
            max_messages: Maximum number of messages to store
        """
        self.max_messages = max_messages
        self.conversation_history: List[Tuple[datetime, str, str, Optional[str]]] = []
        logger.info("Memory Agent initialized")
    
    def add_message(self, role: str, message: str, intent: Optional[str] = None):
        """
        Add a message to conversation history.
        
        Args:
            role: 'user' or 'assistant'
            message: The message content
            intent: Optional intent classification
        """
        timestamp = datetime.now()
        self.conversation_history.append((timestamp, role, message, intent))
        
        # Keep only last max_messages
        if len(self.conversation_history) > self.max_messages:
            self.conversation_history = self.conversation_history[-self.max_messages:]
        
        logger.info(f"Added {role} message to history (intent: {intent})")
    
    def get_recent_messages(self, n: int = 5) -> List[Dict[str, str]]:
        """
        Get the N most recent messages.
        
        Args:
            n: Number of recent messages to retrieve
            
        Returns:
            List of message dictionaries with role and content
        """
        recent = self.conversation_history[-n:] if self.conversation_history else []
        return [
            {"role": role, "content": message}
            for _, role, message, _ in recent
        ]
    
    def get_conversation_context(self) -> str:
        """
        Get formatted conversation context for LLM.
        
        Returns:
            Formatted string of recent conversation
        """
        if not self.conversation_history:
            return "No previous conversation."
        
        context_parts = []
        for timestamp, role, message, intent in self.conversation_history[-5:]:
            time_str = timestamp.strftime("%H:%M:%S")
            intent_str = f" [{intent}]" if intent else ""
            context_parts.append(f"[{time_str}] {role.upper()}{intent_str}: {message}")
        
        return "\n".join(context_parts)
    
    def clear_history(self):
        """Clear all conversation history."""
        self.conversation_history = []
        logger.info("Conversation history cleared")
    
    def get_last_user_message(self) -> Optional[str]:
        """Get the last message from the user."""
        for _, role, message, _ in reversed(self.conversation_history):
            if role == "user":
                return message
        return None
