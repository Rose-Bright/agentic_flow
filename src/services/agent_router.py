from datetime import datetime
from typing import Dict, Any
from src.models.state import AgentState, CustomerTier, Priority, Sentiment, TicketStatus
from src.services.agent_orchestrator import AgentType

class AgentRouter:
    """Routes conversations to appropriate agent types based on context and rules"""
    
    def __init__(self):
        self.routing_rules = self._initialize_routing_rules()
        self.escalation_matrix = self._initialize_escalation_matrix()
    
    async def determine_agent(self, state: AgentState) -> AgentType:
        """Determine the most appropriate agent type for the current state"""
        
        # Calculate routing scores for each agent type
        scores = {}
        for agent_type in AgentType:
            scores[agent_type] = await self._calculate_routing_score(state, agent_type)
        
        # Get agent type with highest score
        selected_agent = max(scores.items(), key=lambda x: x[1])[0]
        
        return selected_agent
    
    async def determine_escalation_level(self, state: AgentState) -> AgentType:
        """Determine the appropriate escalation level based on current state"""
        
        current_agent = AgentType(state.current_agent_type)
        
        # Get next level from escalation matrix
        next_level = self.escalation_matrix.get(current_agent, [None])[0]
        
        if next_level:
            return next_level
        else:
            # Default to supervisor if no specific escalation path
            return AgentType.SUPERVISOR
    
    def _initialize_routing_rules(self) -> Dict[str, Dict[str, float]]:
        """Initialize routing rules with weights for different factors"""
        return {
            "intent_mapping": {
                "technical_support": {
                    AgentType.TIER1: 0.8,
                    AgentType.TIER2: 0.6,
                    AgentType.TIER3: 0.4
                },
                "billing_inquiry": {
                    AgentType.BILLING: 0.9,
                    AgentType.TIER1: 0.5
                },
                "sales_inquiry": {
                    AgentType.SALES: 0.9,
                    AgentType.TIER1: 0.4
                }
            },
            "customer_tier_weights": {
                CustomerTier.PLATINUM: {
                    AgentType.TIER3: 0.8,
                    AgentType.TIER2: 0.6
                },
                CustomerTier.GOLD: {
                    AgentType.TIER2: 0.7,
                    AgentType.TIER1: 0.5
                }
            },
            "priority_weights": {
                Priority.CRITICAL: {
                    AgentType.TIER3: 0.9,
                    AgentType.SUPERVISOR: 0.8
                },
                Priority.HIGH: {
                    AgentType.TIER2: 0.8,
                    AgentType.TIER3: 0.6
                }
            }
        }
    
    def _initialize_escalation_matrix(self) -> Dict[AgentType, List[AgentType]]:
        """Initialize the escalation paths for each agent type"""
        return {
            AgentType.TIER1: [AgentType.TIER2, AgentType.SUPERVISOR],
            AgentType.TIER2: [AgentType.TIER3, AgentType.SUPERVISOR],
            AgentType.TIER3: [AgentType.SUPERVISOR],
            AgentType.SALES: [AgentType.SUPERVISOR],
            AgentType.BILLING: [AgentType.SUPERVISOR],
            AgentType.SUPERVISOR: []
        }
    
    async def _calculate_routing_score(self, state: AgentState, agent_type: AgentType) -> float:
        """Calculate routing score for a specific agent type based on current state"""
        score = 0.0
        
        # Intent-based scoring
        if state.current_intent in self.routing_rules["intent_mapping"]:
            score += self.routing_rules["intent_mapping"][state.current_intent].get(
                agent_type, 0.0
            )
        
        # Customer tier-based scoring
        if state.customer and state.customer.tier in self.routing_rules["customer_tier_weights"]:
            score += self.routing_rules["customer_tier_weights"][state.customer.tier].get(
                agent_type, 0.0
            )
        
        # Priority-based scoring
        if state.ticket and state.ticket.priority in self.routing_rules["priority_weights"]:
            score += self.routing_rules["priority_weights"][state.ticket.priority].get(
                agent_type, 0.0
            )
        
        # Adjust score based on current state
        score = await self._adjust_score_for_state(score, state, agent_type)
        
        return score
    
    async def _adjust_score_for_state(
        self,
        base_score: float,
        state: AgentState,
        agent_type: AgentType
    ) -> float:
        """Adjust routing score based on current conversation state"""
        
        adjustments = 0.0
        
        # Adjust for sentiment
        if state.sentiment == Sentiment.FRUSTRATED:
            if agent_type in [AgentType.TIER3, AgentType.SUPERVISOR]:
                adjustments += 0.2
        
        # Adjust for escalation history
        if len(state.escalation_history) > 0:
            if agent_type == AgentType.SUPERVISOR:
                adjustments += 0.3
        
        # Adjust for failed resolution attempts
        if len(state.resolution_attempts) >= 2:
            if agent_type in [AgentType.TIER2, AgentType.TIER3]:
                adjustments += 0.2
        
        # Adjust for SLA risk
        if state.sla_breach_risk:
            if agent_type in [AgentType.TIER3, AgentType.SUPERVISOR]:
                adjustments += 0.4
        
        return base_score + adjustments