"""
Main application entry point for Contact Center Agentic Flow System
"""

import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from src.api.routes import router as api_router
from src.core.config import get_settings
from src.core.logging import setup_logging
from src.database.connection import init_database
from fastapi import FastAPI, WebSocket, HTTPException
from typing import Dict, Optional
from datetime import datetime
from src.services.agent_orchestrator import AgentOrchestrator
from src.services.performance_monitor import PerformanceMonitor
from src.models.state import AgentState


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    settings = get_settings()
    
    # Setup logging
    setup_logging(settings.log_level)
    logger = logging.getLogger(__name__)
    
    # Initialize database
    logger.info("Initializing database...")
    await init_database()
    
    # Initialize agent orchestrator
    logger.info("Initializing agent orchestrator...")
    orchestrator = AgentOrchestrator()
    await orchestrator.initialize()
    app.state.orchestrator = orchestrator
    
    logger.info("Application startup complete")
    
    yield
    
    # Cleanup
    logger.info("Application shutdown...")
    if hasattr(app.state, 'orchestrator'):
        await app.state.orchestrator.cleanup()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title="Contact Center Agentic Flow System",
        description="An intelligent, multi-agent contact center system",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )
    
    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Include routers
    app.include_router(api_router, prefix=settings.api_prefix)
    
    return app


app = create_app()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "contact-center-agentic-flow"
    }


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )