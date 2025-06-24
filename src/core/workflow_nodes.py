"""
LangGraph workflow nodes for Contact Center Agentic Flow System
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from dataclasses import asdict

from src.models.state import AgentState, TicketStatus, Sentiment, Priority, CustomerTier
from src.core.logging import get_logger

logger = get_logger(__name__)


class WorkflowNodes:
    """Collection of workflow nodes for LangGraph orchestration"""
    
    def __init__(self, agents: Dict[str, Any], tool_registry: Any):
        self.agents = agents
        self.tool_registry = tool_registry
    
    async def customer_entry_node(self, state: AgentState) -> AgentState:
        """Process customer entry and initialize conversation"""
        logger.info(f"Processing customer entry for conversation {state.conversation_id}")
        
        # Initialize conversation metadata
        if not state.session_start:
            state.session_start = datetime.now()
        
        state.last_activity = datetime.now()
        state.status = TicketStatus.NEW
        
        # Get customer context if available
        if state.customer and state.customer.customer_id:
            try:
                customer_data = await self.tool_registry.execute_tool(
                    "get_customer_profile",
                    {"customer_id": state.customer.customer_id},
                    {"agent_type": "system", "permissions": ["read_customer_data"]}
                )
                if customer_data.get("success"):
                    # Update customer profile with latest data
                    state.customer = customer_data["data"]
            except Exception as e:
                logger.warning(f"Could not load customer profile: {e}")
        
        # Add entry to conversation history
        state.conversation_history.append({
            "timestamp": datetime.now(),
            "speaker": "customer",
            "message": state.current_message,
            "intent": None,
            "confidence": None,
            "agent_type": None
        })
        
        return state
    
    async def intent_classification_node(self, state: AgentState) -> AgentState:
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
                "message": f"Intent classified as: {state.current_intent} (confidence: {state.intent_confidence:.2f})",
                "intent": state.current_intent,
                "confidence": state.intent_confidence,
                "agent_type": "intent_classifier"
            })
            
            logger.info(f"Intent classified: {state.current_intent} (confidence: {state.intent_confidence:.2f})")
            
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            state.current_intent = "unknown"
            state.intent_confidence = 0.0
            state.sentiment = Sentiment.NEUTRAL
            state.error_log.append({
                "timestamp": datetime.now().isoformat(),
                "error_type": type(e).__name__,
                "error_message": str(e),
                "node": "intent_classification"
            })
        
        return state
    
    async def smart_routing_node(self, state: AgentState) -> AgentState:
        """Determine optimal agent routing based on context"""
        logger.info(f"Smart routing for conversation {state.conversation_id}")
        
        try:
            # Calculate routing scores for each agent
            routing_scores = await self._calculate_routing_scores(state)
            
            # Select best agent
            best_agent = max(routing_scores.items(), key=lambda x: x[1])
            state.current_agent_type = best_agent[0]
            state.agent_queue = best_agent[0]
            
            # Add routing decision to conversation history
            state.conversation_history.append({
                "timestamp": datetime.now(),
                "speaker": "system",
                "message": f"Routed to {state.current_agent_type} (score: {best_agent[1]:.2f})",
                "intent": state.current_intent,
                "confidence": best_agent[1],
                "agent_type": "router"
            })
            
            logger.info(f"Routed to agent: {state.current_agent_type} (score: {best_agent[1]:.2f})")
            
        except Exception as e:
            logger.error(f"Smart routing failed: {e}")
            # Default to tier1 support
            state.current_agent_type = "tier1_support"
            state.agent_queue = "tier1_support"
            state.error_log.append({
                "timestamp": datetime.now().isoformat(),
                "error_type": type(e).__name__,
                "error_message": str(e),
                "node": "smart_routing"
            })
        
        return state
    
    async def agent_interaction_node(self, state: AgentState, agent_type: str) -> AgentState:
        """Execute interaction with specified agent"""
        logger.info(f"Executing {agent_type} interaction for conversation {state.conversation_id}")
        
        agent = self.agents.get(agent_type)
        if not agent:
            logger.error(f"Agent {agent_type} not found")
            state.should_escalate = True
            return state
        
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
                resolution_attempt = {
                    "agent_type": agent_type,
                    "timestamp": datetime.now(),
                    "actions_taken": result.get("actions_taken", []),
                    "tools_used": result.get("tools_used", []),
                    "outcome": result.get("outcome", ""),
                    "confidence": result.get("confidence", 0.0),
                    "success": result.get("success", False)
                }
                state.resolution_attempts.append(resolution_attempt)
            
            # Update tools used
            if result.get("tools_used"):
                state.tools_used.extend(result["tools_used"])
            
            # Update status if provided
            if result.get("new_status"):
                state.status = result["new_status"]
            
            # Check if escalation is needed
            if await self._should_escalate_from_agent_response(state, result):
                state.should_escalate = True
            
            logger.info(f"Agent {agent_type} processed message with confidence: {state.confidence_score:.2f}")
            
        except Exception as e:
            logger.error(f"Agent interaction failed for {agent_type}: {e}")
            state.should_escalate = True
            state.error_log.append({
                "timestamp": datetime.now().isoformat(),
                "error_type": type(e).__name__,
                "error_message": str(e),
                "agent_type": agent_type,
                "node": "agent_interaction"
            })
        
        return state
    
    async def escalation_handler_node(self, state: AgentState) -> AgentState:
        """Handle escalation logic"""
        logger.info(f"Handling escalation for conversation {state.conversation_id}")
        
        try:
            # Determine escalation level and target
            escalation_target = await self._determine_escalation_target(state)
            escalation_reason = await self._determine_escalation_reason(state)
            
            # Create escalation record
            escalation_record = {
                "from_agent": state.current_agent_type,
                "to_agent": escalation_target,
                "timestamp": datetime.now(),
                "reason": escalation_reason,
                "context_transfer": await self._prepare_context_transfer(state)
            }
            
            # Update state
            state.escalation_level += 1
            state.escalation_history.append(escalation_record)
            state.previous_agents.append(state.current_agent_type)
            state.current_agent_type = escalation_target
            
            # Add escalation to conversation history
            state.conversation_history.append({
                "timestamp": datetime.now(),
                "speaker": "system",
                "message": f"Escalated from {escalation_record['from_agent']} to {escalation_target}. Reason: {escalation_reason}",
                "intent": state.current_intent,
                "confidence": None,
                "agent_type": "escalation_handler"
            })
            
            # Reset should_escalate flag
            state.should_escalate = False
            
            logger.info(f"Escalated to {escalation_target}, level: {state.escalation_level}")
            
        except Exception as e:
            logger.error(f"Escalation handling failed: {e}")
            state.requires_human = True
            state.error_log.append({
                "timestamp": datetime.now().isoformat(),
                "error_type": type(e).__name__,
                "error_message": str(e),
                "node": "escalation_handler"
            })
        
        return state
    
    async def quality_check_node(self, state: AgentState) -> AgentState:
        """Perform quality check on resolution"""
        logger.info(f"Quality check for conversation {state.conversation_id}")
        
        try:
            # Calculate quality metrics
            quality_score = await self._calculate_quality_score(state)
            resolution_quality = await self._assess_resolution_quality(state)
            customer_satisfaction_prediction = await self._predict_customer_satisfaction(state)
            
            # Update state with quality metrics
            state.performance_metrics.update({
                "quality_score": quality_score,
                "resolution_quality": resolution_quality,
                "predicted_satisfaction": customer_satisfaction_prediction,
                "quality_check_timestamp": datetime.now().isoformat()
            })
            
            # Add quality check to conversation history
            state.conversation_history.append({
                "timestamp": datetime.now(),
                "speaker": "system",
                "message": f"Quality check completed. Score: {quality_score:.2f}",
                "intent": state.current_intent,
                "confidence": quality_score,
                "agent_type": "quality_checker"
            })
            
            logger.info(f"Quality check completed with score: {quality_score:.2f}")
            
        except Exception as e:
            logger.error(f"Quality check failed: {e}")
            state.error_log.append({
                "timestamp": datetime.now().isoformat(),
                "error_type": type(e).__name__,
                "error_message": str(e),
                "node": "quality_check"
            })
        
        return state
    
    async def human_handoff_node(self, state: AgentState) -> AgentState:
        """Handle handoff to human agent"""
        logger.info(f"Human handoff for conversation {state.conversation_id}")
        
        try:
            # Set human requirement flags
            state.requires_human = True
            state.status = TicketStatus.ESCALATED
            
            # Generate handoff context
            handoff_context = await self._generate_handoff_context(state)
            
            # Store handoff context
            state.performance_metrics["human_handoff_context"] = handoff_context
            
            # Add handoff to conversation history
            state.conversation_history.append({
                "timestamp": datetime.now(),
                "speaker": "system",
                "message": "Conversation transferred to human agent",
                "intent": state.current_intent,
                "confidence": None,
                "agent_type": "human_handoff"
            })
            
            # Execute handoff tool if available
            try:
                await self.tool_registry.execute_tool(
                    "transfer_to_human_agent",
                    {
                        "conversation_id": state.conversation_id,
                        "handoff_context": handoff_context,
                        "priority": state.ticket.priority.value if state.ticket else "medium"
                    },
                    {"agent_type": "system", "permissions": ["transfer_conversations"]}
                )
            except Exception as tool_error:
                logger.warning(f"Human handoff tool execution failed: {tool_error}")
            
            logger.info(f"Human handoff completed for conversation {state.conversation_id}")
            
        except Exception as e:
            logger.error(f"Human handoff failed: {e}")
            state.error_log.append({
                "timestamp": datetime.now().isoformat(),
                "error_type": type(e).__name__,
                "error_message": str(e),
                "node": "human_handoff"
            })
        
        return state
    
    # Helper methods for routing and decision making
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
            "account_access": {"tier1_support": 0.8},
            "password_reset": {"tier1_support": 0.9},
            "technical": {"tier2_technical": 0.8, "tier1_support": 0.3},
            "connection_issue": {"tier2_technical": 0.9},
            "system_error": {"tier2_technical": 0.8, "tier3_expert": 0.6},
            "billing": {"billing": 0.9, "tier1_support": 0.2},
            "payment_issue": {"billing": 0.9},
            "refund_request": {"billing": 0.8},
            "sales": {"sales": 0.9, "tier1_support": 0.1},
            "product_inquiry": {"sales": 0.8},
            "upgrade_request": {"sales": 0.9},
            "complaint": {"supervisor": 0.7, "tier3_expert": 0.5},
            "escalation": {"supervisor": 1.0},
            "cancellation": {"supervisor": 0.6, "tier3_expert": 0.4}
        }
        
        # Apply intent weights
        intent_category = await self._categorize_intent(state.current_intent)
        if intent_category in intent_weights:
            for agent, weight in intent_weights[intent_category].items():
                scores[agent] += weight
        
        # Customer tier adjustments
        if state.customer:
            tier_multipliers = {
                CustomerTier.PLATINUM: {"tier3_expert": 1.3, "supervisor": 1.2},
                CustomerTier.GOLD: {"tier2_technical": 1.2, "tier3_expert": 1.1},
                CustomerTier.SILVER: {"tier1_support": 1.1, "tier2_technical": 1.0},
                CustomerTier.BRONZE: {"tier1_support": 1.2}
            }
            
            if state.customer.tier in tier_multipliers:
                for agent, multiplier in tier_multipliers[state.customer.tier].items():
                    scores[agent] *= multiplier
        
        # Complexity adjustments based on previous attempts
        complexity_factor = len(state.resolution_attempts) * 0.15
        scores["tier2_technical"] += complexity_factor
        scores["tier3_expert"] += complexity_factor * 1.5
        scores["supervisor"] += complexity_factor * 0.5
        
        # Sentiment adjustments
        if state.sentiment in [Sentiment.NEGATIVE, Sentiment.FRUSTRATED]:
            scores["supervisor"] += 0.4
            scores["tier3_expert"] += 0.3
            # Reduce tier1 score for negative sentiment
            scores["tier1_support"] *= 0.7
        
        # Escalation level adjustments
        if state.escalation_level >= 1:
            scores["supervisor"] += 0.5
            scores["tier3_expert"] += 0.3
        
        # Time-based urgency (SLA considerations)
        if state.sla_breach_risk:
            scores["tier3_expert"] += 0.4
            scores["supervisor"] += 0.3
        
        # Confidence-based adjustments
        if state.intent_confidence < 0.7:
            scores["supervisor"] += 0.2
        
        return scores
    
    async def _categorize_intent(self, intent: str) -> str:
        """Categorize intent into broad categories for routing"""
        intent_mapping = {
            "account_access": "account_access",
            "login_issue": "account_access",
            "password_reset": "password_reset",
            "forgot_password": "password_reset",
            "service_status": "technical",
            "connection_issue": "connection_issue",
            "slow_performance": "technical",
            "system_error": "system_error",
            "billing_inquiry": "billing",
            "payment_issue": "payment_issue",
            "refund_request": "refund_request",
            "invoice_question": "billing",
            "product_inquiry": "product_inquiry",
            "pricing_question": "sales",
            "upgrade_request": "upgrade_request",
            "downgrade_request": "sales",
            "complaint": "complaint",
            "dissatisfaction": "complaint",
            "escalation": "escalation",
            "speak_to_manager": "escalation",
            "cancellation": "cancellation",
            "terminate_service": "cancellation",
            "general_inquiry": "faq",
            "how_to": "faq"
        }
        
        return intent_mapping.get(intent, "faq")
    
    async def _should_escalate_from_agent_response(self, state: AgentState, agent_response: Dict[str, Any]) -> bool:
        """Determine if escalation is needed based on agent response"""
        escalation_triggers = [
            agent_response.get("confidence", 1.0) < 0.6,
            agent_response.get("requires_escalation", False),
            agent_response.get("success", True) is False,
            len(state.resolution_attempts) >= 3,
            state.sentiment in [Sentiment.NEGATIVE, Sentiment.FRUSTRATED] and agent_response.get("confidence", 1.0) < 0.8
        ]
        
        return any(escalation_triggers)
    
    async def _determine_escalation_target(self, state: AgentState) -> str:
        """Determine appropriate escalation target"""
        current_agent = state.current_agent_type
        escalation_level = state.escalation_level
        
        # Escalation hierarchy
        escalation_paths = {
            "tier1_support": ["tier2_technical", "supervisor"],
            "tier2_technical": ["tier3_expert", "supervisor"],
            "tier3_expert": ["supervisor"],
            "sales": ["supervisor"],
            "billing": ["supervisor"],
            "supervisor": ["human_handoff"]
        }
        
        # Special escalation conditions
        if state.requires_human or escalation_level >= 3:
            return "human_handoff"
        
        if current_agent in escalation_paths:
            path = escalation_paths[current_agent]
            if escalation_level < len(path):
                return path[escalation_level]
            else:
                return "supervisor"
        
        return "supervisor"
    
    async def _determine_escalation_reason(self, state: AgentState) -> str:
        """Determine reason for escalation"""
        reasons = []
        
        if len(state.resolution_attempts) >= 3:
            reasons.append("multiple_failed_attempts")
        if state.confidence_score < 0.6:
            reasons.append("low_confidence")
        if state.sentiment in [Sentiment.NEGATIVE, Sentiment.FRUSTRATED]:
            reasons.append("negative_customer_sentiment")
        if state.sla_breach_risk:
            reasons.append("sla_breach_risk")
        if state.customer and state.customer.tier == CustomerTier.PLATINUM:
            reasons.append("vip_customer_escalation")
        if any(error for error in state.error_log if error.get("agent_type")):
            reasons.append("agent_processing_errors")
        
        return ", ".join(reasons) if reasons else "agent_requested_escalation"
    
    async def _prepare_context_transfer(self, state: AgentState) -> Dict[str, Any]:
        """Prepare comprehensive context for agent transfer"""
        return {
            "conversation_summary": await self._generate_conversation_summary(state),
            "customer_profile": asdict(state.customer) if state.customer else {},
            "conversation_metadata": {
                "conversation_id": state.conversation_id,
                "session_id": state.session_id,
                "start_time": state.session_start.isoformat() if state.session_start else None,
                "duration": (datetime.now() - state.session_start).total_seconds() if state.session_start else 0
            },
            "intent_analysis": {
                "current_intent": state.current_intent,
                "intent_confidence": state.intent_confidence,
                "sentiment": state.sentiment.value,
                "sentiment_score": state.sentiment_score
            },
            "resolution_history": state.resolution_attempts,
            "tools_used": state.tools_used,
            "escalation_history": state.escalation_history,
            "performance_metrics": state.performance_metrics,
            "recommended_actions": await self._generate_recommended_actions(state),
            "context_transfer_timestamp": datetime.now().isoformat()
        }
    
    async def _calculate_quality_score(self, state: AgentState) -> float:
        """Calculate comprehensive quality score for conversation"""
        quality_factors = {}
        
        # Resolution success factor (40% weight)
        if state.status == TicketStatus.RESOLVED:
            quality_factors["resolution_success"] = 0.4
        elif state.status == TicketStatus.IN_PROGRESS:
            quality_factors["resolution_success"] = 0.2
        else:
            quality_factors["resolution_success"] = 0.0
        
        # Customer satisfaction factor (30% weight)
        sentiment_score = min(max(state.sentiment_score, 0), 1)  # Normalize to 0-1
        quality_factors["customer_satisfaction"] = sentiment_score * 0.3
        
        # Efficiency factor (20% weight)
        max_attempts = 5
        efficiency = max(0, 1 - (len(state.resolution_attempts) / max_attempts))
        quality_factors["efficiency"] = efficiency * 0.2
        
        # Confidence factor (10% weight)
        quality_factors["confidence"] = state.confidence_score * 0.1
        
        total_score = sum(quality_factors.values())
        
        # Apply penalties
        if state.escalation_level > 0:
            penalty = min(0.1 * state.escalation_level, 0.3)  # Max 30% penalty
            total_score *= (1 - penalty)
        
        if len(state.error_log) > 0:
            error_penalty = min(0.05 * len(state.error_log), 0.2)  # Max 20% penalty
            total_score *= (1 - error_penalty)
        
        return max(0, min(1, total_score))  # Ensure score is between 0 and 1
    
    async def _assess_resolution_quality(self, state: AgentState) -> str:
        """Assess the quality of resolution"""
        quality_score = await self._calculate_quality_score(state)
        
        if quality_score >= 0.8:
            return "excellent"
        elif quality_score >= 0.6:
            return "good"
        elif quality_score >= 0.4:
            return "acceptable"
        else:
            return "poor"
    
    async def _predict_customer_satisfaction(self, state: AgentState) -> float:
        """Predict customer satisfaction based on conversation metrics"""
        satisfaction_factors = {
            "sentiment_positive": 0.4 if state.sentiment in [Sentiment.POSITIVE] else 0.0,
            "quick_resolution": 0.3 if len(state.resolution_attempts) <= 2 else 0.1,
            "high_confidence": 0.2 if state.confidence_score >= 0.8 else 0.0,
            "no_escalation": 0.1 if state.escalation_level == 0 else 0.0
        }
        
        base_satisfaction = sum(satisfaction_factors.values())
        
        # Apply negative factors
        if state.sentiment in [Sentiment.NEGATIVE, Sentiment.FRUSTRATED]:
            base_satisfaction *= 0.5
        
        if len(state.error_log) > 0:
            base_satisfaction *= 0.8
        
        return max(0, min(1, base_satisfaction))
    
    async def _generate_conversation_summary(self, state: AgentState) -> str:
        """Generate a comprehensive conversation summary"""
        summary_components = [
            f"Customer Intent: {state.current_intent}",
            f"Confidence: {state.intent_confidence:.2f}",
            f"Current Status: {state.status.value}",
            f"Agent Interactions: {len([h for h in state.conversation_history if h.get('speaker') == 'agent'])}",
            f"Resolution Attempts: {len(state.resolution_attempts)}",
            f"Escalation Level: {state.escalation_level}",
            f"Customer Sentiment: {state.sentiment.value} ({state.sentiment_score:.2f})",
            f"Tools Used: {', '.join(set(state.tools_used)) if state.tools_used else 'None'}"
        ]
        
        if state.customer:
            summary_components.append(f"Customer Tier: {state.customer.tier.value}")
        
        return " | ".join(summary_components)
    
    async def _generate_handoff_context(self, state: AgentState) -> Dict[str, Any]:
        """Generate comprehensive context for human agent handoff"""
        return {
            "conversation_summary": await self._generate_conversation_summary(state),
            "urgency_level": await self._assess_urgency_level(state),
            "customer_context": {
                "customer_id": state.customer.customer_id if state.customer else None,
                "tier": state.customer.tier.value if state.customer else "unknown",
                "sentiment": state.sentiment.value,
                "satisfaction_risk": state.customer_satisfaction_risk
            },
            "technical_context": {
                "tools_attempted": list(set(state.tools_used)),
                "resolution_attempts": len(state.resolution_attempts),
                "error_count": len(state.error_log),
                "confidence_score": state.confidence_score
            },
            "escalation_context": {
                "escalation_level": state.escalation_level,
                "escalation_reasons": [h.get("reason") for h in state.escalation_history],
                "previous_agents": state.previous_agents
            },
            "recommended_actions": await self._generate_recommended_actions(state),
            "conversation_transcript": state.conversation_history[-10:],  # Last 10 interactions
            "handoff_timestamp": datetime.now().isoformat()
        }
    
    async def _assess_urgency_level(self, state: AgentState) -> str:
        """Assess urgency level for human handoff"""
        urgency_factors = {
            "high": [
                state.customer and state.customer.tier == CustomerTier.PLATINUM,
                state.sentiment in [Sentiment.FRUSTRATED],
                state.sla_breach_risk,
                len(state.error_log) > 2
            ],
            "medium": [
                state.customer and state.customer.tier == CustomerTier.GOLD,
                state.sentiment == Sentiment.NEGATIVE,
                state.escalation_level >= 2,
                len(state.resolution_attempts) >= 3
            ],
            "low": [
                state.escalation_level <= 1,
                state.sentiment in [Sentiment.NEUTRAL, Sentiment.POSITIVE]
            ]
        }
        
        if any(urgency_factors["high"]):
            return "high"
        elif any(urgency_factors["medium"]):
            return "medium"
        else:
            return "low"
    
    async def _generate_recommended_actions(self, state: AgentState) -> List[str]:
        """Generate recommended actions for the receiving agent"""
        recommendations = []
        
        # Sentiment-based recommendations
        if state.sentiment in [Sentiment.NEGATIVE, Sentiment.FRUSTRATED]:
            recommendations.append("Prioritize empathy and active listening")
            recommendations.append("Consider offering compensation or service credits")
        
        # History-based recommendations
        if len(state.resolution_attempts) >= 3:
            recommendations.append("Review all previous resolution attempts")
            recommendations.append("Consider escalating to technical specialist")
        
        # Customer tier recommendations
        if state.customer and state.customer.tier == CustomerTier.PLATINUM:
            recommendations.append("Apply VIP customer service protocols")
            recommendations.append("Ensure immediate supervisor awareness")
        
        # Technical recommendations
        if state.tools_used and len(set(state.tools_used)) >= 3:
            recommendations.append("Review technical diagnostic results")
        
        # Urgency recommendations
        if state.sla_breach_risk:
            recommendations.append("URGENT: Address SLA breach risk immediately")
        
        # Error-based recommendations
        if len(state.error_log) > 0:
            recommendations.append("Review system errors encountered during conversation")
        
        return recommendations