"""
Main application entry point for Contact Center Agentic Flow System
"""

import sys
import os

# Add the root directory to Python path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root_dir)

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
from src.core.langgraph_integration import get_langgraph_integration, cleanup_langgraph_integration


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with LangGraph integration"""
    settings = get_settings()
    
    # Setup logging
    setup_logging(settings.log_level)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Contact Center Agentic Flow System...")
    
    try:
        # Initialize database
        logger.info("Initializing database...")
        await init_database()
        
        # Initialize LangGraph integration
        logger.info("Initializing LangGraph integration...")
        integration = await get_langgraph_integration()
        app.state.langgraph_integration = integration
        
        # Verify system health
        health_status = await integration.health_check()
        if health_status["status"] != "healthy":
            logger.warning(f"System health check shows: {health_status['status']}")
        else:
            logger.info("System health check passed")
        
        logger.info("Application startup complete")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    
    finally:
        # Cleanup
        logger.info("Application shutdown...")
        try:
            await cleanup_langgraph_integration()
            logger.info("LangGraph integration cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title="Contact Center Agentic Flow System",
        description="An intelligent, multi-agent contact center system built with LangGraph and Vertex AI",
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
    """Enhanced health check endpoint with LangGraph integration status"""
    try:
        # Basic health info
        health_info = {
            "status": "healthy",
            "version": "1.0.0",
            "service": "contact-center-agentic-flow",
            "timestamp": "2024-01-01T00:00:00Z"  # This would be actual timestamp
        }
        
        # Check LangGraph integration if available
        if hasattr(app.state, 'langgraph_integration'):
            langgraph_health = await app.state.langgraph_integration.health_check()
            health_info["langgraph"] = langgraph_health
        else:
            health_info["langgraph"] = {"status": "not_initialized"}
        
        # Determine overall status
        if health_info.get("langgraph", {}).get("status") == "error":
            health_info["status"] = "degraded"
        
        return health_info
        
    except Exception as e:
        return {
            "status": "error",
            "version": "1.0.0",
            "service": "contact-center-agentic-flow",
            "error": str(e)
        }


@app.get("/metrics")
async def get_metrics():
    """Get system performance metrics"""
    try:
        if hasattr(app.state, 'langgraph_integration'):
            metrics = await app.state.langgraph_integration.get_performance_metrics()
            return {
                "status": "success",
                "metrics": metrics
            }
        else:
            return {
                "status": "error",
                "error": "LangGraph integration not available"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
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