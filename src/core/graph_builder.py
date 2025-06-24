"""
LangGraph workflow builder for Contact Center Agentic Flow System
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode

from src.models.state import AgentState, TicketStatus, Sentiment, Priority, CustomerTier
from src.core.workflow_nodes import WorkflowNodes
from src.core.logging import get_logger

logger = get_logger(__name__)


class ConversationGraphBuilder:
    """Builder class for creating the conversation flow graph"""
    
    def __init__(self, agents: Dict[str, Any], tool_registry: Any):
        self.agents = agents
        self.tool_registry = tool_registry
        self.workflow_nodes = WorkflowNodes(agents, tool_registry)
    
    def build_conversation_graph(self) -> StateGraph:
        """Build the main conversation flow graph using LangGraph"""
        logger.info("Building conversation flow graph...")
        
        # Create the StateGraph with AgentState as the state type
        workflow = StateGraph(AgentState)
        
        # Add all nodes to the workflow
        self._add_nodes(workflow)
        
        # Add edges to define the conversation flow
        self._add_edges(workflow)
        
        logger.info("Conversation flow graph built successfully")
        return workflow
    
    def _add_nodes(self, workflow: StateGraph):
        """Add all workflow nodes to the graph"""
        logger.info("Adding workflow nodes...")
        
        # Entry and classification nodes
        workflow.add_node("customer_entry", self.workflow_nodes.customer_entry_node)
        workflow.add_node("intent_classification", self.workflow_nodes.intent_classification_node)
        workflow.add_node("smart_routing", self.workflow_nodes.smart_routing_node)
        
        # Agent interaction nodes
        workflow.add_node("tier1_support", self._create_agent_node("tier1_support"))
        workflow.add_node("tier2_technical", self._create_agent_node("tier2_technical"))
        workflow.add_node("tier3_expert", self._create_agent_node("tier3_expert"))
        workflow.add_node("sales", self._create_agent_node("sales"))
        workflow.add_node("billing", self._create_agent_node("billing"))
        workflow.add_node("supervisor", self._create_agent_node("supervisor"))
        
        # Process management nodes
        workflow.add_node("escalation_handler", self.workflow_nodes.escalation_handler_node)
        workflow.add_node("quality_check", self.workflow_nodes.quality_check_node)
        workflow.add_node("human_handoff", self.workflow_nodes.human_handoff_node)
        
        # Utility nodes
        workflow.add_node("clarification_needed", self._create_clarification_node())
        workflow.add_node("conversation_timeout", self._create_timeout_node())
        workflow.add_node("error_handler", self._create_error_handler_node())
        
        logger.info("All workflow nodes added successfully")
    
    def _add_edges(self, workflow: StateGraph):
        """Add edges to define the conversation flow"""
        logger.info("Adding workflow edges...")
        
        # Entry flow
        workflow.add_edge(START, "customer_entry")
        workflow.add_edge("customer_entry", "intent_classification")
        
        # Intent classification flow
        workflow.add_conditional_edges(
            "intent_classification",
            self._intent_classification_router,
            {
                "route_to_agent": "smart_routing",
                "clarification_needed": "clarification_needed",
                "escalate_immediately": "supervisor",
                "error": "error_handler"
            }
        )
        
        # Clarification flow
        workflow.add_conditional_edges(
            "clarification_needed",
            self._clarification_router,
            {
                "retry_classification": "intent_classification",
                "escalate": "supervisor",
                "timeout": "conversation_timeout"
            }
        )
        
        # Smart routing flow
        workflow.add_conditional_edges(
            "smart_routing",
            self._smart_routing_router,
            {
                "tier1_support": "tier1_support",
                "tier2_technical": "tier2_technical",
                "tier3_expert": "tier3_expert",
                "sales": "sales",
                "billing": "billing",
                "supervisor": "supervisor"
            }
        )
        
        # Agent interaction flows
        for agent_name in ["tier1_support", "tier2_technical", "tier3_expert", "sales", "billing"]:
            workflow.add_conditional_edges(
                agent_name,
                self._agent_interaction_router,
                {
                    "resolved": "quality_check",
                    "escalate": "escalation_handler",
                    "continue": agent_name,
                    "transfer": "smart_routing",
                    "human_required": "human_handoff",
                    "error": "error_handler"
                }
            )
        
        # Supervisor flow
        workflow.add_conditional_edges(
            "supervisor",
            self._supervisor_router,
            {
                "assign_agent": "smart_routing",
                "human_required": "human_handoff",
                "resolved": "quality_check",
                "escalate": "escalation_handler",
                "error": "error_handler"
            }
        )
        
        # Escalation handler flow
        workflow.add_conditional_edges(
            "escalation_handler",
            self._escalation_router,
            {
                "escalate_to_supervisor": "supervisor",
                "escalate_to_human": "human_handoff",
                "retry_with_agent": "smart_routing",
                "error": "error_handler"
            }
        )
        
        # Quality check flow
        workflow.add_conditional_edges(
            "quality_check",
            self._quality_check_router,
            {
                "approved": END,
                "needs_followup": "smart_routing",
                "escalate": "supervisor",
                "error": "error_handler"
            }
        )
        
        # Terminal nodes
        workflow.add_edge("human_handoff", END)
        workflow.add_edge("conversation_timeout", END)
        workflow.add_edge("error_handler", END)
        
        logger.info("All workflow edges added successfully")
    
    def _create_agent_node(self, agent_type: str) -> Callable:
        """Create a node function for a specific agent type"""
        async def agent_node(state: AgentState) -> AgentState:
            return await self.workflow_nodes.agent_interaction_node(state, agent_type)
        
        return agent_node
    
    def _create_clarification_node(self) -> Callable:
        """Create clarification node for unclear intents"""
        async def clarification_node(state: AgentState) -> AgentState:
            logger.info(f"Requesting clarification for conversation {state.conversation_id}")
            
            # Add clarification request to conversation
            clarification_message = await self._generate_clarification_message(state)
            
            state.conversation_history.append({
                "timestamp": datetime.now(),
                "speaker": "agent",
                "message": clarification_message,
                "intent": "clarification_request",
                "confidence": None,
                "agent_type": "clarification_agent"
            })
            
            # Reset intent confidence to trigger re-classification
            state.intent_confidence = 0.0
            
            return state
        
        return clarification_node
    
    def _create_timeout_node(self) -> Callable:
        """Create timeout node for conversation timeouts"""
        async def timeout_node(state: AgentState) -> AgentState:
            logger.info(f"Conversation timeout for {state.conversation_id}")
            
            state.status = TicketStatus.CLOSED
            state.conversation_history.append({
                "timestamp": datetime.now(),
                "speaker": "system",
                "message": "Conversation timed out due to inactivity",
                "intent": "timeout",
                "confidence": None,
                "agent_type": "timeout_handler"
            })
            
            return state
        
        return timeout_node
    
    def _create_error_handler_node(self) -> Callable:
        """Create error handler node for system errors"""
        async def error_handler_node(state: AgentState) -> AgentState:
            logger.error(f"Error handling for conversation {state.conversation_id}")
            
            state.status = TicketStatus.ESCALATED
            state.requires_human = True
            
            error_message = "I apologize, but I'm experiencing technical difficulties. Let me transfer you to a human agent who can assist you better."
            
            state.conversation_history.append({
                "timestamp": datetime.now(),
                "speaker": "agent",
                "message": error_message,
                "intent": "error_handling",
                "confidence": None,
                "agent_type": "error_handler"
            })
            
            return state
        
        return error_handler_node
    
    # Router functions for conditional edges
    def _intent_classification_router(self, state: AgentState) -> str:
        """Route based on intent classification results"""
        try:
            # Check for errors first
            if state.error_log and any(error.get("node") == "intent_classification" for error in state.error_log):
                return "error"
            
            # Check confidence levels
            if state.intent_confidence >= 0.85:
                return "route_to_agent"
            elif state.intent_confidence >= 0.5:
                return "clarification_needed"
            elif state.current_intent in ["complaint", "escalation", "emergency"]:
                return "escalate_immediately"
            else:
                return "clarification_needed"
                
        except Exception as e:
            logger.error(f"Intent classification routing error: {e}")
            return "error"
    
    def _clarification_router(self, state: AgentState) -> str:
        """Route based on clarification attempts"""
        try:
            # Count clarification attempts
            clarification_attempts = len([
                h for h in state.conversation_history 
                if h.get("agent_type") == "clarification_agent"
            ])
            
            # Check timeout
            if state.session_start:
                duration = (datetime.now() - state.session_start).total_seconds()
                if duration > state.timeout_minutes * 60:
                    return "timeout"
            
            # Limit clarification attempts
            if clarification_attempts >= 2:
                return "escalate"
            
            # Check if new intent was provided
            if state.intent_confidence > 0.5:
                return "retry_classification"
            
            return "escalate"
            
        except Exception as e:
            logger.error(f"Clarification routing error: {e}")
            return "escalate"
    
    def _smart_routing_router(self, state: AgentState) -> str:
        """Route to appropriate agent based on smart routing logic"""
        try:
            # Use the current agent type determined by smart routing
            return state.current_agent_type
            
        except Exception as e:
            logger.error(f"Smart routing error: {e}")
            return "tier1_support"  # Default fallback
    
    def _agent_interaction_router(self, state: AgentState) -> str:
        """Route based on agent interaction results"""
        try:
            # Check for errors first
            if state.error_log and any(
                error.get("node") == "agent_interaction" and 
                error.get("timestamp", "") > (datetime.now() - datetime.timedelta(minutes=1)).isoformat()
                for error in state.error_log
            ):
                return "error"
            
            # Check if human is explicitly required
            if state.requires_human:
                return "human_required"
            
            # Check resolution status
            if state.status == TicketStatus.RESOLVED:
                return "resolved"
            
            # Check escalation conditions
            if state.should_escalate or self._should_escalate_agent_interaction(state):
                return "escalate"
            
            # Check if agent transfer is needed
            if self._needs_agent_transfer(state):
                return "transfer"
            
            # Continue with same agent if conditions allow
            if self._can_continue_with_agent(state):
                return "continue"
            
            # Default to escalation
            return "escalate"
            
        except Exception as e:
            logger.error(f"Agent interaction routing error: {e}")
            return "error"
    
    def _supervisor_router(self, state: AgentState) -> str:
        """Route based on supervisor decisions"""
        try:
            # Check for errors
            if state.error_log and any(
                error.get("agent_type") == "supervisor" for error in state.error_log[-3:]
            ):
                return "error"
            
            # Check if human is required
            if state.requires_human:
                return "human_required"
            
            # Check if resolved
            if state.status == TicketStatus.RESOLVED:
                return "resolved"
            
            # Check if further escalation is needed
            if state.escalation_level >= 3:
                return "escalate"
            
            # Default to agent assignment
            return "assign_agent"
            
        except Exception as e:
            logger.error(f"Supervisor routing error: {e}")
            return "error"
    
    def _escalation_router(self, state: AgentState) -> str:
        """Route based on escalation handling results"""
        try:
            # Check escalation level and requirements
            if state.requires_human or state.escalation_level >= 3:
                return "escalate_to_human"
            
            if state.escalation_level >= 2:
                return "escalate_to_supervisor"
            
            # Retry with different agent
            return "retry_with_agent"
            
        except Exception as e:
            logger.error(f"Escalation routing error: {e}")
            return "error"
    
    def _quality_check_router(self, state: AgentState) -> str:
        """Route based on quality check results"""
        try:
            quality_score = state.performance_metrics.get("quality_score", 0.0)
            
            # Check for quality issues
            if quality_score >= 0.8:
                return "approved"
            elif quality_score >= 0.6:
                return "needs_followup"
            else:
                return "escalate"
                
        except Exception as e:
            logger.error(f"Quality check routing error: {e}")
            return "escalate"
    
    # Helper methods for routing decisions
    def _should_escalate_agent_interaction(self, state: AgentState) -> bool:
        """Determine if agent interaction should be escalated"""
        escalation_conditions = [
            len(state.resolution_attempts) >= 3,
            state.confidence_score < 0.6,
            state.sentiment in [Sentiment.NEGATIVE, Sentiment.FRUSTRATED],
            state.sla_breach_risk,
            state.customer and state.customer.tier == CustomerTier.PLATINUM and state.confidence_score < 0.8
        ]
        
        return any(escalation_conditions)
    
    def _needs_agent_transfer(self, state: AgentState) -> bool:
        """Determine if conversation needs agent transfer"""
        transfer_conditions = [
            # Intent has changed significantly
            state.intent_confidence > 0.8 and self._intent_requires_different_agent(state),
            # Current agent attempted multiple times unsuccessfully
            len([attempt for attempt in state.resolution_attempts 
                 if attempt.get("agent_type") == state.current_agent_type]) >= 2,
            # Customer explicitly requested different type of help
            self._customer_requested_transfer(state)
        ]
        
        return any(transfer_conditions)
    
    def _can_continue_with_agent(self, state: AgentState) -> bool:
        """Determine if conversation can continue with current agent"""
        continue_conditions = [
            state.confidence_score >= 0.7,
            len(state.resolution_attempts) < 3,
            state.sentiment not in [Sentiment.FRUSTRATED],
            not state.sla_breach_risk
        ]
        
        return all(continue_conditions)
    
    def _intent_requires_different_agent(self, state: AgentState) -> bool:
        """Check if current intent requires a different agent type"""
        current_agent = state.current_agent_type
        optimal_agent = self._get_optimal_agent_for_intent(state.current_intent)
        
        return current_agent != optimal_agent
    
    def _get_optimal_agent_for_intent(self, intent: str) -> str:
        """Get optimal agent type for given intent"""
        intent_agent_mapping = {
            "billing_inquiry": "billing",
            "payment_issue": "billing",
            "refund_request": "billing",
            "product_inquiry": "sales",
            "upgrade_request": "sales",
            "technical_issue": "tier2_technical",
            "connection_problem": "tier2_technical",
            "system_error": "tier3_expert",
            "complaint": "supervisor",
            "escalation": "supervisor"
        }
        
        return intent_agent_mapping.get(intent, "tier1_support")
    
    def _customer_requested_transfer(self, state: AgentState) -> bool:
        """Check if customer explicitly requested transfer"""
        if not state.conversation_history:
            return False
        
        last_message = state.conversation_history[-1]
        if last_message.get("speaker") != "customer":
            return False
        
        transfer_keywords = [
            "speak to someone else",
            "different agent",
            "transfer me",
            "someone who can help",
            "supervisor",
            "manager"
        ]
        
        message_lower = last_message.get("message", "").lower()
        return any(keyword in message_lower for keyword in transfer_keywords)
    
    async def _generate_clarification_message(self, state: AgentState) -> str:
        """Generate appropriate clarification message based on context"""
        
        # Check what type of clarification is needed
        if state.intent_confidence < 0.3:
            return "I want to make sure I understand how to help you best. Could you please describe what you're trying to do or what issue you're experiencing?"
        
        elif state.current_intent == "unknown":
            return "I'm not quite sure what you need help with. Are you looking for help with billing, technical support, or something else?"
        
        else:
            return f"I think you might need help with {state.current_intent}, but I want to make sure. Could you provide a bit more detail about what you need?"