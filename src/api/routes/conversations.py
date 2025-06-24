from fastapi import APIRouter, HTTPException, Depends, WebSocket, status
from typing import List, Optional
from datetime import datetime

from ...models.conversation import (
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
    ConversationStatus
)
from ...services.conversation import ConversationService
from ...core.auth import get_current_user
from ...core.security import validate_conversation_access

router = APIRouter()

@router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation: ConversationCreate,
    current_user = Depends(get_current_user),
    conversation_service: ConversationService = Depends()
):
    """Start a new conversation"""
    try:
        return await conversation_service.create_conversation(
            customer_id=conversation.customer_id,
            channel=conversation.channel,
            initial_message=conversation.initial_message,
            priority=conversation.priority
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: str,
    message: MessageCreate,
    current_user = Depends(get_current_user),
    conversation_service: ConversationService = Depends()
):
    """Send a message to an existing conversation"""
    try:
        # Validate access to conversation
        await validate_conversation_access(conversation_id, current_user)
        
        return await conversation_service.add_message(
            conversation_id=conversation_id,
            message=message.message,
            attachments=message.attachments
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user = Depends(get_current_user),
    conversation_service: ConversationService = Depends()
):
    """Get conversation details"""
    try:
        # Validate access to conversation
        await validate_conversation_access(conversation_id, current_user)
        
        conversation = await conversation_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        return conversation
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{conversation_id}/status", response_model=ConversationStatus)
async def get_conversation_status(
    conversation_id: str,
    current_user = Depends(get_current_user),
    conversation_service: ConversationService = Depends()
):
    """Get the current status of a conversation"""
    try:
        # Validate access to conversation
        await validate_conversation_access(conversation_id, current_user)
        
        status = await conversation_service.get_conversation_status(conversation_id)
        if not status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        return status
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.websocket("/{conversation_id}/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    conversation_id: str,
    conversation_service: ConversationService = Depends()
):
    """WebSocket endpoint for real-time conversation updates"""
    try:
        await websocket.accept()
        await conversation_service.handle_websocket_connection(
            conversation_id=conversation_id,
            websocket=websocket
        )
    except Exception as e:
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        
@router.delete("/{conversation_id}")
async def end_conversation(
    conversation_id: str,
    current_user = Depends(get_current_user),
    conversation_service: ConversationService = Depends()
):
    """End an active conversation"""
    try:
        # Validate access to conversation
        await validate_conversation_access(conversation_id, current_user)
        
        await conversation_service.end_conversation(conversation_id)
        return {"message": "Conversation ended successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )