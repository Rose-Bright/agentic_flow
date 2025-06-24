from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any

from ...models.tools import (
    ToolExecutionRequest,
    ToolExecutionResponse,
    ToolMetadata,
    ToolPermission
)
from ...services.tools import ToolsService
from ...core.auth import get_current_user
from ...core.security import validate_tool_access

router = APIRouter()

@router.post("/execute", response_model=ToolExecutionResponse)
async def execute_tool(
    execution_request: ToolExecutionRequest,
    current_user = Depends(get_current_user),
    tools_service: ToolsService = Depends()
):
    """Execute a specific tool"""
    try:
        # Validate tool access
        await validate_tool_access(
            tool_name=execution_request.tool_name,
            user=current_user
        )
        
        return await tools_service.execute_tool(
            tool_name=execution_request.tool_name,
            parameters=execution_request.parameters,
            agent_context=execution_request.agent_context
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/list", response_model=List[ToolMetadata])
async def list_available_tools(
    current_user = Depends(get_current_user),
    tools_service: ToolsService = Depends()
):
    """List all available tools and their metadata"""
    try:
        return await tools_service.list_tools()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{tool_name}/permissions", response_model=ToolPermission)
async def get_tool_permissions(
    tool_name: str,
    current_user = Depends(get_current_user),
    tools_service: ToolsService = Depends()
):
    """Get permissions for a specific tool"""
    try:
        permissions = await tools_service.get_tool_permissions(tool_name)
        if not permissions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tool not found"
            )
        return permissions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{tool_name}/metadata", response_model=ToolMetadata)
async def get_tool_metadata(
    tool_name: str,
    current_user = Depends(get_current_user),
    tools_service: ToolsService = Depends()
):
    """Get metadata for a specific tool"""
    try:
        metadata = await tools_service.get_tool_metadata(tool_name)
        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tool not found"
            )
        return metadata
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{tool_name}/validate")
async def validate_tool_parameters(
    tool_name: str,
    parameters: Dict[str, Any],
    current_user = Depends(get_current_user),
    tools_service: ToolsService = Depends()
):
    """Validate parameters for a tool without executing it"""
    try:
        validation_result = await tools_service.validate_tool_parameters(
            tool_name=tool_name,
            parameters=parameters
        )
        return {"valid": validation_result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )