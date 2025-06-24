from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from src.models.state import AgentState, ConversationTurn
from src.services.agent_orchestrator import AgentOrchestrator
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from src.models.state import AgentState, ConversationTurn
from src.services.agent_orchestrator import AgentOrchestrator
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
    channel: str = Field(..., regex="^(web|phone|email|mobile|social)$")
    initial_message: str
    priority: str = Field(..., regex="^(low|medium|high|critical)$")

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

router = APIRouter()
@router.post("/conversations", response_model=ConversationResponse)
async def start_conversation(
    request: ConversationRequest,
    token: str = Depends(oauth2_scheme)
) -> ConversationResponse:
    try:
        orchestrator = AgentOrchestrator()
        state = await orchestrator.handle_conversation(
            customer_input=request.initial_message,
            conversation_id=None
        )

        return ConversationResponse(
            conversation_id=state.conversation_id,
            agent_type=state.current_agent_type,
            response=state.current_message,
            next_steps=state.next_action,
            created_at=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: str,
    message: MessageRequest,
    token: str = Depends(oauth2_scheme)
) -> MessageResponse:
    try:
        orchestrator = AgentOrchestrator()
        state = await orchestrator.handle_conversation(
            customer_input=message.content,
            conversation_id=conversation_id
        )

        return MessageResponse(
            message_id=f"{conversation_id}_{len(state.conversation_history)}",
            content=state.current_message,
            agent_type=state.current_agent_type,
            timestamp=datetime.utcnow(),
            confidence_score=state.confidence_score
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/conversations/{conversation_id}/state", response_model=AgentState)
async def get_conversation_state(
    conversation_id: str,
    token: str = Depends(oauth2_scheme)
) -> AgentState:
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
            detail=str(e)
        )
@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
