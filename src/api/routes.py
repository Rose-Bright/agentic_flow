from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from src.models.state import AgentState, ConversationTurn
from src.services.simple_orchestrator import AgentOrchestrator
from .auth import (
    oauth2_scheme,
    Token,
    authenticate_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    fake_users_db,
)
from fastapi.security import OAuth2PasswordRequestForm

class ConversationRequest(BaseModel):
    customer_id: str
    channel: str = Field(..., pattern="^(web|phone|email|mobile|social)$")
    initial_message: str
    priority: str = Field(..., pattern="^(low|medium|high|critical)$")

class MessageRequest(BaseModel):
    content: str
    attachments: Optional[List[dict]] = None

class ConversationResponse(BaseModel):
    conversation_id: str
    agent_type: str
    response: str
    next_steps: Optional[List[str]] = None
    created_at: datetime

class MessageResponse(BaseModel):
    message_id: str
    content: str
    agent_type: str
    timestamp: datetime
    confidence_score: float

# Create the main router
router = APIRouter()

@router.post("/conversations", response_model=ConversationResponse)
async def start_conversation(
    request: ConversationRequest,
    token: str = Depends(oauth2_scheme)
) -> ConversationResponse:
    """Start a new conversation with the support system"""
    try:
        orchestrator = AgentOrchestrator()
        state = await orchestrator.handle_conversation(
            customer_input=request.initial_message,
            conversation_id=None,
            customer_id=request.customer_id,
            channel=request.channel,
            priority=request.priority
        )

        return ConversationResponse(
            conversation_id=state.conversation_id,
            agent_type=state.current_agent_type,
            response=state.current_message or "Hello! I'm here to help you today.",
            next_steps=[state.next_action] if state.next_action else None,
            created_at=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start conversation: {str(e)}"
        )

@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: str,
    message: MessageRequest,
    token: str = Depends(oauth2_scheme)
) -> MessageResponse:
    """Send a message to an existing conversation"""
    try:
        orchestrator = AgentOrchestrator()
        state = await orchestrator.handle_conversation(
            customer_input=message.content,
            conversation_id=conversation_id
        )

        return MessageResponse(
            message_id=f"{conversation_id}_{len(state.conversation_history)}",
            content=state.current_message or "I understand your message. Let me help you with that.",
            agent_type=state.current_agent_type,
            timestamp=datetime.utcnow(),
            confidence_score=state.confidence_score
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )

@router.get("/conversations/{conversation_id}/state", response_model=AgentState)
async def get_conversation_state(
    conversation_id: str,
    token: str = Depends(oauth2_scheme)
) -> AgentState:
    """Get the current state of a conversation"""
    try:
        orchestrator = AgentOrchestrator()
        state = await orchestrator.get_conversation_state(conversation_id)
        if not state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        return state
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation state: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "service": "contact-center-api"
    }