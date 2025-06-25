"""
Simple Agent Orchestrator for basic conversation handling
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from src.models.state import AgentState, TicketStatus, Sentiment, CustomerTier, ConversationTurn, CustomerProfile
from src.core.logging import get_logger

logger = get_logger(__name__)


class AgentOrchestrator:
    """Simple orchestrator for managing conversation flow"""
    
    def __init__(self):
        self.conversations: Dict[str, AgentState] = {}
    
    async def handle_conversation(
        self,
        customer_input: str,
        conversation_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        channel: str = "web",
        priority: str = "medium"
    ) -> AgentState:
        """Handle a conversation turn"""
        
        try:
            # Handle new conversation
            if conversation_id is None:
                conversation_id = str(uuid.uuid4())
                state = await self._create_new_conversation(
                    conversation_id=conversation_id,
                    customer_id=customer_id,
                    channel=channel,
                    priority=priority,
                    initial_message=customer_input
                )
            else:
                # Handle existing conversation
                state = self.conversations.get(conversation_id)
                if not state:
                    raise ValueError(f"Conversation {conversation_id} not found")
                
                # Add customer message to history
                customer_turn = ConversationTurn(
                    timestamp=datetime.now(),
                    speaker="customer",
                    message=customer_input
                )
                state.conversation_history.append(customer_turn)
                state.current_message = customer_input
                state.last_activity = datetime.now()
            
            # Process the message
            await self._process_message(state, customer_input)
            
            # Store updated state
            self.conversations[conversation_id] = state
            
            return state
            
        except Exception as e:
            logger.error(f"Error handling conversation: {e}")
            return self._create_error_state(conversation_id, str(e))
    
    async def get_conversation_state(self, conversation_id: str) -> Optional[AgentState]:
        """Get conversation state"""
        return self.conversations.get(conversation_id)
    
    async def _create_new_conversation(
        self,
        conversation_id: str,
        customer_id: Optional[str],
        channel: str,
        priority: str,
        initial_message: str
    ) -> AgentState:
        """Create new conversation state"""
        
        customer = CustomerProfile(
            customer_id=customer_id or f"guest_{conversation_id[:8]}",
            name="Customer",
            email="customer@example.com",
            phone="",
            tier=CustomerTier.SILVER,
            account_status="active",
            registration_date=datetime.now(),
            lifetime_value=0.0
        ) if customer_id else None
        
        initial_turn = ConversationTurn(
            timestamp=datetime.now(),
            speaker="customer",
            message=initial_message
        )
        
        state = AgentState(
            session_id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            customer=customer,
            conversation_history=[initial_turn],
            current_message=initial_message,
            status=TicketStatus.NEW,
            session_start=datetime.now(),
            last_activity=datetime.now()
        )
        
        return state
    
    async def _process_message(self, state: AgentState, message: str):
        """Process customer message and generate response"""
        
        # Simple intent classification
        intent, confidence = await self._classify_intent(message)
        state.current_intent = intent
        state.intent_confidence = confidence
        
        # Determine agent type
        agent_type = await self._determine_agent_type(intent)
        state.current_agent_type = agent_type
        
        # Generate response
        response = await self._generate_response(intent, agent_type, message)
        state.current_message = response
        
        # Set confidence score
        state.confidence_score = confidence
        
        # Add agent response to history
        agent_turn = ConversationTurn(
            timestamp=datetime.now(),
            speaker="agent",
            message=response,
            intent=intent,
            confidence=confidence,
            agent_type=agent_type
        )
        state.conversation_history.append(agent_turn)
    
    async def _classify_intent(self, message: str) -> tuple[str, float]:
        """Simple intent classification"""
        message_lower = message.lower()
        
        intent_patterns = {
            "account_access": ["login", "password", "access", "account"],
            "billing_inquiry": ["bill", "charge", "payment", "invoice"],
            "technical_support": ["slow", "not working", "error", "problem"],
            "sales_inquiry": ["price", "plan", "upgrade", "buy"],
            "general_inquiry": ["help", "support", "question", "hello", "hi"]
        }
        
        best_intent = "general_inquiry"
        best_score = 0.0
        
        for intent, keywords in intent_patterns.items():
            score = sum(1 for keyword in keywords if keyword in message_lower)
            if score > best_score:
                best_score = score
                best_intent = intent
        
        confidence = min(0.9, 0.5 + (best_score * 0.1))
        return best_intent, confidence
    
    async def _determine_agent_type(self, intent: str) -> str:
        """Determine agent type based on intent"""
        agent_routing = {
            "account_access": "tier1_support",
            "billing_inquiry": "billing_agent",
            "technical_support": "tier2_technical",
            "sales_inquiry": "sales_agent",
            "general_inquiry": "tier1_support"
        }
        return agent_routing.get(intent, "tier1_support")
    
    async def _generate_response(self, intent: str, agent_type: str, message: str) -> str:
        """Generate response based on intent and agent type"""
        
        responses = {
            "account_access": "I can help you with account access issues. What specific problem are you experiencing?",
            "billing_inquiry": "I'm here to help with your billing question. What would you like to know about your account?",
            "technical_support": "I understand you're experiencing a technical issue. Can you provide more details?",
            "sales_inquiry": "I'd be happy to help you with information about our products and services. What interests you?",
            "general_inquiry": "Hello! I'm here to help you today. How can I assist you?"
        }
        
        return responses.get(intent, "Thank you for contacting us. How can I help you today?")
    
    def _create_error_state(self, conversation_id: Optional[str], error_message: str) -> AgentState:
        """Create error state"""
        return AgentState(
            session_id=str(uuid.uuid4()),
            conversation_id=conversation_id or str(uuid.uuid4()),
            current_message="I apologize, but I'm experiencing technical difficulties. Please try again.",
            current_agent_type="system",
            status=TicketStatus.NEW,
            session_start=datetime.now(),
            last_activity=datetime.now(),
            confidence_score=0.0
        )