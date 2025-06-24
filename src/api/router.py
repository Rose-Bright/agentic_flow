from fastapi import APIRouter
from .routes import conversations, agents, metrics, tools

# Create main API router
api_router = APIRouter()

# Include all route modules
api_router.include_router(
    conversations.router,
    prefix="/conversations",
    tags=["conversations"]
)

api_router.include_router(
    agents.router,
    prefix="/agents",
    tags=["agents"]
)

api_router.include_router(
    metrics.router,
    prefix="/metrics", 
    tags=["metrics"]
)

api_router.include_router(
    tools.router,
    prefix="/tools",
    tags=["tools"]
)