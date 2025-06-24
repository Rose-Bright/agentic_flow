"""API route definitions for the Contact Center Agentic Flow System."""

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordBearer
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

# Models for request/response
class ConversationRequest(BaseModel):
    customer_id: str
    channel: str = Field(..., regex="^(web|phone|email|mobile|social)$")
    initial_message: str
    priority: str = Field(..., regex="^(low|medium|high|critical)$")

class MessageRequest(BaseModel):
    message: str
    attachments: Optional[List[Dict[str, Any]]] = None

class ConversationResponse(BaseModel):
    conversation_id: str
    agent_type: str
    response: str
    next_steps: Optional[List[str]] = None
    created_at: datetime

class ConversationStatus(BaseModel):
    conversation_id: str
    status: str
    current_agent: str
    last_update: datetime
    resolution_progress: float

class AgentPerformanceMetrics(BaseModel):
    agent_type: str
    conversations_handled: int
    avg_response_time: float
    resolution_rate: float
    customer_satisfaction: float
    updated_at: datetime

# Create router instance
router = APIRouter(prefix="/api/v1", tags=["contact-center"])

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, conversation_id: str):
        await websocket.accept()
        self.active_connections[conversation_id] = websocket

    async def disconnect(self, conversation_id: str):
        if conversation_id in self.active_connections:
            del self.active_connections[conversation_id]

    async def send_message(self, conversation_id: str, message: dict):
        if conversation_id in self.active_connections:
            await self.active_connections[conversation_id].send_json(message)

manager = ConnectionManager()

@router.post("/conversations", response_model=ConversationResponse)
async def start_conversation(
    request: ConversationRequest,
    token: str = Depends(oauth2_scheme)
) -> ConversationResponse:
    """Start a new conversation with the AI agent system."""
    try:
        # Here you would implement:
        # 1. Validate customer ID and access
        # 2. Initialize conversation state
        # 3. Route to appropriate agent based on intent
        # 4. Generate initial response
        
        return ConversationResponse(
            conversation_id="unique_id",  # Generate actual unique ID
            agent_type="intent_classifier",
            response="Thank you for contacting us. How can I help you today?",
            next_steps=["await_customer_response"],
            created_at=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    message: MessageRequest,
    token: str = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """Send a message to an existing conversation."""
    try:
        # Here you would implement:
        # 1. Validate conversation exists
        # 2. Process message through agent system
        # 3. Generate and return response
        
        return {
            "message_id": "unique_msg_id",  # Generate actual unique ID
            "response": "Agent response to the message",
            "agent_type": "current_agent_type",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{conversation_id}/status", response_model=ConversationStatus)
async def get_conversation_status(
    conversation_id: str,
    token: str = Depends(oauth2_scheme)
) -> ConversationStatus:
    """Get the current status of a conversation."""
    try:
        return ConversationStatus(
            conversation_id=conversation_id,
            status="in_progress",
            current_agent="technical_support",
            last_update=datetime.utcnow(),
            resolution_progress=0.65
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/performance", response_model=List[AgentPerformanceMetrics])
async def get_agent_performance(
    time_range: str = "24h",
    agent_type: Optional[str] = None,
    token: str = Depends(oauth2_scheme)
) -> List[AgentPerformanceMetrics]:
    """Get performance metrics for AI agents."""
    try:
        # Here you would implement:
        # 1. Query metrics from monitoring system
        # 2. Aggregate and format data
        # 3. Apply filters based on parameters
        
        return [
            AgentPerformanceMetrics(
                agent_type="tier1_support",
                conversations_handled=150,
                avg_response_time=2.5,
                resolution_rate=0.85,
                customer_satisfaction=4.2,
                updated_at=datetime.utcnow()
            )
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    """WebSocket endpoint for real-time conversation updates."""
    try:
        await manager.connect(websocket, conversation_id)
        while True:
            try:
                # Receive and process messages
                data = await websocket.receive_text()
                
                # Process message and get response
                response = {
                    "type": "agent_response",
                    "message": f"Processing: {data}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Send response back to client
                await manager.send_message(conversation_id, response)
                
            except WebSocketDisconnect:
                await manager.disconnect(conversation_id)
                break
            
    except Exception as e:
        await manager.disconnect(conversation_id)
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint for the API."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}