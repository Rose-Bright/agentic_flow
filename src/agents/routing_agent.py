"""
Routing agent for initial message classification and routing
"""

import re
from typing import Dict, Any, List
import asyncio

from src.agents.base import BaseAgent, AgentMessage, AgentResponse, ConversationContext
from src.database.models import AgentType
from src.integrations.openai_client import openai_client
from src.core.logging import get_logger

logger = get_logger(__name__)


class RoutingAgent(BaseAgent):
    """Agent responsible for routing conversations to appropriate specialists"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(AgentType.ROUTING, config)
        
        # Intent patterns for quick classification
        self.intent_patterns = {
            "technical_support": [
                r"\b(not working|broken|error|bug|crash|issue|problem|technical|support)\b",
                r"\b(can't|cannot|unable|won't|will not|doesn't work)\b",
                r"\b(troubleshoot|fix|repair|resolve)\b"
            ],
            "billing": [
                r"\b(bill|billing|invoice|payment|charge|subscription|refund|credit)\b",
                r"\b(money|cost|price|fee|amount|due)\b",
                r"\b(pay|paid|paying|owe|debt)\b"
            ],
            "sales": [
                r"\b(buy|purchase|order|upgrade|downgrade|plan|pricing|quote)\b",
                r"\b(product|service|feature|demo|trial)\b",
                r"\b(interested|want|need|looking for)\b"
            ],
            "complaint": [
                r"\b(complaint|complain|dissatisfied|unhappy|angry|frustrated)\b",
                r"\b(manager|supervisor|escalate|speak to|talk to)\b",
                r"\b(terrible|awful|horrible|worst|hate)\b"
            ],
            "account": [
                r"\b(account|profile|settings|password|login|username)\b",
                r"\b(access|locked|suspended|disabled|blocked)\b",
                r"\b(update|change|modify|edit)\b"
            ]
        }
        
        # Confidence thresholds
        self.confidence_threshold = 0.7
        
    async def initialize(self) -> None:
        """Initialize routing agent"""
        logger.info("Routing agent initialized")
    
    async def cleanup(self) -> None:
        """Cleanup routing agent"""
        logger.info("Routing agent cleanup completed")
    
    async def process_message(self, message: AgentMessage, 
                            context: ConversationContext) -> AgentResponse:
        """Process message and route to appropriate agent"""
        
        # First, try pattern-based classification for speed
        intent, confidence = await self._classify_with_patterns(message.content)
        
        # If confidence is low, use AI classification
        if confidence < self.confidence_threshold:
            intent, confidence = await self._classify_with_ai(message.content, context)
        
        # Generate appropriate response
        response_message = await self._generate_routing_response(intent, confidence)
        
        # Determine next agent
        next_agent = self._get_agent_for_intent(intent)
        
        return AgentResponse(
            message=response_message,
            action="route",
            data={
                "intent": intent,
                "confidence": confidence,
                "routing_method": "pattern" if confidence >= self.confidence_threshold else "ai"
            },
            confidence=confidence,
            next_agent=next_agent
        )
    
    async def _classify_with_patterns(self, message: str) -> tuple[str, float]:
        """Classify message using regex patterns"""
        message_lower = message.lower()
        scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, message_lower))
                score += matches
            
            if score > 0:
                scores[intent] = score
        
        if not scores:
            return "general", 0.3
        
        # Get highest scoring intent
        best_intent = max(scores, key=scores.get)
        max_score = scores[best_intent]
        
        # Normalize confidence (simple heuristic)
        confidence = min(0.8, 0.4 + (max_score * 0.1))
        
        return best_intent, confidence
    
    async def _classify_with_ai(self, message: str, 
                              context: ConversationContext) -> tuple[str, float]:
        """Classify message using AI"""
        
        # Prepare context for AI
        context_info = ""
        if context.messages:
            recent_messages = context.messages[-3:]  # Last 3 messages for context
            context_info = "Recent conversation:\n"
            for msg in recent_messages:
                role = "Customer" if msg.get("role") == "user" else "Agent"
                context_info += f"{role}: {msg.get('content', '')}\n"
        
        system_prompt = """You are a customer service routing assistant. Classify the customer's message into one of these categories:

1. technical_support - Issues with products/services not working, errors, bugs
2. billing - Payment, invoicing, subscription, refund related questions
3. sales - Interest in purchasing, upgrades, product information
4. complaint - Complaints, requests for managers, escalations
5. account - Account management, login issues, profile changes
6. general - General inquiries that don't fit other categories

Return your response as JSON with "intent" and "confidence" (0.0-1.0).

Context: {context}

Customer message: {message}"""
        
        try:
            response = await openai_client.generate_completion(
                messages=[{
                    "role": "system",
                    "content": system_prompt.format(
                        context=context_info,
                        message=message
                    )
                }],
                model="gpt-3.5-turbo",
                temperature=0.1,
                max_tokens=100
            )
            
            # Parse JSON response
            import json
            result = json.loads(response)
            return result.get("intent", "general"), result.get("confidence", 0.5)
        
        except Exception as e:
            logger.error(f"AI classification failed: {e}")
            return "general", 0.3
    
    async def _generate_routing_response(self, intent: str, confidence: float) -> str:
        """Generate appropriate routing response"""
        
        routing_messages = {
            "technical_support": [
                "I can help you with technical issues. Let me connect you with our technical support team.",
                "I understand you're experiencing a technical problem. I'll get our technical team to assist you.",
                "Technical issues can be frustrating. Let me route you to our specialized technical support."
            ],
            "billing": [
                "I can help with billing questions. Let me connect you with our billing specialist.",
                "For billing inquiries, I'll transfer you to our billing team who can assist you better.",
                "Let me route your billing question to our billing department."
            ],
            "sales": [
                "I'd be happy to help with information about our products and services.",
                "Let me connect you with our sales team to discuss your needs.",
                "I'll route you to our sales specialist who can provide detailed product information."
            ],
            "complaint": [
                "I understand your concern and want to ensure you receive the best service.",
                "Let me connect you with a specialist who can address your concerns properly.",
                "I'll escalate this to ensure your issue receives the attention it deserves."
            ],
            "account": [
                "I can help with account-related questions. Let me assist you.",
                "For account management, I'll connect you with our account specialists.",
                "Let me route you to our account support team."
            ],
            "general": [
                "I'm here to help. Let me connect you with the right person for your inquiry.",
                "I'll make sure you get connected to someone who can best assist you.",
                "Let me route your question to the appropriate team."
            ]
        }
        
        messages = routing_messages.get(intent, routing_messages["general"])
        
        # Select message based on confidence
        if confidence > 0.8:
            return messages[0]  # Most confident
        elif confidence > 0.6:
            return messages[1] if len(messages) > 1 else messages[0]
        else:
            return messages[-1]  # Least confident
    
    def _get_agent_for_intent(self, intent: str) -> AgentType:
        """Map intent to agent type"""
        intent_to_agent = {
            "technical_support": AgentType.TECHNICAL_SUPPORT,
            "billing": AgentType.BILLING,
            "sales": AgentType.SALES,
            "complaint": AgentType.ESCALATION,
            "account": AgentType.CUSTOMER_SERVICE,
            "general": AgentType.CUSTOMER_SERVICE
        }
        
        return intent_to_agent.get(intent, AgentType.CUSTOMER_SERVICE)