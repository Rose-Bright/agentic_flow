from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any
from datetime import datetime, timedelta

from ...models.agent import (
    AgentMetrics,
    AgentPerformance,
    AgentStatus,
    AgentType
)
from ...services.agent import AgentService
from ...core.auth import get_current_user
from ...core.security import validate_agent_access

router = APIRouter()

@router.get("/performance", response_model=List[AgentPerformance])
async def get_agent_performance(
    time_range: str = "24h",
    agent_type: AgentType = None,
    current_user = Depends(get_current_user),
    agent_service: AgentService = Depends()
):
    """Get agent performance metrics"""
    try:
        # Convert time range to timedelta
        time_ranges = {
            "1h": timedelta(hours=1),
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30)
        }
        
        if time_range not in time_ranges:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid time range"
            )
            
        return await agent_service.get_agent_performance(
            time_delta=time_ranges[time_range],
            agent_type=agent_type
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/metrics", response_model=AgentMetrics)
async def get_agent_metrics(
    agent_id: str,
    current_user = Depends(get_current_user),
    agent_service: AgentService = Depends()
):
    """Get detailed metrics for a specific agent"""
    try:
        # Validate access to agent metrics
        await validate_agent_access(agent_id, current_user)
        
        metrics = await agent_service.get_agent_metrics(agent_id)
        if not metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/status", response_model=List[AgentStatus])
async def get_agent_status(
    agent_type: AgentType = None,
    current_user = Depends(get_current_user),
    agent_service: AgentService = Depends()
):
    """Get current status of all agents or filtered by type"""
    try:
        return await agent_service.get_agent_status(agent_type)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{agent_id}/reload")
async def reload_agent(
    agent_id: str,
    current_user = Depends(get_current_user),
    agent_service: AgentService = Depends()
):
    """Reload an agent's configuration and models"""
    try:
        # Validate access to agent management
        await validate_agent_access(agent_id, current_user)
        
        await agent_service.reload_agent(agent_id)
        return {"message": "Agent reloaded successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{agent_id}/stop")
async def stop_agent(
    agent_id: str,
    current_user = Depends(get_current_user),
    agent_service: AgentService = Depends()
):
    """Stop an agent's operations"""
    try:
        # Validate access to agent management
        await validate_agent_access(agent_id, current_user)
        
        await agent_service.stop_agent(agent_id)
        return {"message": "Agent stopped successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )