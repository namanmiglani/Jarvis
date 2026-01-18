"""
LangGraph Workflow

State-driven agent orchestration using LangGraph.
"""

import logging
from typing import TypedDict, List, Optional, Literal
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from agents.reasoning import Intent

logger = logging.getLogger(__name__)


class ConversationState(TypedDict):
    """State schema for conversation workflow."""
    # Messages
    messages: List[BaseMessage]
    user_input: str
    
    # Intent classification
    intent: Optional[str]
    confidence: float
    entities: dict
    has_followup: bool
    followup_question: Optional[str]
    
    # Tool execution
    tool_result: Optional[dict]
    
    # Response
    final_response: Optional[str]


class JarvisGraph:
    """LangGraph workflow for Jarvis agent orchestration."""
    
    def __init__(self, reasoning_agent, memory_agent, weather_tool, vision_tool=None, snapshot_tool=None, translation_tool=None):
        """Initialize graph with agents and tools."""
        self.reasoning_agent = reasoning_agent
        self.memory_agent = memory_agent
        self.weather_tool = weather_tool
        self.vision_tool = vision_tool
        self.snapshot_tool = snapshot_tool
        self.translation_tool = translation_tool
        
        # Build the graph
        self.workflow = self._build_graph()
        self.app = self.workflow.compile()
        
        logger.info("LangGraph workflow initialized")
    
    def _build_graph(self) -> StateGraph:
        """Build the conversation workflow graph."""
        workflow = StateGraph(ConversationState)
        
        # Add nodes
        workflow.add_node("classify_intent", self._classify_intent_node)
        workflow.add_node("execute_tool", self._execute_tool_node)
        workflow.add_node("generate_response", self._generate_response_node)
        
        # Set entry point
        workflow.set_entry_point("classify_intent")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "classify_intent",
            self._route_after_classification,
            {
                "followup": END,  # Ask followup question
                "tool": "execute_tool",  # Execute tool
                "response": "generate_response"  # Generate direct response
            }
        )
        
        workflow.add_edge("execute_tool", "generate_response")
        workflow.add_edge("generate_response", END)
        
        return workflow
    
    async def _classify_intent_node(self, state: ConversationState) -> ConversationState:
        """Node: Classify user intent and extract entities."""
        user_input = state["user_input"]
        
        # Get conversation context
        context = self.memory_agent.get_conversation_context()
        
        # Classify intent
        classification = await self.reasoning_agent.classify_intent(
            user_input,
            conversation_context=context
        )
        
        # Update state
        state["intent"] = classification.intent.value
        state["confidence"] = classification.confidence
        state["entities"] = classification.entities
        state["has_followup"] = classification.has_followup
        state["followup_question"] = classification.followup_question
        
        # If has direct response (small talk, general question)
        if classification.response:
            state["final_response"] = classification.response
        
        logger.info(f"Intent: {classification.intent}, Has followup: {classification.has_followup}")
        return state
    
    async def _execute_tool_node(self, state: ConversationState) -> ConversationState:
        """Node: Execute appropriate tool based on intent."""
        intent = state["intent"]
        entities = state["entities"]
        
        if intent == "weather":
            location = entities.get('location', '')
            if location:
                logger.info(f"Executing weather tool for: {location}")
                weather_data = await self.weather_tool.get_weather(location)
                state["tool_result"] = weather_data
            else:
                state["tool_result"] = {
                    'success': False,
                    'error': 'No location provided'
                }
        
        elif intent == "vision":
            if self.vision_tool:
                logger.info("Executing vision tool")
                vision_data = await self.vision_tool.describe_surroundings()
                state["tool_result"] = vision_data
            else:
                state["tool_result"] = {
                    'success': False,
                    'error': 'Vision tool not available'
                }
        
        elif intent == "snapshot_save":
            if self.snapshot_tool:
                logger.info("Executing snapshot save tool")
                snapshot_data = await self.snapshot_tool.save_snapshot()
                state["tool_result"] = snapshot_data
            else:
                state["tool_result"] = {
                    'success': False,
                    'error': 'Snapshot tool not available'
                }
        
        elif intent == "snapshot_retrieve":
            if self.snapshot_tool:
                logger.info("Executing snapshot retrieve tool")
                snapshot_data = await self.snapshot_tool.get_latest_snapshot()
                state["tool_result"] = snapshot_data
            else:
                state["tool_result"] = {
                    'success': False,
                    'error': 'Snapshot tool not available'
                }
        
        elif intent == "translate":
            if self.translation_tool:
                logger.info("Executing translation tool")
                # Extract target language from entities
                entities = state.get("entities", {})
                target_lang = entities.get("language", "en")  # Default to English
                
                translation_data = await self.translation_tool.translate_from_camera(target_lang)
                state["tool_result"] = translation_data
            else:
                state["tool_result"] = {
                    'success': False,
                    'error': 'Translation tool not available'
                }
        
        else:
            # Other tools
            state["tool_result"] = {
                'success': False,
                'error': f'Tool for {intent} not yet implemented'
            }
        
        return state
    
    async def _generate_response_node(self, state: ConversationState) -> ConversationState:
        """Node: Generate final response from tool result or direct response."""
        # If already have final response (from small talk/general question)
        if state.get("final_response"):
            return state
        
        # Format tool result
        tool_result = state.get("tool_result")
        if tool_result:
            if state["intent"] == "weather":
                response = self.weather_tool.format_weather_response(tool_result)
            elif state["intent"] == "vision":
                response = self.vision_tool.format_vision_response(tool_result)
            elif state["intent"] == "snapshot_save":
                response = self.snapshot_tool.format_save_response(tool_result)
            elif state["intent"] == "snapshot_retrieve":
                response = self.snapshot_tool.format_retrieve_response(tool_result)
            elif state["intent"] == "translate":
                response = self.translation_tool.format_translation_response(tool_result)
            else:
                response = tool_result.get('error', 'Unable to process request')
            
            state["final_response"] = response
        else:
            state["final_response"] = "I encountered an error processing your request."
        
        return state
    
    def _route_after_classification(self, state: ConversationState) -> Literal["followup", "tool", "response"]:
        """Determine next step after intent classification."""
        # If needs followup question
        if state["has_followup"] and state["followup_question"]:
            return "followup"
        
        # If has direct response (small talk, general question)
        if state.get("final_response"):
            return "response"
        
        # Otherwise execute tool
        return "tool"
    
    async def run(self, user_input: str) -> dict:
        """
        Run the workflow with user input.
        
        Args:
            user_input: User's message
            
        Returns:
            Final state with response
        """
        initial_state = ConversationState(
            messages=[],
            user_input=user_input,
            intent=None,
            confidence=0.0,
            entities={},
            has_followup=False,
            followup_question=None,
            tool_result=None,
            final_response=None
        )
        
        result = await self.app.ainvoke(initial_state)
        return result
