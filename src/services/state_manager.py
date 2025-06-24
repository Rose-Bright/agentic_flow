import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from src.models.state import (
    AgentState,
    CustomerProfile,
    Ticket,
    Priority,
    CustomerTier,
    Sentiment,
    TicketStatus
)

class StateManager:
    """Manages conversation state persistence and retrieval"""
    
    def __init__(self):
        self.active_states: Dict[str, AgentState] = {}
        self.state_store = StateStore()  # Interface to persistent storage
        self.cleanup_interval = timedelta(minutes=30)
        self.last_cleanup = datetime.utcnow()
    
    async def get_or_create_state(self, conversation_id: Optional[str] = None) -> AgentState:
        """Get existing state or create new one"""
        
        # Periodic cleanup of expired states
        await self._cleanup_expired_states()
        
        if conversation_id and conversation_id in self.active_states:
            return self.active_states[conversation_id]
        
        if conversation_id:
            # Try to load from persistent storage
            saved_state = await self.state_store.load_state(conversation_id)
            if saved_state:
                self.active_states[conversation_id] = saved_state
                return saved_state
        
        # Create new state
        new_state = await self._create_new_state(conversation_id)
        self.active_states[new_state.conversation_id] = new_state
        
        return new_state
    
    async def update_state(self, state: AgentState):
        """Update state in both memory and persistent storage"""
        state.last_activity = datetime.utcnow()
        self.active_states[state.conversation_id] = state
        await self.state_store.save_state(state)
    
    async def _create_new_state(self, conversation_id: Optional[str] = None) -> AgentState:
        """Create a new conversation state"""
        new_state = AgentState(
            session_id=str(uuid.uuid4()),
            conversation_id=conversation_id or str(uuid.uuid4()),
            session_start=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
        
        # Save new state
        await self.state_store.save_state(new_state)
        
        return new_state
    
    async def _cleanup_expired_states(self):
        """Clean up expired states from memory"""
        current_time = datetime.utcnow()
        
        # Only run cleanup periodically
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        expired_states = []
        for conv_id, state in self.active_states.items():
            if current_time - state.last_activity > timedelta(minutes=state.timeout_minutes):
                expired_states.append(conv_id)
        
        for conv_id in expired_states:
            # Save final state before removing from memory
            await self.state_store.save_state(self.active_states[conv_id])
            del self.active_states[conv_id]
        
        self.last_cleanup = current_time

class StateStore:
    """Handles persistent storage of conversation states"""
    
    async def save_state(self, state: AgentState):
        """Save state to persistent storage"""
        # TODO: Implement actual persistence logic (e.g., Redis + PostgreSQL)
        pass
    
    async def load_state(self, conversation_id: str) -> Optional[AgentState]:
        """Load state from persistent storage"""
        # TODO: Implement actual loading logic
        return None
    
    async def list_recent_states(self, hours: int = 24) -> Dict[str, AgentState]:
        """List recent conversation states"""
        # TODO: Implement actual query logic
        return {}
    
    async def get_customer_states(self, customer_id: str) -> Dict[str, AgentState]:
        """Get all conversation states for a customer"""
        # TODO: Implement actual query logic
        return {}