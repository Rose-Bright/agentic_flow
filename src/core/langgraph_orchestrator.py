"""
LangGraph orchestration layer for Contact Center Agentic Flow System
"""

from typing import Dict, Any, List, Optional, Literal
from datetime import datetime
import asyncio
from dataclasses import asdict

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode

from src.models.state import AgentState, TicketStatus, Sentiment, Priority, CustomerTier
from src.core.config import get_settings
from src.core.logging import get_logger
from src.services.tool_registry import ToolRegistry
from src.agents.intent_classification_agent import IntentClassificationAgent
from src.agents.tier1_support_agent import Tier1SupportAgent
from src.agents.tier2_technical_agent import Tier2TechnicalAgent
from src.agents.tier3_expert_agent import Tier3ExpertAgent
from src.agents.sales_agent import SalesAgent
from src.agents.billing_agent import BillingAgent
from src.agents.supervisor_agent import SupervisorAgent

logger = get_logger(__name__)


class LangGraphOrchestrator:
    """Main LangGraph orchestrator for conversation flow management"""
    
    def __init__(self):
        self.settings = get_settings()
        self.tool_registry = ToolRegistry()
        self.graph = None
        self.checkpointer = MemorySaver()
        self.agents = {}
        
    async def initialize(self):
        """Initialize the LangGraph orchestrator with agents and workflow"""
        logger.info("Initializing LangGraph orchestrator...")
        
        # Initialize agents
        await self._initialize_agents()
        
        # Build the conversation flow graph
        self.graph = await self._build_conversation_graph()
        
        # Compile the graph
        self.compiled_graph = self.graph.compile(checkpointer=self.checkpointer)
        
        logger.info("LangGraph orchestrator initialized successfully")
    
    async def _initialize_agents(self):
        """Initialize all specialized agents"""
        logger.info("Initializing specialized agents...")
        
        # Initialize Intent Classification Agent
        self.agents['intent_classifier'] = IntentClassificationAgent(
            name="intent_classifier",
            model=self.settings.gemini_pro_model,
            capabilities=["intent_classification", "sentiment_analysis", "language_detection"],
            tools=["get_customer_profile", "search_knowledge_base", "log_interaction_metrics"],
            confidence_threshold=0.85
        )
        
        # Initialize Tier 1 Support Agent
        self.agents['tier1_support'] = Tier1SupportAgent(
            name="tier1_support",
            model=self.settings.gemini_pro_model,
            capabilities=["faq_resolution", "basic_troubleshooting", "account_queries"],
            tools=[
                "get_customer_profile", "get_account_services", "search_knowledge_base",
                "get_troubleshooting_guide", "update_ticket_status", "send_customer_notification"
            ],
            confidence_threshold=0.7
        )
        
        # Initialize Tier 2 Technical Agent
        self.agents['tier2_technical'] = Tier2TechnicalAgent(
            name="tier2_technical",
            model=self.settings.claude_3_model,
            capabilities=["advanced_diagnostics", "system_configuration", "integration_troubleshooting"],
            tools=[
                "run_diagnostic_test", "check_system_logs", "get_similar_cases",
                "schedule_technician_visit", "update_customer_notes"
            ],
            confidence_threshold=0.8
        )
        
        # Initialize Tier 3 Expert Agent
        self.agents['tier3_expert'] = Tier3ExpertAgent(
            name="tier3_expert",
            model=self.settings.claude_3_model,
            capabilities=["system_architecture", "complex_integrations", "compliance_issues"],
            tools=[
                "apply_credit_adjustment", "process_order", "check_compliance_requirements",
                "audit_log_action"
            ],
            confidence_threshold=0.9
        )
        
        # Initialize Sales Agent
        self.agents['sales'] = SalesAgent(
            name="sales",
            model=self.settings.gemini_pro_model,
            capabilities=["product_recommendations", "pricing_quotes", "upselling"],
            tools=[
                "get_product_information", "generate_quote", "check_inventory_availability",
                "process_order", "calculate_customer_satisfaction"
            ],
            confidence_threshold=0.75
        )
        
        # Initialize Billing Agent
        self.agents['billing'] = BillingAgent(
            name="billing",
            model=self.settings.gemini_pro_model,
            capabilities=["billing_explanations", "payment_processing", "dispute_resolution"],
            tools=[
                "get_billing_information", "process_payment", "apply_credit_adjustment",
                "setup_payment_plan", "verify_customer_identity"
            ],
            confidence_threshold=0.8
        )
        
        # Initialize Supervisor Agent
        self.agents['supervisor'] = SupervisorAgent(
            name="supervisor",
            model=self.settings.claude_3_model,
            capabilities=["complex_routing", "escalation_management", "quality_assurance"],
            tools=[
                "get_agent_performance_data", "escalate_ticket", "transfer_to_human_agent",
                "schedule_callback"
            ],
            confidence_threshold=0.85
        )
        
        # Register tool registry with all agents
        for agent in self.agents.values():
            agent.register_tool_registry(self.tool_registry)
    
    async def _build_conversation_graph(self) -> StateGraph:
        """Build the main conversation flow graph using LangGraph"""
        logger.info("Building conversation flow graph...")
        
        # Create the StateGraph
        workflow = StateGraph(AgentState)
        
        # Add nodes for each agent and decision point
        workflow.add_node("customer_entry", self._customer_entry_node)
        workflow.add_node("intent_classification", self._intent_classification_node)
        workflow.add_node("smart_routing", self._smart_routing_node)
        workflow.add_node("tier1_support", self._tier1_support_node)
        workflow.add_node("tier2_technical", self._tier2_technical_node)
        workflow.add_node("tier3_expert", self._tier3_expert_node)
        workflow.add_node("sales", self._sales_node)
        workflow.add_node("billing", self._billing_node)
        workflow.add_node("supervisor", self._supervisor_node)
        workflow.add_node("escalation_handler", self._escalation_handler_node)
        workflow.add_node("quality_check", self._quality_check_node)
        workflow.add_node("human_handoff", self._human_handoff_node)
        
        # Define the conversation flow edges
        workflow.add_edge(START, "customer_entry")
        workflow.add_edge("customer_entry", "intent_classification")
        
        # Conditional edges from intent classification
        workflow.add_conditional_edges(
            "intent_classification",
            self._should_route_to_agent,
            {
                "route_to_agent": "smart_routing",
                "clarification_needed": "intent_classification",
                "escalate": "supervisor"
            }
        )
        
        # Conditional edges from smart routing
        workflow.add_conditional_edges(
            "smart_routing",
            self._determine_agent_routing,
            {
                "tier1_support": "tier1_support",
                "tier2_technical": "tier2_technical", 
                "tier3_expert": "tier3_expert",
                "sales": "sales",
                "billing": "billing",
                "supervisor": "supervisor"
            }
        )
        
        # Agent processing edges
        for agent_name in ["tier1_support", "tier2_technical", "tier3_expert", "sales", "billing"]:
            workflow.add_conditional_edges(
                agent_name,
                self._check_resolution_status,
                {
                    "resolved": "quality_check",
                    "escalate": "escalation_handler",
                    "continue": agent_name,
                    "transfer": "smart_routing"
                }
            )
        
        # Supervisor edges
        workflow.add_conditional_edges(
            "supervisor",
            self._supervisor_decision,
            {
                "assign_agent": "smart_routing",
                "human_required": "human_handoff",
                "resolved": "quality_check"
            }
        )
        
        # Escalation handler edges
        workflow.add_conditional_edges(
            "escalation_handler",
            self._escalation_decision,
            {
                "escalate_to_supervisor": "supervisor",
                "escalate_to_human": "human_handoff",
                "retry_with_agent": "smart_routing"
            }
        )
        
        # Quality check edges
        workflow.add_conditional_edges(
            "quality_check",
            self._quality_check_decision,
            {
                "approved": END,
                "needs_followup": "smart_routing",
                "escalate": "supervisor"
            }
        )
        
        # Human handoff edge
        workflow.add_edge("human_handoff", END)
        
        return workflow
    
    # Node implementations
    async def _customer_entry_node(self, state: AgentState) -> AgentState:
        """Process customer entry and initialize conversation"""
        logger.info(f"Processing customer entry for conversation {state.conversation_id}")
        
        # Initialize conversation metadata
        if not state.session_start:
            state.session_start = datetime.now()
        
        state.last_activity = datetime.now()
        state.status = TicketStatus.NEW
        
        # Get customer context if available
        if state.customer and state.customer.customer_id:
            # Load customer profile using tool
            try:
                customer_data = await self.tool_registry.execute_tool(
                    "get_customer_profile",
                    {"customer_id": state.customer.customer_id},
                    {"agent_type": "system", "permissions": ["read_customer_data"]}
                )
                # Update customer profile with latest data
                if customer_data.get("success"):
                    state.customer = customer_data["data"]
            except Exception as e:
                logger.warning(f"Could not load customer profile: {e}")
        
        return state
    
    async def _intent_classification_node(self, state: AgentState) -> AgentState:
        """Classify customer intent and sentiment"""
        logger.info(f"Classifying intent for conversation {state.conversation_id}")
        
        agent = self.agents['intent_classifier']
        
        try:
            # Process message with intent classification agent
            result = await agent.handle_message(state.current_message, state)
            
            # Update state with classification results
            state.current_intent = result.get("intent", "")
            state.intent_confidence = result.get("confidence", 0.0)
            state.sentiment = result.get("sentiment", Sentiment.NEUTRAL)
            state.sentiment_score = result.get("sentiment_score", 0.0)
            
            # Add conversation turn
            state.conversation_history.append({
                "timestamp": datetime.now(),
                "speaker": "system",
                "message": f"Intent classified as: {state.current_intent}",
                "intent": state.current_intent,
                "confidence": state.intent_confidence,
                "agent_type": "intent_classifier"
            })
            
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            state.current_intent = "unknown"
            state.intent_confidence = 0.0
            state.sentiment = Sentiment.NEUTRAL
        
        return state
    
    async def _smart_routing_node(self, state: AgentState) -> AgentState:
        """Determine optimal agent routing based on context"""
        logger.info(f"Smart routing for conversation {state.conversation_id}")
        
        # Calculate routing scores for each agent
        routing_scores = await self._calculate_routing_scores(state)
        
        # Select best agent
        best_agent = max(routing_scores.items(), key=lambda x: x[1])
        state.current_agent_type = best_agent[0]
        state.agent_queue = best_agent[0]
        
        logger.info(f"Routed to agent: {state.current_agent_type} (score: {best_agent[1]:.2f})")
        
        return state
    
    async def _tier1_support_node(self, state: AgentState) -> AgentState:
        """Handle Tier 1 support interactions"""
        return await self._execute_agent_interaction(state, 'tier1_support')
    
    async def _tier2_technical_node(self, state: AgentState) -> AgentState:
        """Handle Tier 2 technical support interactions"""
        return await self._execute_agent_interaction(state, 'tier2_technical')
    
    async def _tier3_expert_node(self, state: AgentState) -> AgentState:
        """Handle Tier 3 expert interactions"""
        return await self._execute_agent_interaction(state, 'tier3_expert')
    
    async def _sales_node(self, state: AgentState) -> AgentState:
        """Handle sales interactions"""
        return await self._execute_agent_interaction(state, 'sales')
    
    async def _billing_node(self, state: AgentState) -> AgentState:
        """Handle billing interactions"""
        return await self._execute_agent_interaction(state, 'billing')
    
    async def _supervisor_node(self, state: AgentState) -> AgentState:
        """Handle supervisor interactions"""
        return await self._execute_agent_interaction(state, 'supervisor')
    
    async def _execute_agent_interaction(self, state: AgentState, agent_type: str) -> AgentState:
        """Execute interaction with specified agent"""
        logger.info(f"Executing {agent_type} interaction for conversation {state.conversation_id}")
        
        agent = self.agents[agent_type]
        
        try:
            # Process message with agent
            result = await agent.handle_message(state.current_message, state)
            
            # Update state with agent response
            state.current_agent_type = agent_type
            state.confidence_score = result.get("confidence", 0.0)
            
            # Add conversation turn
            state.conversation_history.append({
                "timestamp": datetime.now(),
                "speaker": "agent",
                "message": result.get("message", ""),
                "intent": state.current_intent,
                "confidence": result.get("confidence", 0.0),
                "agent_type": agent_type
            })
            
            # Update resolution attempts
            if result.get("resolution_attempt"):
                state.resolution_attempts.append({
                    "agent_type": agent_type,
                    "timestamp": datetime.now(),
                    "actions_taken": result.get("actions_taken", []),
                    "tools_used": result.get("tools_used", []),
                    "outcome": result.get("outcome", ""),
                    "confidence": result.get("confidence", 0.0),
                    "success": result.get("success", False)
                })
            
            # Update tools used
            if result.get("tools_used"):
                state.tools_used.extend(result["tools_used"])
            
            # Update status if provided
            if result.get("new_status"):
                state.status = result["new_status"]
            
        except Exception as e:
            logger.error(f"Agent interaction failed for {agent_type}: {e}")
            state.should_escalate = True
            state.error_log.append({
                "timestamp": datetime.now().isoformat(),
                "error_type": type(e).__name__,
                "error_message": str(e),
                "agent_type": agent_type
            })
        
        return state
    
    async def _escalation_handler_node(self, state: AgentState) -> AgentState:
        """Handle escalation logic"""
        logger.info(f"Handling escalation for conversation {state.conversation_id}")
        
        # Determine escalation level
        escalation_level = await self._determine_escalation_level(state)
        
        # Create escalation record
        escalation_record = {
            "from_agent": state.current_agent_type,
            "to_agent": escalation_level,
            "timestamp": datetime.now(),
            "reason": await self._determine_escalation_reason(state),
            "context_transfer": await self._prepare_context_transfer(state)
        }
        
        # Update state
        state.escalation_level += 1
        state.escalation_history.append(escalation_record)
        state.previous_agents.append(state.current_agent_type)
        state.current_agent_type = escalation_level
        
        return state
    
    async def _quality_check_node(self, state: AgentState) -> AgentState:
        """Perform quality check on resolution"""
        logger.info(f"Quality check for conversation {state.conversation_id}")
        
        # Basic quality checks
        quality_score = await self._calculate_quality_score(state)
        
        # Update state with quality metrics
        state.performance_metrics["quality_score"] = quality_score
        state.performance_metrics["quality_check_timestamp"] = datetime.now().isoformat()
        
        return state
    
    async def _human_handoff_node(self, state: AgentState) -> AgentState:
        """Handle handoff to human agent"""
        logger.info(f"Human handoff for conversation {state.conversation_id}")
        
        state.requires_human = True
        state.status = TicketStatus.ESCALATED
        
        # Create handoff context
        handoff_context = {
            "conversation_summary": await self._generate_conversation_summary(state),
            "customer_context": asdict(state.customer) if state.customer else {},
            "resolution_attempts": state.resolution_attempts,
            "escalation_history": state.escalation_history,
            "recommended_actions": await self._generate_recommended_actions(state)
        }
        
        # Store handoff context
        state.performance_metrics["human_handoff_context"] = handoff_context
        
        return state
    
    # Conditional edge functions
    async def _should_route_to_agent(self, state: AgentState) -> str:
        """Determine if intent classification is sufficient for routing"""
        if state.intent_confidence >= 0.85:
            return "route_to_agent"
        elif state.intent_confidence >= 0.5:
            return "clarification_needed"
        else:
            return "escalate"
    
    async def _determine_agent_routing(self, state: AgentState) -> str:
        """Determine which agent to route to based on intent and context"""
        routing_scores = await self._calculate_routing_scores(state)
        best_agent = max(routing_scores.items(), key=lambda x: x[1])
        return best_agent[0]
    
    async def _check_resolution_status(self, state: AgentState) -> str:
        """Check if conversation is resolved or needs escalation"""
        if state.status == TicketStatus.RESOLVED:
            return "resolved"
        elif state.should_escalate or await self._should_escalate(state):
            return "escalate"
        elif len(state.resolution_attempts) >= 3:
            return "escalate"
        elif state.confidence_score >= 0.8:
            return "resolved"
        else:
            return "continue"
    
    async def _supervisor_decision(self, state: AgentState) -> str:
        """Supervisor decision logic"""
        if state.requires_human:
            return "human_required"
        elif state.status == TicketStatus.RESOLVED:
            return "resolved"
        else:
            return "assign_agent"
    
    async def _escalation_decision(self, state: AgentState) -> str:
        """Escalation decision logic"""
        if state.escalation_level >= 3 or state.requires_human:
            return "escalate_to_human"
        elif state.escalation_level >= 2:
            return "escalate_to_supervisor"
        else:
            return "retry_with_agent"
    
    async def _quality_check_decision(self, state: AgentState) -> str:
        """Quality check decision logic"""
        quality_score = state.performance_metrics.get("quality_score", 0.0)
        
        if quality_score >= 0.8:
            return "approved"
        elif quality_score >= 0.6:
            return "needs_followup"
        else:
            return "escalate"
    
    # Helper methods
    async def _calculate_routing_scores(self, state: AgentState) -> Dict[str, float]:
        """Calculate routing scores for each agent type"""
        scores = {
            "tier1_support": 0.0,
            "tier2_technical": 0.0,
            "tier3_expert": 0.0,
            "sales": 0.0,
            "billing": 0.0,
            "supervisor": 0.0
        }
        
        # Intent-based scoring
        intent_weights = {
            "faq": {"tier1_support": 0.9},
            "technical": {"tier2_technical": 0.8, "tier1_support": 0.3},
            "billing": {"billing": 0.9, "tier1_support": 0.2},
            "sales": {"sales": 0.9, "tier1_support": 0.1},
            "escalation": {"supervisor": 1.0}
        }
        
        # Apply intent weights
        intent_category = await self._categorize_intent(state.current_intent)
        if intent_category in intent_weights:
            for agent, weight in intent_weights[intent_category].items():
                scores[agent] += weight
        
        # Customer tier adjustments
        if state.customer:
            tier_multipliers = {
                CustomerTier.PLATINUM: {"tier3_expert": 1.2, "supervisor": 1.1},
                CustomerTier.GOLD: {"tier2_technical": 1.1, "tier3_expert": 1.0},
                CustomerTier.SILVER: {"tier1_support": 1.1, "tier2_technical": 1.0},
                CustomerTier.BRONZE: {"tier1_support": 1.2}
            }
            
            if state.customer.tier in tier_multipliers:
                for agent, multiplier in tier_multipliers[state.customer.tier].items():
                    scores[agent] *= multiplier
        
        # Complexity adjustments
        complexity_factor = len(state.resolution_attempts) * 0.1
        scores["tier2_technical"] += complexity_factor
        scores["tier3_expert"] += complexity_factor * 1.5
        
        # Sentiment adjustments
        if state.sentiment in [Sentiment.NEGATIVE, Sentiment.FRUSTRATED]:
            scores["supervisor"] += 0.3
            scores["tier3_expert"] += 0.2
        
        return scores
    
    async def _categorize_intent(self, intent: str) -> str:
        """Categorize intent into broad categories"""
        intent_mapping = {
            "account_access": "faq",
            "password_reset": "faq",
            "service_status": "technical",
            "connection_issue": "technical",
            "billing_inquiry": "billing",
            "payment_issue": "billing",
            "product_inquiry": "sales",
            "upgrade_request": "sales",
            "complaint": "escalation",
            "cancellation": "escalation"
        }
        
        return intent_mapping.get(intent, "faq")
    
    async def _should_escalate(self, state: AgentState) -> bool:
        """Determine if conversation should be escalated"""
        escalation_triggers = [
            len(state.resolution_attempts) >= 3,
            state.confidence_score < 0.6,
            state.sentiment in [Sentiment.NEGATIVE, Sentiment.FRUSTRATED],
            state.sla_breach_risk,
            state.customer and state.customer.tier == CustomerTier.PLATINUM and state.sentiment_score < 0.3
        ]
        
        return any(escalation_triggers)
    
    async def _determine_escalation_level(self, state: AgentState) -> str:
        """Determine appropriate escalation level"""
        if state.escalation_level >= 2 or state.requires_human:
            return "human_handoff"
        elif state.escalation_level >= 1:
            return "supervisor"
        else:
            return "tier2_technical"
    
    async def _determine_escalation_reason(self, state: AgentState) -> str:
        """Determine reason for escalation"""
        reasons = []
        
        if len(state.resolution_attempts) >= 3:
            reasons.append("multiple_failed_attempts")
        if state.confidence_score < 0.6:
            reasons.append("low_confidence")
        if state.sentiment in [Sentiment.NEGATIVE, Sentiment.FRUSTRATED]:
            reasons.append("negative_sentiment")
        if state.sla_breach_risk:
            reasons.append("sla_breach_risk")
        if state.customer and state.customer.tier == CustomerTier.PLATINUM:
            reasons.append("vip_customer")
        
        return ", ".join(reasons) if reasons else "agent_request"
    
    async def _prepare_context_transfer(self, state: AgentState) -> Dict[str, Any]:
        """Prepare context for agent transfer"""
        return {
            "conversation_summary": await self._generate_conversation_summary(state),
            "customer_context": asdict(state.customer) if state.customer else {},
            "resolution_attempts": state.resolution_attempts,
            "tools_used": state.tools_used,
            "sentiment_analysis": {
                "current_sentiment": state.sentiment.value,
                "sentiment_score": state.sentiment_score
            },
            "escalation_context": {
                "escalation_level": state.escalation_level,
                "previous_agents": state.previous_agents,
                "escalation_reason": await self._determine_escalation_reason(state)
            }
        }
    
    async def _calculate_quality_score(self, state: AgentState) -> float:
        """Calculate quality score for conversation"""
        quality_factors = {
            "resolution_success": 0.4 if state.status == TicketStatus.RESOLVED else 0.0,
            "customer_satisfaction": min(state.sentiment_score, 1.0) * 0.3,
            "efficiency": max(0, 1 - (len(state.resolution_attempts) / 5)) * 0.2,
            "confidence": state.confidence_score * 0.1
        }
        
        return sum(quality_factors.values())
    
    async def _generate_conversation_summary(self, state: AgentState) -> str:
        """Generate summary of conversation"""
        summary_parts = [
            f"Conversation {state.conversation_id}",
            f"Intent: {state.current_intent}",
            f"Status: {state.status.value}",
            f"Resolution attempts: {len(state.resolution_attempts)}",
            f"Escalation level: {state.escalation_level}",
            f"Customer sentiment: {state.sentiment.value}"
        ]
        
        return " | ".join(summary_parts)
    
    async def _generate_recommended_actions(self, state: AgentState) -> List[str]:
        """Generate recommended actions for human agent"""
        recommendations = []
        
        if state.sentiment in [Sentiment.NEGATIVE, Sentiment.FRUSTRATED]:
            recommendations.append("Prioritize empathy and active listening")
        
        if len(state.resolution_attempts) >= 3:
            recommendations.append("Review previous resolution attempts")
        
        if state.customer and state.customer.tier == CustomerTier.PLATINUM:
            recommendations.append("Apply VIP customer protocols")
        
        if state.sla_breach_risk:
            recommendations.append("Urgent - SLA breach risk")
        
        return recommendations
    
    async def process_conversation(
        self, 
        message: str, 
        conversation_id: str,
        customer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a conversation message through the LangGraph workflow"""
        
        # Create or retrieve conversation state
        initial_state = AgentState(
            session_id=f"session_{conversation_id}",
            conversation_id=conversation_id,
            current_message=message
        )
        
        # Add customer context if provided
        if customer_id:
            # This would typically fetch from database
            initial_state.customer = CustomerProfile(
                customer_id=customer_id,
                name="",
                email="",
                phone="",
                tier=CustomerTier.SILVER,
                account_status="active",
                registration_date=datetime.now(),
                lifetime_value=0.0
            )
        
        try:
            # Process through LangGraph workflow
            result = await self.compiled_graph.ainvoke(
                initial_state,
                {"configurable": {"thread_id": conversation_id}}
            )
            
            logger.info(f"Conversation processed successfully: {conversation_id}")
            
            return {
                "success": True,
                "conversation_id": conversation_id,
                "final_state": result,
                "response": result.conversation_history[-1]["message"] if result.conversation_history else "No response generated",
                "status": result.status.value,
                "agent_type": result.current_agent_type,
                "confidence": result.confidence_score
            }
            
        except Exception as e:
            logger.error(f"Error processing conversation {conversation_id}: {e}")
            return {
                "success": False,
                "conversation_id": conversation_id,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def get_conversation_state(self, conversation_id: str) -> Optional[AgentState]:
        """Retrieve conversation state from checkpointer"""
        try:
            # Get state from checkpointer
            config = {"configurable": {"thread_id": conversation_id}}
            state = await self.compiled_graph.aget_state(config)
            
            return state.values if state else None
            
        except Exception as e:
            logger.error(f"Error retrieving conversation state {conversation_id}: {e}")
            return None
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up LangGraph orchestrator...")
        # Cleanup logic here
        pass