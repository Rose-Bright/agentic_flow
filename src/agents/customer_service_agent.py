"""
Customer service agent for general inquiries and support
"""

from typing import Dict, Any, List
import asyncio
from datetime import datetime

from src.agents.base import BaseAgent, AgentMessage, AgentResponse, ConversationContext
from src.database.models import AgentType
from src.integrations.openai_client import openai_client
from src.integrations.knowledge_base import knowledge_base
from src.core.logging import get_logger

logger = get_logger(__name__)


class CustomerServiceAgent(BaseAgent):
    """General customer service agent for handling common inquiries"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(AgentType.CUSTOMER_SERVICE, config)
        
        # Agent personality and behavior settings
        self.personality = {
            "tone": "friendly and professional",
            "empathy_level": "high",
            "formality": "casual-professional",
            "proactive": True
        }
        
        # Common responses for frequent questions
        self.quick_responses = {
            "greeting": [
                "Hello! I'm here to help you today. What can I assist you with?",
                "Hi there! How can I make your day better?",
                "Welcome! I'm ready to help with any questions you have."
            ],
            "thanks": [
                "You're very welcome! Is there anything else I can help you with?",
                "Happy to help! Let me know if you need anything else.",
                "My pleasure! Feel free to reach out if you have more questions."
            ],
            "goodbye": [
                "Thank you for contacting us! Have a wonderful day!",
                "It was great helping you today. Take care!",
                "Have a fantastic day! We're always here if you need us."
            ]
        }
        
        # Escalation triggers
        self.escalation_keywords = [
            "manager", "supervisor", "escalate", "complaint", "legal",
            "lawyer", "sue", "terrible", "awful", "worst", "hate"
        ]
    
    async def initialize(self) -> None:
        """Initialize customer service agent"""
        logger.info("Customer service agent initialized")
    
    async def cleanup(self) -> None:
        """Cleanup customer service agent"""
        logger.info("Customer service agent cleanup completed")
    
    async def process_message(self, message: AgentMessage, 
                            context: ConversationContext) -> AgentResponse:
        """Process customer message and provide appropriate response"""
        
        # Check for quick responses first
        quick_response = await self._check_quick_responses(message.content)
        if quick_response:
            return AgentResponse(
                message=quick_response,
                action="quick_response",
                confidence=0.9
            )
        
        # Check if this needs escalation
        should_escalate = await self._check_escalation_triggers(message.content, context)
        if should_escalate:
            return await self._handle_escalation(message, context)
        
        # Search knowledge base for relevant information
        kb_results = await self._search_knowledge_base(message.content)
        
        # Generate AI response with context
        response_text = await self._generate_ai_response(message, context, kb_results)
        
        # Determine confidence based on knowledge base match
        confidence = self._calculate_confidence(kb_results, response_text)
        
        return AgentResponse(
            message=response_text,
            action="respond",
            data={
                "kb_results_count": len(kb_results),
                "response_length": len(response_text),
                "personality_applied": True
            },
            confidence=confidence,
            should_escalate=confidence < 0.6
        )
    
    async def _check_quick_responses(self, message: str) -> str:
        """Check if message matches quick response patterns"""
        message_lower = message.lower().strip()
        
        # Greeting patterns
        if any(word in message_lower for word in ["hello", "hi", "hey", "good morning", "good afternoon"]):
            if len(message_lower.split()) <= 3:  # Short greeting
                return self.quick_responses["greeting"][0]
        
        # Thank you patterns
        if any(phrase in message_lower for phrase in ["thank you", "thanks", "appreciate"]):
            if len(message_lower.split()) <= 5:  # Short thanks
                return self.quick_responses["thanks"][0]
        
        # Goodbye patterns
        if any(word in message_lower for word in ["bye", "goodbye", "see you", "later"]):
            if len(message_lower.split()) <= 3:  # Short goodbye
                return self.quick_responses["goodbye"][0]
        
        return None
    
    async def _check_escalation_triggers(self, message: str, 
                                       context: ConversationContext) -> bool:
        """Check if message contains escalation triggers"""
        message_lower = message.lower()
        
        # Check for escalation keywords
        for keyword in self.escalation_keywords:
            if keyword in message_lower:
                return True
        
        # Check conversation length and sentiment
        if len(context.messages) > 8 and context.sentiment == "negative":
            return True
        
        # Check for repeated issues
        recent_messages = context.messages[-4:] if len(context.messages) >= 4 else context.messages
        similar_issues = sum(1 for msg in recent_messages if "problem" in msg.get("content", "").lower())
        if similar_issues >= 2:
            return True
        
        return False
    
    async def _handle_escalation(self, message: AgentMessage, 
                               context: ConversationContext) -> AgentResponse:
        """Handle escalation request"""
        escalation_messages = [
            "I understand your frustration, and I want to make sure you get the best possible help. Let me connect you with a senior specialist who can address your concerns.",
            "I hear you, and I want to ensure your issue gets the attention it deserves. I'm transferring you to someone who can provide more specialized assistance.",
            "I completely understand your situation. Let me escalate this to our specialized team who can better address your needs."
        ]
        
        return AgentResponse(
            message=escalation_messages[0],
            action="escalate",
            should_escalate=True,
            escalation_reason="Customer request or frustration detected",
            next_agent=AgentType.ESCALATION,
            confidence=0.9
        )
    
    async def _search_knowledge_base(self, query: str) -> List[Dict[str, Any]]:
        """Search knowledge base for relevant information"""
        try:
            results = await knowledge_base.search(query, limit=3)
            return results
        except Exception as e:
            logger.error(f"Knowledge base search failed: {e}")
            return []
    
    async def _generate_ai_response(self, message: AgentMessage, 
                                  context: ConversationContext,
                                  kb_results: List[Dict[str, Any]]) -> str:
        """Generate AI response using context and knowledge base"""
        
        # Prepare context information
        context_info = self._prepare_context_info(context)
        
        # Prepare knowledge base information
        kb_info = self._prepare_kb_info(kb_results)
        
        # Create system prompt
        system_prompt = f"""You are a helpful customer service representative with the following characteristics:
- Tone: {self.personality['tone']}
- Empathy level: {self.personality['empathy_level']}
- Communication style: {self.personality['formality']}
- Be proactive: {self.personality['proactive']}

Guidelines:
1. Be helpful, empathetic, and professional
2. Provide clear, actionable solutions when possible
3. Use the knowledge base information when relevant
4. Keep responses concise but thorough
5. Ask clarifying questions if needed
6. Show genuine care for the customer's experience

Context: {context_info}

Knowledge base information: {kb_info}

Customer message: {message.content}

Provide a helpful response:"""
        
        try:
            response = await openai_client.generate_completion(
                messages=[{"role": "system", "content": system_prompt}],
                model="gpt-4",
                temperature=0.7,
                max_tokens=300
            )
            return response.strip()
        
        except Exception as e:
            logger.error(f"AI response generation failed: {e}")
            return "I apologize, but I'm having trouble processing your request right now. Let me connect you with another representative who can help you better."
    
    def _prepare_context_info(self, context: ConversationContext) -> str:
        """Prepare context information for AI prompt"""
        info_parts = []
        
        # Customer information
        if context.customer_data:
            info_parts.append(f"Customer: {context.customer_data.get('name', 'Valued customer')}")
            if context.customer_data.get('tier'):
                info_parts.append(f"Customer tier: {context.customer_data['tier']}")
        
        # Conversation history
        if context.messages:
            recent_messages = context.messages[-3:]  # Last 3 messages
            info_parts.append("Recent conversation:")
            for msg in recent_messages:
                role = "Customer" if msg.get("role") == "user" else "Agent"
                content = msg.get("content", "")[:100]  # Truncate long messages
                info_parts.append(f"- {role}: {content}")
        
        # Current intent and sentiment
        if context.current_intent:
            info_parts.append(f"Current intent: {context.current_intent}")
        if context.sentiment:
            info_parts.append(f"Customer sentiment: {context.sentiment}")
        
        return "\n".join(info_parts) if info_parts else "No additional context available"
    
    def _prepare_kb_info(self, kb_results: List[Dict[str, Any]]) -> str:
        """Prepare knowledge base information for AI prompt"""
        if not kb_results:
            return "No specific knowledge base articles found for this query."
        
        info_parts = ["Relevant knowledge base articles:"]
        for i, result in enumerate(kb_results[:3], 1):  # Top 3 results
            title = result.get("title", "Unknown")
            content = result.get("content", "")[:200]  # Truncate content
            score = result.get("score", 0)
            info_parts.append(f"{i}. {title} (relevance: {score:.2f})")
            info_parts.append(f"   {content}...")
        
        return "\n".join(info_parts)
    
    def _calculate_confidence(self, kb_results: List[Dict[str, Any]], 
                            response: str) -> float:
        """Calculate confidence score for the response"""
        base_confidence = 0.7
        
        # Boost confidence if we have good knowledge base matches
        if kb_results:
            avg_score = sum(r.get("score", 0) for r in kb_results) / len(kb_results)
            kb_boost = min(0.2, avg_score * 0.3)
            base_confidence += kb_boost
        
        # Reduce confidence for very generic responses
        generic_phrases = ["I understand", "I'm sorry", "Let me help", "I apologize"]
        generic_count = sum(1 for phrase in generic_phrases if phrase.lower() in response.lower())
        if generic_count > 2:
            base_confidence -= 0.1
        
        # Ensure confidence is within bounds
        return max(0.3, min(1.0, base_confidence))