from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator

class ToolCategory(str, Enum):
    CUSTOMER = "customer"
    TECHNICAL = "technical"
    BILLING = "billing"
    KNOWLEDGE = "knowledge"
    DIAGNOSTIC = "diagnostic"
    ANALYTICS = "analytics"
    SYSTEM = "system"

class ToolPermission(BaseModel):
    """Model for tool access permissions"""
    tool_name: str = Field(..., description="Tool identifier")
    allowed_roles: List[str] = Field(..., description="Roles allowed to use this tool")
    requires_approval: bool = Field(default=False, description="Whether tool requires approval")
    approval_roles: Optional[List[str]] = Field(None, description="Roles that can approve tool use")
    rate_limit: Optional[int] = Field(None, description="Maximum uses per minute")
    audit_level: str = Field(default="standard", description="Level of auditing required")
    restrictions: Dict[str, Any] = Field(default={}, description="Additional restrictions")

class ToolMetadata(BaseModel):
    """Model for tool metadata"""
    name: str = Field(..., description="Tool name")
    category: ToolCategory = Field(..., description="Tool category")
    description: str = Field(..., description="Tool description")
    version: str = Field(..., description="Tool version")
    parameters: Dict[str, Dict[str, Any]] = Field(..., description="Tool parameters specification")
    return_type: Dict[str, Any] = Field(..., description="Tool return type specification")
    timeout: int = Field(default=30, description="Tool execution timeout in seconds")
    retry_config: Dict[str, Any] = Field(default={}, description="Retry configuration")
    required_permissions: List[str] = Field(default=[], description="Required permissions")
    documentation_url: Optional[str] = Field(None, description="Link to tool documentation")

class ToolExecutionContext(BaseModel):
    """Model for tool execution context"""
    conversation_id: str = Field(..., description="Conversation identifier")
    agent_id: str = Field(..., description="Agent identifier")
    agent_type: str = Field(..., description="Agent type")
    customer_id: str = Field(..., description="Customer identifier")
    execution_id: str = Field(..., description="Unique execution identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Execution timestamp")
    metadata: Dict[str, Any] = Field(default={}, description="Additional context")

class ToolExecutionRequest(BaseModel):
    """Model for tool execution request"""
    tool_name: str = Field(..., description="Name of the tool to execute")
    parameters: Dict[str, Any] = Field(..., description="Tool parameters")
    agent_context: ToolExecutionContext = Field(..., description="Execution context")
    timeout: Optional[int] = Field(None, description="Custom timeout in seconds")
    async_execution: bool = Field(default=False, description="Whether to execute asynchronously")
    idempotency_key: Optional[str] = Field(None, description="Idempotency key for retries")

class ToolExecutionResult(BaseModel):
    """Model for tool execution result"""
    execution_id: str = Field(..., description="Execution identifier")
    tool_name: str = Field(..., description="Tool name")
    status: str = Field(..., description="Execution status")
    result: Optional[Dict[str, Any]] = Field(None, description="Execution result")
    error: Optional[Dict[str, Any]] = Field(None, description="Error details if failed")
    start_time: datetime = Field(..., description="Execution start time")
    end_time: datetime = Field(..., description="Execution end time")
    duration_ms: float = Field(..., description="Execution duration in milliseconds")
    metadata: Dict[str, Any] = Field(default={}, description="Additional execution metadata")

    @validator('error', always=True)
    def check_result_or_error(cls, v, values):
        """Validate that either result or error is present, but not both"""
        if 'result' in values and values['result'] is not None and v is not None:
            raise ValueError('Cannot have both result and error')
        if 'result' in values and values['result'] is None and v is None:
            raise ValueError('Must have either result or error')
        return v

class ToolExecutionLog(BaseModel):
    """Model for tool execution logging"""
    execution_id: str = Field(..., description="Execution identifier")
    tool_name: str = Field(..., description="Tool name")
    agent_id: str = Field(..., description="Agent identifier")
    conversation_id: str = Field(..., description="Conversation identifier")
    customer_id: str = Field(..., description="Customer identifier")
    parameters: Dict[str, Any] = Field(..., description="Execution parameters")
    result: Optional[Dict[str, Any]] = Field(None, description="Execution result")
    error: Optional[Dict[str, Any]] = Field(None, description="Error details if failed")
    start_time: datetime = Field(..., description="Start timestamp")
    end_time: datetime = Field(..., description="End timestamp")
    duration_ms: float = Field(..., description="Duration in milliseconds")
    status: str = Field(..., description="Execution status")
    metrics: Dict[str, Any] = Field(default={}, description="Performance metrics")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }