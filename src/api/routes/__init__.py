"""API routes package initialization."""

from fastapi import APIRouter
from .conversations import router as conversation_router
from .agents import router as agent_router
from .metrics import router as metrics_router
from .tools import router as tools_router

# Create main router
router = APIRouter()

# Include all sub-routers
router.include_router(
    conversation_router,
    prefix="/conversations",
    tags=["conversations"]
)

router.include_router(
    agent_router,
    prefix="/agents", 
    tags=["agents"]
)

router.include_router(
    metrics_router,
    prefix="/metrics",
    tags=["metrics"]
)

router.include_router(
    tools_router,
    prefix="/tools",
    tags=["tools"]
)