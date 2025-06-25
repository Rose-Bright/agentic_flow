import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect

from ..models.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationStatus,
    MessageCreate,
    MessageResponse,
    Message,
    Priority,
    Channel,
    ConversationMetrics
)
from ..core.langgraph_integration import get_langgraph_integration
from ..database.connection import get_database
from ..core.exceptions import ConversationNotFoundError, DatabaseError

logger = logging.getLogger(__name__)

class ConversationService:
    """Service for managing customer conversations"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.logger = logger
    
    async def create_conversation(
        self,
        customer_id: str,
        channel: Channel,
        initial_message: str,
        priority: Priority = Priority.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationResponse:
        """Create a new conversation"""
        try:
            conversation_id = str(uuid.uuid4())
            current_time = datetime.utcnow()
            
            # Create conversation record
            conversation_data = {
                "id": conversation_id,
                "customer_id": customer_id,
                "channel": channel,
                "status": ConversationStatus.NEW,
                "priority": priority,
                "created_at": current_time,
                "updated_at": current_time,
                "metadata": metadata or {}
            }
            
            # Save to database
            db = await get_database()
            await self._save_conversation_to_db(db, conversation_data)
            
            # Process initial message through LangGraph
            langgraph_integration = await get_langgraph_integration()
            
            # Start conversation processing
            processing_result = await langgraph_integration.process_conversation(
                message=initial_message,
                conversation_id=conversation_id,
                customer_id=customer_id
            )
            
            # Create initial message record
            initial_msg = await self._create_message(
                conversation_id=conversation_id,
                message=initial_message,
                sender_type="customer",
                sender_id=customer_id
            )
            
            # Create response message if available
            messages = [initial_msg]
            if processing_result.get("response"):
                response_msg = await self._create_message(
                    conversation_id=conversation_id,
                    message=processing_result["response"],
                    sender_type="agent",
                    sender_id=processing_result.get("agent_id", "system"),
                    agent_type=processing_result.get("agent_type"),
                    intent=processing_result.get("intent"),
                    confidence=processing_result.get("confidence"),
                    sentiment=processing_result.get("sentiment")
                )
                messages.append(response_msg)
            
            # Update conversation status
            updated_status = ConversationStatus.IN_PROGRESS if processing_result.get("response") else ConversationStatus.NEW
            await self._update_conversation_status(db, conversation_id, updated_status)
            
            # Build response
            conversation_response = ConversationResponse(
                id=conversation_id,
                customer_id=customer_id,
                channel=channel,
                status=updated_status,
                priority=priority,
                created_at=current_time,
                updated_at=current_time,
                current_agent=processing_result.get("agent_type"),
                escalation_level=0,
                resolution_attempts=0,
                metadata=metadata or {},
                messages=messages
            )
            
            self.logger.info(f"Created conversation {conversation_id} for customer {customer_id}")
            return conversation_response
            
        except Exception as e:
            self.logger.error(f"Failed to create conversation: {str(e)}")
            raise DatabaseError(f"Failed to create conversation: {str(e)}")
    
    async def add_message(
        self,
        conversation_id: str,
        message: str,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> MessageResponse:
        """Add a message to an existing conversation"""
        try:
            # Verify conversation exists
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                raise ConversationNotFoundError(f"Conversation {conversation_id} not found")
            
            # Create customer message
            customer_msg = await self._create_message(
                conversation_id=conversation_id,
                message=message,
                sender_type="customer",
                sender_id=conversation.customer_id,
                attachments=attachments or []
            )
            
            # Process message through LangGraph
            langgraph_integration = await get_langgraph_integration()
            processing_result = await langgraph_integration.process_conversation(
                message=message,
                conversation_id=conversation_id,
                customer_id=conversation.customer_id
            )
            
            # Create agent response if available
            if processing_result.get("response"):
                agent_msg = await self._create_message(
                    conversation_id=conversation_id,
                    message=processing_result["response"],
                    sender_type="agent",
                    sender_id=processing_result.get("agent_id", "system"),
                    agent_type=processing_result.get("agent_type"),
                    intent=processing_result.get("intent"),
                    confidence=processing_result.get("confidence"),
                    sentiment=processing_result.get("sentiment")
                )
                
                # Send real-time update via WebSocket
                await self._send_websocket_update(conversation_id, agent_msg)
                
                return agent_msg
            
            return customer_msg
            
        except ConversationNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to add message to conversation {conversation_id}: {str(e)}")
            raise DatabaseError(f"Failed to add message: {str(e)}")
    
    async def get_conversation(self, conversation_id: str) -> Optional[ConversationResponse]:
        """Get conversation by ID"""
        try:
            db = await get_database()
            
            # This would typically query your database
            # For now, we'll return a basic structure
            # You'll need to implement actual database queries based on your schema
            
            query = """
            SELECT c.*, array_agg(
                json_build_object(
                    'id', m.id,
                    'message', m.message,
                    'sender_type', m.sender_type,
                    'sender_id', m.sender_id,
                    'created_at', m.created_at,
                    'agent_type', m.agent_type,
                    'intent', m.intent,
                    'confidence', m.confidence,
                    'sentiment', m.sentiment
                ) ORDER BY m.created_at
            ) as messages
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
            WHERE c.id = $1
            GROUP BY c.id
            """
            
            # This is a placeholder - implement actual database query
            # For now, return None to indicate conversation not found
            self.logger.warning(f"Database query not implemented for conversation {conversation_id}")
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get conversation {conversation_id}: {str(e)}")
            raise DatabaseError(f"Failed to get conversation: {str(e)}")
    
    async def get_conversation_status(self, conversation_id: str) -> Optional[ConversationStatus]:
        """Get the current status of a conversation"""
        try:
            conversation = await self.get_conversation(conversation_id)
            return conversation.status if conversation else None
            
        except Exception as e:
            self.logger.error(f"Failed to get status for conversation {conversation_id}: {str(e)}")
            return None
    
    async def end_conversation(self, conversation_id: str) -> bool:
        """End an active conversation"""
        try:
            db = await get_database()
            await self._update_conversation_status(
                db, 
                conversation_id, 
                ConversationStatus.CLOSED,
                ended_at=datetime.utcnow()
            )
            
            # Close WebSocket connection if active
            if conversation_id in self.active_connections:
                await self.active_connections[conversation_id].close()
                del self.active_connections[conversation_id]
            
            self.logger.info(f"Ended conversation {conversation_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to end conversation {conversation_id}: {str(e)}")
            return False
    
    async def handle_websocket_connection(self, conversation_id: str, websocket: WebSocket):
        """Handle WebSocket connection for real-time updates"""
        try:
            self.active_connections[conversation_id] = websocket
            
            while True:
                try:
                    # Keep connection alive and handle incoming messages
                    data = await websocket.receive_text()
                    
                    # Process incoming WebSocket message
                    await self._handle_websocket_message(conversation_id, data)
                    
                except WebSocketDisconnect:
                    break
                    
        except Exception as e:
            self.logger.error(f"WebSocket error for conversation {conversation_id}: {str(e)}")
        finally:
            # Clean up connection
            if conversation_id in self.active_connections:
                del self.active_connections[conversation_id]
    
    async def _create_message(
        self,
        conversation_id: str,
        message: str,
        sender_type: str,
        sender_id: str,
        attachments: Optional[List[Dict[str, Any]]] = None,
        agent_type: Optional[str] = None,
        intent: Optional[str] = None,
        confidence: Optional[float] = None,
        sentiment: Optional[str] = None
    ) -> MessageResponse:
        """Create a message record"""
        message_id = str(uuid.uuid4())
        current_time = datetime.utcnow()
        
        message_response = MessageResponse(
            id=message_id,
            conversation_id=conversation_id,
            message=message,
            sender_type=sender_type,
            sender_id=sender_id,
            created_at=current_time,
            attachments=attachments or [],
            agent_type=agent_type,
            intent=intent,
            confidence=confidence,
            sentiment=sentiment,
            entities=[]  # Would be populated by NLP processing
        )
        
        # Save to database (implement actual database save)
        await self._save_message_to_db(message_response)
        
        return message_response
    
    async def _save_conversation_to_db(self, db, conversation_data: Dict[str, Any]):
        """Save conversation to database"""
        # Implement actual database save
        # This is a placeholder for your database implementation
        self.logger.info(f"Saving conversation {conversation_data['id']} to database")
        pass
    
    async def _save_message_to_db(self, message: MessageResponse):
        """Save message to database"""
        # Implement actual database save
        # This is a placeholder for your database implementation
        self.logger.info(f"Saving message {message.id} to database")
        pass
    
    async def _update_conversation_status(
        self, 
        db, 
        conversation_id: str, 
        status: ConversationStatus,
        ended_at: Optional[datetime] = None
    ):
        """Update conversation status in database"""
        # Implement actual database update
        self.logger.info(f"Updating conversation {conversation_id} status to {status}")
        pass
    
    async def _send_websocket_update(self, conversation_id: str, message: MessageResponse):
        """Send real-time update via WebSocket"""
        if conversation_id in self.active_connections:
            try:
                websocket = self.active_connections[conversation_id]
                await websocket.send_json({
                    "type": "new_message",
                    "data": message.dict()
                })
            except Exception as e:
                self.logger.error(f"Failed to send WebSocket update: {str(e)}")
    
    async def _handle_websocket_message(self, conversation_id: str, data: str):
        """Handle incoming WebSocket message"""
        try:
            # Parse and process WebSocket message
            # This could be used for typing indicators, read receipts, etc.
            self.logger.debug(f"Received WebSocket message for conversation {conversation_id}: {data}")
        except Exception as e:
            self.logger.error(f"Failed to handle WebSocket message: {str(e)}")

    async def check_user_access(self, conversation_id: str, user) -> bool:
        """Check if user has access to a conversation"""
        try:
            # Get conversation from database
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                return False

            # Check access based on user role and conversation ownership
            # For now, implement basic access control
            # In a real implementation, you'd check:
            # - If user is the customer who created the conversation
            # - If user is an agent assigned to the conversation
            # - If user has supervisor/admin permissions

            # Basic implementation - allow access if:
            # 1. User is admin/supervisor
            # 2. User is the conversation owner
            # 3. User is assigned agent

            if hasattr(user, 'is_admin') and user.is_admin:
                return True

            if hasattr(user, 'is_supervisor') and user.is_supervisor:
                return True

            # Check if user is the customer who created the conversation
            if hasattr(user, 'customer_id') and conversation.customer_id == user.customer_id:
                return True

            # For agents, check if they're assigned to this conversation
            if hasattr(user, 'agent_id') and conversation.current_agent == user.agent_id:
                return True

            # Default to allowing access for now (you'll want to tighten this)
            return True

        except Exception as e:
            self.logger.error(f"Failed to check user access for conversation {conversation_id}: {str(e)}")
            return False

# Dependency function for FastAPI
async def get_conversation_service() -> ConversationService:
    """Get conversation service instance"""
    return ConversationService()