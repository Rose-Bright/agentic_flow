from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any
from datetime import datetime, timedelta

from ...models.metrics import (
    SystemMetrics,
    ConversationMetrics,
    PerformanceMetrics,
    BusinessMetrics
)
from ...services.metrics import MetricsService, get_metrics_service
from ...core.auth import get_current_user
from ...core.security import validate_metrics_access

router = APIRouter()

@router.get("/system", response_model=SystemMetrics)
async def get_system_metrics(
    current_user = Depends(get_current_user),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """Get current system metrics"""
    try:
        return await metrics_service.get_system_metrics()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/conversations", response_model=ConversationMetrics)
async def get_conversation_metrics(
    time_range: str = "24h",
    current_user = Depends(get_current_user),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """Get conversation-related metrics"""
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
            
        return await metrics_service.get_conversation_metrics(
            time_delta=time_ranges[time_range]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance_metrics(
    current_user = Depends(get_current_user),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """Get system performance metrics"""
    try:
        return await metrics_service.get_performance_metrics()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/business", response_model=BusinessMetrics)
async def get_business_metrics(
    current_user = Depends(get_current_user),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """Get business-related metrics"""
    try:
        # Validate access to business metrics
        await validate_metrics_access(current_user, "business")
        
        return await metrics_service.get_business_metrics()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/export")
async def export_metrics(
    start_date: datetime,
    end_date: datetime,
    metric_types: List[str],
    format: str = "csv",
    current_user = Depends(get_current_user),
    metrics_service: MetricsService = Depends(get_metrics_service)
):
    """Export metrics data in specified format"""
    try:
        # Validate access to metrics export
        await validate_metrics_access(current_user, "export")
        
        if format not in ["csv", "json", "excel"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported export format"
            )
            
        return await metrics_service.export_metrics(
            start_date=start_date,
            end_date=end_date,
            metric_types=metric_types,
            format=format
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )