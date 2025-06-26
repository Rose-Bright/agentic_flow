"""
Supervisor Agent for Contact Center Agentic Flow System
Handles complex routing, performance monitoring, escalation management, and quality assurance
"""

from typing import Dict, Any, List, Optional, Literal
from datetime import datetime, timedelta
import asyncio
from dataclasses import asdict
import json
from enum import Enum

from src.agents.base_agent import BaseAgent
from src.models.state import AgentState, TicketStatus, Sentiment, Priority, CustomerTier
from src.core.logging import get_logger
from src.services.tool_registry import ToolRegistry

logger = get_logger(__name__)


class EscalationReason(Enum):
    MULTIPLE_FAILED_ATTEMPTS = "multiple_failed_attempts"
    LOW_CONFIDENCE = "low_confidence"
    NEGATIVE_SENTIMENT = "negative_sentiment"
    SLA_BREACH_RISK = "sla_breach_risk"
    VIP_CUSTOMER = "vip_customer"
    TECHNICAL_COMPLEXITY = "technical_complexity"
    REGULATORY_COMPLIANCE = "regulatory_compliance"
    SYSTEM_EXCEPTION = "system_exception"
    CUSTOMER_REQUEST = "customer_request"
    AGENT_REQUEST = "agent_request"


class SupervisorDecision(Enum):
    ASSIGN_AGENT = "assign_agent"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    RETRY_WITH_OPTIMIZATION = "retry_with_optimization"
    APPLY_EXCEPTION_HANDLING = "apply_exception_handling"
    SCHEDULE_CALLBACK = "schedule_callback"
    MARK_RESOLVED = "mark_resolved"
    REQUEST_MANAGER_REVIEW = "request_manager_review"


class SupervisorAgent(BaseAgent):
    """
    Supervisor Agent responsible for:
    - Complex routing decisions and optimization
    - Performance monitoring and intervention
    - Escalation management and human handoff coordination
    - Quality assurance and exception handling
    - Strategic decision making for edge cases
    """
    
    def __init__(
        self,
        name: str = "supervisor_agent",
        model: str = "claude-3-sonnet",
        capabilities: List[str] = None,
        tools: List[str] = None,
        confidence_threshold: float = 0.85
    ):
        self.tools = tools or []
        super().__init__(name, model, capabilities or [], tools or [], confidence_threshold)
        
        # Supervisor-specific capabilities
        self.capabilities.extend([
            "complex_routing_analysis",
            "performance_optimization",
            "escalation_management", 
            "quality_assurance",
            "exception_handling",
            "strategic_decision_making",
            "resource_allocation",
            "sla_management",
            "compliance_oversight"
        ])
        
        # Supervisor-specific tools
        self.tools.extend([
            "get_agent_performance_data",
            "get_system_metrics",
            "escalate_ticket",
            "transfer_to_human_agent",
            "schedule_callback",
            "apply_business_rules",
            "get_escalation_history",
            "calculate_sla_risk",
            "get_similar_escalations",
            "notify_management",
            "create_exception_case",
            "update_routing_rules"
        ])
        
        # Performance thresholds and business rules
        self.performance_thresholds = {
            "max_resolution_attempts": 3,
            "min_confidence_score": 0.7,
            "max_response_time_minutes": 15,
            "critical_sentiment_threshold": 0.3,
            "sla_breach_warning_minutes": 30,
            "vip_escalation_threshold": 2
        }
        
        # Routing optimization rules
        self.routing_rules = {
            "load_balancing_enabled": True,
            "skill_based_routing": True,
            "workload_distribution": True,
            "priority_queue_management": True
        }
        
        # Quality metrics tracking
        self.quality_metrics = {
            "resolution_accuracy": 0.0,
            "customer_satisfaction": 0.0,
            "first_contact_resolution": 0.0,
            "average_handle_time": 0.0,
            "escalation_rate": 0.0
        }
    
    async def handle_message(self, message: str, state: AgentState) -> Dict[str, Any]:
        """
        Main supervisor message handling with comprehensive analysis and decision making
        """
        logger.info(f"Supervisor handling message for conversation {state.conversation_id}")
        
        try:
            # Comprehensive situation analysis
            situation_analysis = await self._analyze_situation(state)
            
            # Performance impact assessment
            performance_impact = await self._assess_performance_impact(state)
            
            # Strategic decision making
            supervisor_decision = await self._make_strategic_decision(
                state, situation_analysis, performance_impact
            )
            
            # Execute decision with monitoring
            execution_result = await self._execute_supervisor_decision(
                supervisor_decision, state, situation_analysis
            )
            
            # Generate comprehensive response
            response = await self._generate_supervisor_response(
                state, supervisor_decision, execution_result
            )
            
            # Update quality metrics
            await self._update_quality_metrics(state, execution_result)
            
            # Log supervisor action for audit trail
            await self._log_supervisor_action(state, supervisor_decision, execution_result)
            
            return {
                "message": response["message"],
                "decision": supervisor_decision.value,
                "confidence": response["confidence"],
                "actions_taken": execution_result.get("actions_taken", []),
                "tools_used": execution_result.get("tools_used", []),
                "next_steps": response.get("next_steps", []),
                "escalation_required": execution_result.get("escalation_required", False),
                "human_handoff": execution_result.get("human_handoff", False),
                "follow_up_scheduled": execution_result.get("follow_up_scheduled", False),
                "business_impact": performance_impact,
                "resolution_timeline": response.get("resolution_timeline"),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Supervisor agent error for conversation {state.conversation_id}: {e}")
            return await self._handle_supervisor_error(state, e)
    
    async def _analyze_situation(self, state: AgentState) -> Dict[str, Any]:
        """
        Comprehensive situation analysis combining multiple factors
        """
        logger.info(f"Analyzing situation for conversation {state.conversation_id}")
        
        # Customer context analysis
        customer_analysis = await self._analyze_customer_context(state)
        
        # Historical performance analysis
        historical_analysis = await self._analyze_historical_performance(state)
        
        # Current system state analysis
        system_analysis = await self._analyze_system_state(state)
        
        # Risk assessment
        risk_assessment = await self._assess_risks(state)
        
        # Escalation pattern analysis
        escalation_analysis = await self._analyze_escalation_patterns(state)
        
        return {
            "customer_context": customer_analysis,
            "historical_performance": historical_analysis,
            "system_state": system_analysis,
            "risk_assessment": risk_assessment,
            "escalation_patterns": escalation_analysis,
            "complexity_score": await self._calculate_complexity_score(state),
            "urgency_level": await self._determine_urgency_level(state),
            "business_impact": await self._assess_business_impact(state)
        }
    


    async def _analyze_customer_context(self, state: AgentState) -> Dict[str, Any]:
        """Analyze customer context and history"""
        try:
            # Get comprehensive customer profile
            customer_data = await self.tool_registry.execute_tool(
                "get_customer_profile",
                {"customer_id": state.customer.customer_id if state.customer else None},
                {"agent_type": "supervisor", "permissions": ["read_customer_full"]}
            )
            
            # Get interaction history
            interaction_history = await self.tool_registry.execute_tool(
                "get_customer_interaction_history",
                {
                    "customer_id": state.customer.customer_id if state.customer else None,
                    "days_back": 90,
                    "include_sentiment": True
                },
                {"agent_type": "supervisor", "permissions": ["read_interaction_history"]}
            )
            
            # Analyze customer journey and patterns
            journey_analysis = await self._analyze_customer_journey(
                customer_data.get("data", {}),
                interaction_history.get("data", [])
            )
            
            return {
                "profile": customer_data.get("data", {}),
                "interaction_history": interaction_history.get("data", []),
                "journey_analysis": journey_analysis,
                "tier_privileges": await self._get_tier_privileges(state.customer.tier if state.customer else CustomerTier.BRONZE),
                "satisfaction_trend": await self._calculate_satisfaction_trend(interaction_history.get("data", [])),
                "escalation_propensity": await self._calculate_escalation_propensity(state.customer if state.customer else None)
            }
            
        except Exception as e:
            logger.warning(f"Customer context analysis failed: {e}")
            return {"error": str(e), "fallback_analysis": True}
    
    async def _analyze_historical_performance(self, state: AgentState) -> Dict[str, Any]:
        """Analyze historical performance for similar cases"""
        try:
            # Get similar cases
            similar_cases = await self.tool_registry.execute_tool(
                "get_similar_cases",
                {
                    "intent": state.current_intent,
                    "customer_tier": state.customer.tier.value if state.customer else "bronze",
                    "complexity_score": await self._calculate_complexity_score(state),
                    "limit": 10
                },
                {"agent_type": "supervisor", "permissions": ["read_case_history"]}
            )
            
            # Analyze resolution patterns
            resolution_patterns = await self._analyze_resolution_patterns(similar_cases.get("data", []))
            
            # Get agent performance data
            agent_performance = await self.tool_registry.execute_tool(
                "get_agent_performance_data",
                {
                    "time_range": "30d",
                    "intent_filter": state.current_intent,
                    "metrics": ["resolution_rate", "satisfaction_score", "handle_time"]
                },
                {"agent_type": "supervisor", "permissions": ["read_performance_data"]}
            )
            
            return {
                "similar_cases": similar_cases.get("data", []),
                "resolution_patterns": resolution_patterns,
                "agent_performance": agent_performance.get("data", {}),
                "success_predictors": await self._identify_success_predictors(similar_cases.get("data", [])),
                "optimal_routing": await self._determine_optimal_routing(resolution_patterns, agent_performance.get("data", {}))
            }
            
        except Exception as e:
            logger.warning(f"Historical performance analysis failed: {e}")
            return {"error": str(e), "fallback_analysis": True}
    
    async def _analyze_system_state(self, state: AgentState) -> Dict[str, Any]:
        """Analyze current system state and capacity"""
        try:
            # Get system metrics
            system_metrics = await self.tool_registry.execute_tool(
                "get_system_metrics",
                {
                    "metrics": [
                        "agent_availability",
                        "queue_lengths", 
                        "response_times",
                        "error_rates",
                        "resource_utilization"
                    ]
                },
                {"agent_type": "supervisor", "permissions": ["read_system_metrics"]}
            )
            
            # Calculate capacity and load
            capacity_analysis = await self._analyze_capacity(system_metrics.get("data", {}))
            
            # Check for system issues
            system_health = await self._check_system_health(system_metrics.get("data", {}))
            
            return {
                "system_metrics": system_metrics.get("data", {}),
                "capacity_analysis": capacity_analysis,
                "system_health": system_health,
                "load_distribution": await self._analyze_load_distribution(system_metrics.get("data", {})),
                "bottlenecks": await self._identify_bottlenecks(system_metrics.get("data", {}))
            }
            
        except Exception as e:
            logger.warning(f"System state analysis failed: {e}")
            return {"error": str(e), "fallback_analysis": True}
    
    async def _assess_risks(self, state: AgentState) -> Dict[str, Any]:
        """Comprehensive risk assessment"""
        risks = {}
        
        # SLA breach risk
        sla_risk = await self._calculate_sla_risk(state)
        risks["sla_breach"] = sla_risk
        
        # Customer satisfaction risk
        satisfaction_risk = await self._calculate_satisfaction_risk(state)
        risks["customer_satisfaction"] = satisfaction_risk
        
        # Escalation risk
        escalation_risk = await self._calculate_escalation_risk(state)
        risks["escalation"] = escalation_risk
        
        # Business impact risk
        business_risk = await self._calculate_business_risk(state)
        risks["business_impact"] = business_risk
        
        # Compliance risk
        compliance_risk = await self._calculate_compliance_risk(state)
        risks["compliance"] = compliance_risk
        
        # Overall risk score
        risks["overall_risk_score"] = await self._calculate_overall_risk_score(risks)
        
        return risks
    
    async def _make_strategic_decision(
        self, 
        state: AgentState, 
        situation_analysis: Dict[str, Any],
        performance_impact: Dict[str, Any]
    ) -> SupervisorDecision:
        """
        Make strategic decision based on comprehensive analysis
        """
        logger.info(f"Making strategic decision for conversation {state.conversation_id}")
        
        # Decision matrix based on multiple factors
        decision_factors = {
            "escalation_required": await self._should_escalate_to_human(state, situation_analysis),
            "retry_with_optimization": await self._should_retry_with_optimization(state, situation_analysis),
            "exception_handling_needed": await self._needs_exception_handling(state, situation_analysis),
            "callback_scheduling": await self._should_schedule_callback(state, situation_analysis),
            "manager_review_needed": await self._needs_manager_review(state, situation_analysis),
            "can_resolve_directly": await self._can_resolve_directly(state, situation_analysis)
        }
        
        # Apply decision logic with priority order
        if decision_factors["escalation_required"]:
            return SupervisorDecision.ESCALATE_TO_HUMAN
        
        if decision_factors["can_resolve_directly"]:
            return SupervisorDecision.MARK_RESOLVED
        
        if decision_factors["manager_review_needed"]:
            return SupervisorDecision.REQUEST_MANAGER_REVIEW
        
        if decision_factors["exception_handling_needed"]:
            return SupervisorDecision.APPLY_EXCEPTION_HANDLING
        
        if decision_factors["callback_scheduling"]:
            return SupervisorDecision.SCHEDULE_CALLBACK
        
        if decision_factors["retry_with_optimization"]:
            return SupervisorDecision.RETRY_WITH_OPTIMIZATION
        
        # Default to agent assignment with optimization
        return SupervisorDecision.ASSIGN_AGENT
    
    async def _execute_supervisor_decision(
        self,
        decision: SupervisorDecision,
        state: AgentState,
        situation_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the supervisor decision with appropriate actions"""
        
        execution_handlers = {
            SupervisorDecision.ASSIGN_AGENT: self._execute_agent_assignment,
            SupervisorDecision.ESCALATE_TO_HUMAN: self._execute_human_escalation,
            SupervisorDecision.RETRY_WITH_OPTIMIZATION: self._execute_optimized_retry,
            SupervisorDecision.APPLY_EXCEPTION_HANDLING: self._execute_exception_handling,
            SupervisorDecision.SCHEDULE_CALLBACK: self._execute_callback_scheduling,
            SupervisorDecision.MARK_RESOLVED: self._execute_resolution_marking,
            SupervisorDecision.REQUEST_MANAGER_REVIEW: self._execute_manager_review_request
        }
        
        handler = execution_handlers.get(decision)
        if handler:
            return await handler(state, situation_analysis)
        else:
            logger.error(f"Unknown supervisor decision: {decision}")
            return {"success": False, "error": f"Unknown decision: {decision}"}
    
    async def _execute_agent_assignment(
        self, 
        state: AgentState, 
        situation_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute optimized agent assignment"""
        logger.info(f"Executing agent assignment for conversation {state.conversation_id}")
        
        try:
            # Determine optimal agent based on analysis
            optimal_agent = await self._determine_optimal_agent_assignment(
                state, situation_analysis
            )
            
            # Check agent availability and capacity
            agent_availability = await self._check_agent_availability(optimal_agent)
            
            if not agent_availability["available"]:
                # Find alternative agent or queue appropriately
                alternative_assignment = await self._find_alternative_assignment(
                    state, optimal_agent, situation_analysis
                )
                optimal_agent = alternative_assignment["agent"]
            
            # Create assignment context
            assignment_context = await self._create_assignment_context(
                state, situation_analysis, optimal_agent
            )
            
            # Execute assignment
            assignment_result = await self.tool_registry.execute_tool(
                "assign_to_agent",
                {
                    "conversation_id": state.conversation_id,
                    "agent_type": optimal_agent,
                    "assignment_context": assignment_context,
                    "priority": await self._determine_assignment_priority(state)
                },
                {"agent_type": "supervisor", "permissions": ["assign_conversations"]}
            )
            
            return {
                "success": True,
                "assigned_agent": optimal_agent,
                "assignment_context": assignment_context,
                "actions_taken": ["agent_assignment", "context_transfer"],
                "tools_used": ["assign_to_agent"],
                "estimated_resolution_time": assignment_result.get("estimated_resolution_time"),
                "assignment_priority": await self._determine_assignment_priority(state)
            }
            
        except Exception as e:
            logger.error(f"Agent assignment execution failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_human_escalation(
        self, 
        state: AgentState, 
        situation_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute escalation to human agent"""
        logger.info(f"Executing human escalation for conversation {state.conversation_id}")
        
        try:
            # Determine escalation urgency and type
            escalation_type = await self._determine_escalation_type(state, situation_analysis)
            escalation_urgency = await self._determine_escalation_urgency(state, situation_analysis)
            
            # Prepare comprehensive handoff package
            handoff_package = await self._prepare_human_handoff_package(
                state, situation_analysis
            )
            
            # Find appropriate human agent
            human_agent_selection = await self._select_human_agent(
                escalation_type, escalation_urgency, state
            )
            
            # Execute escalation
            escalation_result = await self.tool_registry.execute_tool(
                "escalate_ticket",
                {
                    "conversation_id": state.conversation_id,
                    "escalation_type": escalation_type,
                    "urgency": escalation_urgency,
                    "human_agent": human_agent_selection,
                    "handoff_package": handoff_package,
                    "escalation_reason": await self._determine_primary_escalation_reason(state)
                },
                {"agent_type": "supervisor", "permissions": ["escalate_to_human"]}
            )
            
            # Notify management if required
            if escalation_urgency == "critical" or state.customer.tier == CustomerTier.PLATINUM:
                await self._notify_management_of_escalation(state, escalation_result)
            
            return {
                "success": True,
                "escalation_type": escalation_type,
                "urgency": escalation_urgency,
                "human_agent": human_agent_selection,
                "handoff_package": handoff_package,
                "actions_taken": ["human_escalation", "handoff_preparation", "management_notification"],
                "tools_used": ["escalate_ticket", "transfer_to_human_agent"],
                "escalation_required": True,
                "human_handoff": True,
                "estimated_response_time": escalation_result.get("estimated_response_time")
            }
            
        except Exception as e:
            logger.error(f"Human escalation execution failed: {e}")
            return {"success": False, "error": str(e)}
        
    async def can_handle(self, state: AgentState) -> bool:
        """
        Determine if supervisor intervention is needed based on escalation criteria
        """
        logger.info(f"Evaluating supervisor intervention for conversation {state.conversation_id}")
        
        try:
            # Check for explicit escalation conditions
            escalation_conditions = await self._check_escalation_conditions(state)
            
            # Check for performance intervention needs
            performance_intervention = await self._needs_performance_intervention(state)
            
            # Check for quality assurance requirements
            qa_requirements = await self._needs_quality_assurance(state)
            
            # Check for exception handling needs
            exception_handling = await self._needs_exception_handling_check(state)
            
            # Supervisor should handle if any condition is met
            return any([
                escalation_conditions,
                performance_intervention,
                qa_requirements,
                exception_handling
            ])
            
        except Exception as e:
            logger.error(f"Error evaluating supervisor intervention: {e}")
            # Default to supervisor handling in case of evaluation errors
            return True
    
    async def _check_escalation_conditions(self, state: AgentState) -> bool:
        """Check if standard escalation conditions are met"""
        # Multiple failed resolution attempts
        if len(state.resolution_attempts) >= self.performance_thresholds["max_resolution_attempts"]:
            return True
        
        # Low confidence scores
        if state.confidence_score < self.performance_thresholds["min_confidence_score"]:
            return True
        
        # Negative sentiment with VIP customers
        if (state.customer and 
            state.customer.tier in [CustomerTier.GOLD, CustomerTier.PLATINUM] and
            state.sentiment_score < self.performance_thresholds["critical_sentiment_threshold"]):
            return True
        
        # SLA breach risk
        if await self._is_sla_breach_risk(state):
            return True
        
        # System exceptions or errors
        if state.current_status == TicketStatus.ERROR:
            return True
        
        return False
    
    async def _needs_performance_intervention(self, state: AgentState) -> bool:
        """Check if performance intervention is needed"""
        # Check if previous agents have failed
        if len([attempt for attempt in state.resolution_attempts if not attempt.get("success", False)]) >= 2:
            return True
        
        # Check for handling time exceeding thresholds
        if state.created_at:
            elapsed_time = datetime.now() - state.created_at
            if elapsed_time > timedelta(minutes=self.performance_thresholds["max_response_time_minutes"]):
                return True
        
        # Check for repeated routing loops
        if len(set(attempt.get("agent_type", "") for attempt in state.resolution_attempts)) >= 3:
            return True
        
        return False
    
    async def _needs_quality_assurance(self, state: AgentState) -> bool:
        """Check if quality assurance intervention is needed"""
        # High-value customer interactions
        if (state.customer and 
            state.customer.tier == CustomerTier.PLATINUM and
            state.priority == Priority.HIGH):
            return True
        
        # Compliance-sensitive intents
        compliance_intents = [
            "regulatory_complaint",
            "privacy_request", 
            "data_deletion",
            "legal_inquiry",
            "accessibility_issue"
        ]
        if state.current_intent in compliance_intents:
            return True
        
        # Complex technical issues
        if state.current_intent and "technical" in state.current_intent.lower():
            complexity_indicators = len(state.context.get("technical_details", []))
            if complexity_indicators >= 3:
                return True
        
        return False
    
    async def _needs_exception_handling_check(self, state: AgentState) -> bool:
        """Check if exception handling is needed"""
        # System-level exceptions
        if "exception" in state.context.get("error_type", "").lower():
            return True
        
        # Unusual customer behavior patterns
        if state.context.get("unusual_pattern_detected", False):
            return True
        
        # Business rule violations
        if state.context.get("business_rule_violation", False):
            return True
        
        return False
    



    async def _calculate_satisfaction_risk(self, state: AgentState) -> float:
        """Calculate customer satisfaction risk"""
        try:
            # Check sentiment score
            sentiment_risk = 0.0
            if state.sentiment_score < 0.3:
                sentiment_risk = 0.8
            elif state.sentiment_score < 0.5:
                sentiment_risk = 0.4
            
            # Check number of resolution attempts
            attempt_risk = min(len(state.resolution_attempts) * 0.2, 1.0)
            
            # Combine risks
            return min(sentiment_risk + attempt_risk, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating satisfaction risk: {e}")
            return 0.0

    async def _calculate_escalation_risk(self, state: AgentState) -> float:
        """Calculate escalation risk"""
        try:
            risk_factors = []
            
            # Failed resolution attempts
            if len(state.resolution_attempts) >= 2:
                risk_factors.append(0.6)
            
            # Low confidence scores
            if state.confidence_score < 0.5:
                risk_factors.append(0.4)
            
            # Negative sentiment
            if state.sentiment_score < 0.4:
                risk_factors.append(0.5)
            
            # VIP customer with issues
            if (state.customer and 
                state.customer.tier in [CustomerTier.GOLD, CustomerTier.PLATINUM]):
                risk_factors.append(0.3)
            
            return min(sum(risk_factors), 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating escalation risk: {e}")
            return 0.0

    async def _calculate_business_risk(self, state: AgentState) -> float:
        """Calculate business impact risk"""
        try:
            # High-value customer risk
            customer_risk = 0.0
            if state.customer and state.customer.tier == CustomerTier.PLATINUM:
                customer_risk = 0.7
            elif state.customer and state.customer.tier == CustomerTier.GOLD:
                customer_risk = 0.4
            
            # Priority-based risk - use getattr with default
            priority = getattr(state, 'priority', Priority.MEDIUM)
            priority_risk = 0.0
            if priority == Priority.HIGH:
                priority_risk = 0.6
            elif priority == Priority.MEDIUM:
                priority_risk = 0.3
            
            return min(customer_risk + priority_risk, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating business risk: {e}")
            return 0.0

    async def _calculate_compliance_risk(self, state: AgentState) -> float:
        """Calculate compliance risk"""
        try:
            # Check for compliance-related keywords in conversation
            compliance_keywords = [
                "regulatory", "compliance", "legal", "privacy", 
                "gdpr", "data protection", "security breach"
            ]
            
            # Get conversation text from available sources
            conversation_text = ""
            
            # Try to get from messages (if available)
            if hasattr(state, 'messages') and state.messages:
                conversation_text = " ".join([msg.content for msg in state.messages])
            elif hasattr(state, 'conversation_history') and state.conversation_history:
                conversation_text = " ".join([turn.message for turn in state.conversation_history])
            elif hasattr(state, 'current_message') and state.current_message:
                conversation_text = state.current_message
            
            for keyword in compliance_keywords:
                if keyword.lower() in conversation_text.lower():
                    return 0.8
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating compliance risk: {e}")
            return 0.0

    async def _calculate_overall_risk_score(self, risks: Dict[str, float]) -> float:
        """Calculate overall risk score from individual risk components"""
        try:
            # Weight different risk types
            weights = {
                "sla_breach": 0.3,
                "customer_satisfaction": 0.25,
                "escalation": 0.2,
                "business_impact": 0.15,
                "compliance": 0.1
            }
            
            total_score = 0.0
            for risk_type, score in risks.items():
                if risk_type in weights and isinstance(score, (int, float)):
                    total_score += score * weights[risk_type]
            
            return min(total_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating overall risk score: {e}")
            return 0.0

    def _get_sla_threshold(self, customer_tier) -> timedelta:
        """Get SLA threshold based on customer tier"""
        sla_thresholds = {
            CustomerTier.PLATINUM: timedelta(minutes=5),
            CustomerTier.GOLD: timedelta(minutes=10),
            CustomerTier.SILVER: timedelta(minutes=15),
            CustomerTier.BRONZE: timedelta(minutes=30)
        }
        
        return sla_thresholds.get(customer_tier, timedelta(minutes=30))


    async def _needs_performance_intervention(self, state: AgentState) -> bool:
        """Check if performance intervention is needed"""
        # Check if response times are degrading
        if len(state.resolution_attempts) > 2:
            return True
        
        # Check if confidence scores are low
        if state.confidence_score < 0.4:
            return True
        
        return False

    async def _needs_quality_assurance(self, state: AgentState) -> bool:
        """Check if quality assurance is needed"""
        # Random sampling for QA
        import random
        if random.random() < 0.05:  # 5% of conversations
            return True
        
        # VIP customers always get QA
        if (state.customer and 
            state.customer.tier in [CustomerTier.GOLD, CustomerTier.PLATINUM]):
            return True
        
        return False

    async def _needs_exception_handling_check(self, state: AgentState) -> bool:
        """Check if exception handling is needed"""
        return (
            state.current_status == TicketStatus.ERROR or
            state.error_count > 0 or
            len(state.resolution_attempts) >= 3
        )
    




    async def _analyze_escalation_patterns(self, state: AgentState) -> Dict[str, Any]:
        """Analyze escalation patterns and history"""
        try:
            escalation_analysis = {
                "previous_escalations": 0,
                "escalation_frequency": 0.0,
                "escalation_reasons": [],
                "escalation_success_rate": 0.0,
                "time_since_last_escalation": None
            }
            
            # Get escalation history from conversation context
            if hasattr(state, 'escalation_history') and state.escalation_history:
                escalation_analysis["previous_escalations"] = len(state.escalation_history)
                escalation_analysis["escalation_reasons"] = [
                    escalation.get("reason", "unknown") 
                    for escalation in state.escalation_history
                ]
            
            # Calculate escalation frequency based on agent history
            if hasattr(state, 'agent_history') and state.agent_history:
                total_agents = len(state.agent_history)
                escalation_count = sum(1 for agent in state.agent_history if agent.get("escalated", False))
                escalation_analysis["escalation_frequency"] = escalation_count / total_agents if total_agents > 0 else 0.0
            
            # Analyze patterns
            escalation_analysis["risk_indicators"] = await self._identify_escalation_risk_indicators(state)
            
            return escalation_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing escalation patterns: {e}")
            return {
                "previous_escalations": 0,
                "escalation_frequency": 0.0,
                "escalation_reasons": [],
                "escalation_success_rate": 0.0,
                "risk_indicators": []
            }

    async def _identify_escalation_risk_indicators(self, state: AgentState) -> List[str]:
        """Identify indicators that suggest escalation risk"""
        indicators = []
        
        try:
            # Check for frustration keywords
            frustration_keywords = ["frustrated", "angry", "unacceptable", "terrible", "awful", "worst"]
            conversation_text = ""
            
            if hasattr(state, 'current_message') and state.current_message:
                conversation_text = state.current_message.lower()
                
            for keyword in frustration_keywords:
                if keyword in conversation_text:
                    indicators.append(f"frustration_keyword_{keyword}")
            
            # Check for repeat issues
            if hasattr(state, 'resolution_attempts') and getattr(state, 'resolution_attempts', 0) > 2:
                indicators.append("multiple_resolution_attempts")
            
            # Check for high-value customer
            if state.customer and state.customer.tier in [CustomerTier.GOLD, CustomerTier.PLATINUM]:
                indicators.append("high_value_customer")
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error identifying escalation risk indicators: {e}")
            return []
        


     




    async def _assess_performance_impact(self, state: AgentState) -> Dict[str, Any]:
        """Assess performance impact of current situation"""
        try:
            return {
                "response_time_impact": await self._calculate_response_time_impact(state),
                "resource_utilization": await self._calculate_resource_utilization(state),
                "queue_impact": await self._calculate_queue_impact(state),
                "agent_workload_impact": await self._calculate_agent_workload_impact(state),
                "system_performance_impact": await self._calculate_system_performance_impact(state)
            }
        except Exception as e:
            logger.error(f"Error assessing performance impact: {e}")
            return {"error": str(e), "fallback_assessment": True}

    async def _calculate_response_time_impact(self, state: AgentState) -> float:
        """Calculate impact on response times"""
        try:
            if hasattr(state, 'created_at') and state.created_at:
                elapsed_time = datetime.now() - state.created_at
                if elapsed_time > timedelta(minutes=10):
                    return 0.8
                elif elapsed_time > timedelta(minutes=5):
                    return 0.5
            return 0.2
        except Exception:
            return 0.0

    async def _calculate_resource_utilization(self, state: AgentState) -> float:
        """Calculate current resource utilization impact"""
        return 0.5  # Placeholder - would integrate with actual resource monitoring

    async def _calculate_queue_impact(self, state: AgentState) -> float:
        """Calculate impact on queue lengths"""
        return 0.3  # Placeholder - would integrate with queue monitoring

    async def _calculate_agent_workload_impact(self, state: AgentState) -> float:
        """Calculate impact on agent workloads"""
        return 0.4  # Placeholder

    async def _calculate_system_performance_impact(self, state: AgentState) -> float:
        """Calculate overall system performance impact"""
        return 0.3  # Placeholder

    async def _calculate_complexity_score(self, state: AgentState) -> float:
        """Calculate complexity score for the conversation"""
        try:
            complexity_factors = []
            
            # Number of resolution attempts
            complexity_factors.append(len(state.resolution_attempts) * 0.2)
            
            # Intent complexity
            complex_intents = ['technical_support', 'billing_dispute', 'compliance_request']
            if state.current_intent in complex_intents:
                complexity_factors.append(0.4)
            
            # Customer tier (higher tier = potentially more complex needs)
            if state.customer:
                tier_complexity = {
                    CustomerTier.PLATINUM: 0.4,
                    CustomerTier.GOLD: 0.3,
                    CustomerTier.SILVER: 0.2,
                    CustomerTier.BRONZE: 0.1
                }
                complexity_factors.append(tier_complexity.get(state.customer.tier, 0.1))
            
            return min(sum(complexity_factors), 1.0)
        except Exception as e:
            logger.error(f"Error calculating complexity score: {e}")
            return 0.5

    async def _determine_urgency_level(self, state: AgentState) -> str:
        """Determine urgency level"""
        try:
            urgency_score = 0.0
            
            # Priority-based urgency
            priority = getattr(state, 'priority', Priority.MEDIUM)
            if priority == Priority.HIGH:
                urgency_score += 0.6
            elif priority == Priority.MEDIUM:
                urgency_score += 0.3
            
            # Customer tier urgency
            if state.customer:
                if state.customer.tier == CustomerTier.PLATINUM:
                    urgency_score += 0.4
                elif state.customer.tier == CustomerTier.GOLD:
                    urgency_score += 0.2
            
            # Sentiment-based urgency
            if state.sentiment_score < 0.3:
                urgency_score += 0.3
            
            # Time-based urgency
            if hasattr(state, 'created_at') and state.created_at:
                elapsed_time = datetime.now() - state.created_at
                if elapsed_time > timedelta(minutes=30):
                    urgency_score += 0.4
            
            if urgency_score >= 0.8:
                return "critical"
            elif urgency_score >= 0.5:
                return "high"
            elif urgency_score >= 0.3:
                return "medium"
            else:
                return "low"
                
        except Exception as e:
            logger.error(f"Error determining urgency level: {e}")
            return "medium"

    async def _assess_business_impact(self, state: AgentState) -> Dict[str, Any]:
        """Assess business impact"""
        try:
            return {
                "customer_value_impact": await self._calculate_customer_value_impact(state),
                "revenue_impact": await self._calculate_revenue_impact(state),
                "reputation_impact": await self._calculate_reputation_impact(state),
                "compliance_impact": await self._calculate_compliance_impact(state),
                "operational_impact": await self._calculate_operational_impact(state)
            }
        except Exception as e:
            logger.error(f"Error assessing business impact: {e}")
            return {"error": str(e)}

    async def _calculate_customer_value_impact(self, state: AgentState) -> float:
        """Calculate impact on customer value"""
        if state.customer:
            tier_impact = {
                CustomerTier.PLATINUM: 0.9,
                CustomerTier.GOLD: 0.7,
                CustomerTier.SILVER: 0.4,
                CustomerTier.BRONZE: 0.2
            }
            return tier_impact.get(state.customer.tier, 0.2)
        return 0.2

    async def _calculate_revenue_impact(self, state: AgentState) -> float:
        """Calculate potential revenue impact"""
        # Placeholder - would integrate with customer value data
        return 0.3

    async def _calculate_reputation_impact(self, state: AgentState) -> float:
        """Calculate potential reputation impact"""
        if state.sentiment_score < 0.3:
            return 0.8
        elif state.sentiment_score < 0.6:
            return 0.4
        return 0.1

    async def _calculate_compliance_impact(self, state: AgentState) -> float:
        """Calculate compliance impact"""
        compliance_intents = ['privacy_request', 'data_deletion', 'compliance_inquiry']
        if state.current_intent in compliance_intents:
            return 0.9
        return 0.1

    async def _calculate_operational_impact(self, state: AgentState) -> float:
        """Calculate operational impact"""
        return min(len(state.resolution_attempts) * 0.2, 1.0)

    async def _generate_supervisor_response(
        self, 
        state: AgentState, 
        decision: SupervisorDecision, 
        execution_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive supervisor response"""
        try:
            response_templates = {
                SupervisorDecision.ESCALATE_TO_HUMAN: {
                    "message": "I understand this requires special attention. Let me connect you with one of our specialized agents who can provide the expert assistance you need.",
                    "confidence": 0.95
                },
                SupervisorDecision.ASSIGN_AGENT: {
                    "message": "I've analyzed your request and will connect you with the most suitable agent to help resolve this efficiently.",
                    "confidence": 0.85
                },
                SupervisorDecision.RETRY_WITH_OPTIMIZATION: {
                    "message": "Let me try a different approach to better address your needs.",
                    "confidence": 0.75
                },
                SupervisorDecision.SCHEDULE_CALLBACK: {
                    "message": "I'll schedule a callback at your convenience so we can give this the attention it deserves.",
                    "confidence": 0.8
                }
            }
            
            template = response_templates.get(decision, {
                "message": "Let me ensure you receive the best possible assistance.",
                "confidence": 0.7
            })
            
            return {
                "message": template["message"],
                "confidence": template["confidence"],
                "next_steps": execution_result.get("next_steps", []),
                "resolution_timeline": execution_result.get("estimated_resolution_time", "within 24 hours")
            }
            
        except Exception as e:
            logger.error(f"Error generating supervisor response: {e}")
            return {
                "message": "I'll make sure you get the help you need.",
                "confidence": 0.6
            }

    async def _update_quality_metrics(self, state: AgentState, execution_result: Dict[str, Any]) -> None:
        """Update quality metrics based on supervisor action"""
        try:
            # Update resolution accuracy
            if execution_result.get("success", False):
                self.quality_metrics["resolution_accuracy"] = min(
                    self.quality_metrics["resolution_accuracy"] + 0.1, 1.0
                )
            
            # Update escalation rate
            if execution_result.get("escalation_required", False):
                self.quality_metrics["escalation_rate"] = min(
                    self.quality_metrics["escalation_rate"] + 0.05, 1.0
                )
            
            logger.debug(f"Updated quality metrics: {self.quality_metrics}")
            
        except Exception as e:
            logger.error(f"Error updating quality metrics: {e}")

    async def _log_supervisor_action(
        self, 
        state: AgentState, 
        decision: SupervisorDecision, 
        execution_result: Dict[str, Any]
    ) -> None:
        """Log supervisor action for audit trail"""
        try:
            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "conversation_id": state.conversation_id,
                "supervisor_decision": decision.value,
                "execution_result": execution_result,
                "customer_tier": state.customer.tier.value if state.customer else "unknown",
                "urgency_level": await self._determine_urgency_level(state)
            }
            
            logger.info(f"Supervisor action logged: {audit_entry}")
            
        except Exception as e:
            logger.error(f"Error logging supervisor action: {e}")

    # Add placeholder methods for decision logic
    async def _should_escalate_to_human(self, state: AgentState, situation_analysis: Dict[str, Any]) -> bool:
        """Determine if escalation to human is needed"""
        risk_score = situation_analysis.get("risk_assessment", {}).get("overall_risk_score", 0)
        return risk_score > 0.7

    async def _should_retry_with_optimization(self, state: AgentState, situation_analysis: Dict[str, Any]) -> bool:
        """Determine if retry with optimization should be attempted"""
        return len(state.resolution_attempts) < 2 and state.confidence_score > 0.3

    async def _needs_exception_handling(self, state: AgentState, situation_analysis: Dict[str, Any]) -> bool:
        """Determine if exception handling is needed"""
        return state.current_status == TicketStatus.ERROR

    async def _should_schedule_callback(self, state: AgentState, situation_analysis: Dict[str, Any]) -> bool:
        """Determine if callback should be scheduled"""
        return False  # Placeholder

    async def _needs_manager_review(self, state: AgentState, situation_analysis: Dict[str, Any]) -> bool:
        """Determine if manager review is needed"""
        return (state.customer and 
                state.customer.tier == CustomerTier.PLATINUM and 
                len(state.resolution_attempts) > 2)

    async def _can_resolve_directly(self, state: AgentState, situation_analysis: Dict[str, Any]) -> bool:
        """Determine if supervisor can resolve directly"""
        return False  # Supervisor typically orchestrates, doesn't resolve directly

    # Add placeholder execution methods
    async def _execute_optimized_retry(self, state: AgentState, situation_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Execute optimized retry"""
        return {
            "success": True,
            "actions_taken": ["optimized_retry"],
            "next_steps": ["retry_with_enhanced_context"]
        }

    async def _execute_exception_handling(self, state: AgentState, situation_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Execute exception handling"""
        return {
            "success": True,
            "actions_taken": ["exception_handling"],
            "next_steps": ["error_recovery"]
        }

    async def _execute_callback_scheduling(self, state: AgentState, situation_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Execute callback scheduling"""
        return {
            "success": True,
            "actions_taken": ["callback_scheduled"],
            "follow_up_scheduled": True
        }

    async def _execute_resolution_marking(self, state: AgentState, situation_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Execute resolution marking"""
        return {
            "success": True,
            "actions_taken": ["marked_resolved"],
            "resolution_complete": True
        }

    async def _execute_manager_review_request(self, state: AgentState, situation_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Execute manager review request"""
        return {
            "success": True,
            "actions_taken": ["manager_review_requested"],
            "manager_review_scheduled": True
        }
    
#------------------

    async def _is_sla_breach_risk(self, state: AgentState) -> bool:
        """Check if there's a risk of SLA breach"""
        try:
            sla_risk_result = await self.tool_registry.execute_tool(
                "calculate_sla_risk",
                {
                    "conversation_id": state.conversation_id,
                    "customer_tier": state.customer.tier.value if state.customer else "bronze",
                    "priority": getattr(state, 'priority', Priority.MEDIUM).value
                },
                self.get_agent_context(state)
            )
            
            risk_score = sla_risk_result.get("data", {}).get("risk_score", 0)
            return risk_score > 0.7  # High risk threshold
            
        except Exception as e:
            logger.warning(f"SLA risk calculation failed: {e}")
            # Fallback to time-based check
            elapsed_time = None
            
            if hasattr(state, 'created_at') and state.created_at:
                elapsed_time = datetime.now() - state.created_at
            elif state.conversation_history:
                # Use first message timestamp as fallback - fix the empty iterable issue
                try:
                    message_times = [msg.timestamp for msg in state.conversation_history if hasattr(msg, 'timestamp') and msg.timestamp]
                    if message_times:  # Check if list is not empty
                        first_message_time = min(message_times)
                        elapsed_time = datetime.now() - first_message_time
                    else:
                        return False  # No valid timestamps found
                except (ValueError, AttributeError):
                    return False
            
            if elapsed_time:
                warning_threshold = timedelta(minutes=self.performance_thresholds["sla_breach_warning_minutes"])
                return elapsed_time > warning_threshold
            
            return False

    async def _handle_supervisor_error(self, state: AgentState, error: Exception) -> Dict[str, Any]:
        """Handle supervisor-specific errors - fix parameter order"""
        # Get conversation_id safely
        conversation_id = getattr(state, 'conversation_id', 'unknown')
        logger.error(f"Supervisor error for conversation {conversation_id}: {error}")
        
        try:
            # Log error details
            error_details = {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # Attempt graceful fallback
            fallback_response = {
                "success": False,
                "error": "Supervisor encountered an error",
                "fallback_action": "escalate_to_human",
                "message": "I apologize, but I'm experiencing a technical issue. Let me connect you with a human agent who can assist you better.",
                "next_action": "escalate_to_human",
                "error_details": error_details,
                "confidence": 0.0,
                "escalation_required": True,
                "human_handoff": True
            }
            
            # Update state safely
            if hasattr(state, 'current_status'):
                state.current_status = TicketStatus.ERROR
            if hasattr(state, 'error_count'):
                state.error_count += 1
            else:
                state.error_count = 1
            
            return fallback_response
            
        except Exception as fallback_error:
            logger.error(f"Error in supervisor error handler: {fallback_error}")
            return {
                "success": False,
                "error": "Critical supervisor error",
                "message": "I apologize for the technical difficulties. Let me escalate this to a human agent.",
                "next_action": "escalate_to_human",
                "confidence": 0.0,
                "escalation_required": True,
                "human_handoff": True
            }

    async def _calculate_sla_risk(self, state: AgentState) -> float:
        """Calculate SLA breach risk"""
        try:
            sla_risk_result = await self.tool_registry.execute_tool(
                "calculate_sla_risk",
                {
                    "conversation_id": state.conversation_id,
                    "customer_tier": state.customer.tier.value if state.customer else "bronze",
                    "priority": getattr(state, 'priority', Priority.MEDIUM).value
                },
                self.get_agent_context(state)
            )
            
            risk_score = sla_risk_result.get("data", {}).get("risk_score", 0)
            return risk_score
            
        except Exception as e:
            logger.warning(f"SLA risk calculation failed: {e}")
            # Fallback to time-based check using conversation start time
            elapsed_time = None
            
            if hasattr(state, 'created_at') and state.created_at:
                elapsed_time = datetime.now() - state.created_at
            elif state.conversation_history:
                # Use first message timestamp as fallback - fix empty iterable issue
                try:
                    message_times = [msg.timestamp for msg in state.conversation_history if hasattr(msg, 'timestamp') and msg.timestamp]
                    if message_times:  # Check if list is not empty
                        first_message_time = min(message_times)
                        elapsed_time = datetime.now() - first_message_time
                    else:
                        return 0.0  # No valid timestamps, return low risk
                except (ValueError, AttributeError):
                    return 0.0
            
            if elapsed_time:
                warning_threshold = timedelta(minutes=self.performance_thresholds["sla_breach_warning_minutes"])
                return 0.8 if elapsed_time > warning_threshold else 0.0
            
            return 0.0  # No time reference available, return low risk

