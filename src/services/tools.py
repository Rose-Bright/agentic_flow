"""
Tools Service - Manages tool execution and permissions
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Set
import asyncio
import json

from ..models.tools import (
    ToolMetadata,
    ToolPermission,
    ToolExecutionRequest,
    ToolExecutionResult,
    ToolExecutionStatus
)
from ..models.user import User
from ..core.config import get_settings
from ..core.logging import get_logger
from ..core.exceptions import ToolExecutionError, AuthorizationError
from .tool_registry import ToolRegistry

logger = get_logger(__name__)


class ToolsService:
    """Service for managing tool execution and permissions"""
    
    def __init__(self):
        self.settings = get_settings()
        self.tool_registry = ToolRegistry()
        self.tool_permissions: Dict[str, ToolPermission] = {}
        self.execution_history: List[ToolExecutionResult] = []
        self.initialized = False
    
    async def initialize(self):
        """Initialize the tools service"""
        if self.initialized:
            return
        
        logger.info("Initializing Tools Service...")
        
        try:
            # Initialize tool registry
            await self.tool_registry.initialize()
            
            # Load tool permissions
            await self._load_tool_permissions()
            
            self.initialized = True
            logger.info("Tools Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Tools Service: {e}")
            raise
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        user: User,
        execution_context: Optional[Dict[str, Any]] = None
    ) -> ToolExecutionResult:
        """Execute a tool with the given parameters"""
        execution_id = f"exec_{int(datetime.utcnow().timestamp() * 1000)}"
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Executing tool {tool_name} with execution ID {execution_id}")
            
            # Validate tool exists
            if not await self.tool_registry.has_tool(tool_name):
                raise ToolExecutionError(f"Tool '{tool_name}' not found")
            
            # Check permissions
            if not await self._check_tool_permissions(tool_name, user):
                raise AuthorizationError(f"Insufficient permissions to execute tool '{tool_name}'")
            
            # Validate parameters
            validation_result = await self.validate_tool_parameters(tool_name, parameters)
            if not validation_result["valid"]:
                raise ToolExecutionError(f"Invalid parameters: {validation_result['errors']}")
            
            # Execute the tool
            result = await self.tool_registry.execute_tool(
                tool_name=tool_name,
                parameters=parameters,
                agent_context=execution_context or {}
            )
            
            # Create execution result
            execution_result = ToolExecutionResult(
                execution_id=execution_id,
                tool_name=tool_name,
                parameters=parameters,
                result=result,
                status=ToolExecutionStatus.SUCCESS,
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
                timestamp=datetime.utcnow(),
                user_id=user.id,
                metadata={
                    "execution_context": execution_context,
                    "user_roles": user.roles,
                    "success": True
                }
            )
            
            # Store execution history
            self.execution_history.append(execution_result)
            
            # Log successful execution
            await self._log_tool_execution(execution_result)
            
            logger.info(f"Tool {tool_name} executed successfully (ID: {execution_id})")
            return execution_result
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            
            # Create error result
            error_result = ToolExecutionResult(
                execution_id=execution_id,
                tool_name=tool_name,
                parameters=parameters,
                result=None,
                status=ToolExecutionStatus.ERROR,
                execution_time=(datetime.utcnow() - start_time).total_seconds(),
                timestamp=datetime.utcnow(),
                user_id=user.id,
                error=str(e),
                metadata={
                    "execution_context": execution_context,
                    "user_roles": user.roles,
                    "success": False,
                    "error_type": type(e).__name__
                }
            )
            
            # Store execution history
            self.execution_history.append(error_result)
            
            # Log failed execution
            await self._log_tool_execution(error_result)
            
            # Re-raise the exception
            raise
    
    async def list_available_tools(self, user: User) -> List[ToolMetadata]:
        """List all tools available to the user"""
        try:
            all_tools = await self.tool_registry.list_tools()
            available_tools = []
            
            for tool_name, tool in all_tools.items():
                # Check if user has access to this tool
                if await self._check_tool_permissions(tool_name, user):
                    metadata = ToolMetadata(
                        name=tool_name,
                        description=tool.description,
                        parameters=tool.parameters,
                        category=getattr(tool, 'category', 'general'),
                        tags=getattr(tool, 'tags', []),
                        version=getattr(tool, 'version', '1.0.0'),
                        author=getattr(tool, 'author', 'System'),
                        requires_approval=self._requires_approval(tool_name),
                        execution_time_estimate="< 30 seconds",  # This could be dynamic
                        metadata={
                            "permissions": self.tool_permissions.get(tool_name, {}).dict() if tool_name in self.tool_permissions else {},
                            "usage_count": await self._get_tool_usage_count(tool_name),
                            "last_used": await self._get_tool_last_used(tool_name)
                        }
                    )
                    available_tools.append(metadata)
            
            return available_tools
            
        except Exception as e:
            logger.error(f"Error listing available tools: {e}")
            return []
    
    async def get_tool_permissions(self, tool_name: str) -> ToolPermission:
        """Get permissions for a specific tool"""
        try:
            if tool_name not in self.tool_permissions:
                # Return default permissions if not explicitly configured
                return ToolPermission(
                    tool_name=tool_name,
                    allowed_roles=["agent", "supervisor", "admin"],
                    required_permissions=[],
                    restrictions={},
                    approval_required=False
                )
            
            return self.tool_permissions[tool_name]
            
        except Exception as e:
            logger.error(f"Error getting tool permissions for {tool_name}: {e}")
            raise
    
    async def get_tool_metadata(self, tool_name: str) -> Optional[ToolMetadata]:
        """Get metadata for a specific tool"""
        try:
            if not await self.tool_registry.has_tool(tool_name):
                return None
            
            tool = await self.tool_registry.get_tool(tool_name)
            
            return ToolMetadata(
                name=tool_name,
                description=tool.description,
                parameters=tool.parameters,
                category=getattr(tool, 'category', 'general'),
                tags=getattr(tool, 'tags', []),
                version=getattr(tool, 'version', '1.0.0'),
                author=getattr(tool, 'author', 'System'),
                requires_approval=self._requires_approval(tool_name),
                execution_time_estimate="< 30 seconds",
                metadata={
                    "permissions": self.tool_permissions.get(tool_name, {}).dict() if tool_name in self.tool_permissions else {},
                    "usage_count": await self._get_tool_usage_count(tool_name),
                    "last_used": await self._get_tool_last_used(tool_name)
                }
            )
            
        except Exception as e:
            logger.error(f"Error getting tool metadata for {tool_name}: {e}")
            return None
    
    async def validate_tool_parameters(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate parameters for a tool without executing it"""
        try:
            if not await self.tool_registry.has_tool(tool_name):
                return {
                    "valid": False,
                    "errors": [f"Tool '{tool_name}' not found"]
                }
            
            tool = await self.tool_registry.get_tool(tool_name)
            
            # Basic parameter validation
            errors = []
            required_params = tool.parameters.get("required", [])
            provided_params = set(parameters.keys())
            
            # Check required parameters
            for param in required_params:
                if param not in provided_params:
                    errors.append(f"Missing required parameter: {param}")
            
            # Check parameter types if schema is available
            if "properties" in tool.parameters:
                for param_name, param_value in parameters.items():
                    if param_name in tool.parameters["properties"]:
                        param_schema = tool.parameters["properties"][param_name]
                        param_type = param_schema.get("type")
                        
                        if param_type and not self._validate_parameter_type(param_value, param_type):
                            errors.append(f"Invalid type for parameter '{param_name}': expected {param_type}")
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "validated_parameters": parameters
            }
            
        except Exception as e:
            logger.error(f"Error validating tool parameters for {tool_name}: {e}")
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"]
            }
    
    async def get_execution_history(
        self,
        user: User,
        limit: int = 100,
        tool_name: Optional[str] = None
    ) -> List[ToolExecutionResult]:
        """Get execution history for a user"""
        try:
            # Filter by user and optionally by tool name
            filtered_history = [
                result for result in self.execution_history
                if result.user_id == user.id and (tool_name is None or result.tool_name == tool_name)
            ]
            
            # Sort by timestamp (most recent first) and limit
            filtered_history.sort(key=lambda x: x.timestamp, reverse=True)
            return filtered_history[:limit]
            
        except Exception as e:
            logger.error(f"Error getting execution history: {e}")
            return []
    
    async def get_tool_usage_stats(self, tool_name: str) -> Dict[str, Any]:
        """Get usage statistics for a tool"""
        try:
            executions = [
                result for result in self.execution_history
                if result.tool_name == tool_name
            ]
            
            if not executions:
                return {
                    "tool_name": tool_name,
                    "total_executions": 0,
                    "successful_executions": 0,
                    "failed_executions": 0,
                    "success_rate": 0.0,
                    "avg_execution_time": 0.0,
                    "last_execution": None
                }
            
            successful = [e for e in executions if e.status == ToolExecutionStatus.SUCCESS]
            failed = [e for e in executions if e.status == ToolExecutionStatus.ERROR]
            
            avg_execution_time = sum(e.execution_time for e in executions) / len(executions)
            
            return {
                "tool_name": tool_name,
                "total_executions": len(executions),
                "successful_executions": len(successful),
                "failed_executions": len(failed),
                "success_rate": len(successful) / len(executions) * 100,
                "avg_execution_time": avg_execution_time,
                "last_execution": max(executions, key=lambda x: x.timestamp).timestamp
            }
            
        except Exception as e:
            logger.error(f"Error getting tool usage stats for {tool_name}: {e}")
            return {}
    
    # Private helper methods
    async def _load_tool_permissions(self):
        """Load tool permissions configuration"""
        # Default permissions for different tools
        self.tool_permissions = {
            "get_customer_profile": ToolPermission(
                tool_name="get_customer_profile",
                allowed_roles=["agent", "supervisor", "admin"],
                required_permissions=["read_customer_data"],
                restrictions={"rate_limit": 100},
                approval_required=False
            ),
            "search_knowledge_base": ToolPermission(
                tool_name="search_knowledge_base",
                allowed_roles=["agent", "supervisor", "admin"],
                required_permissions=["read_knowledge_base"],
                restrictions={"rate_limit": 200},
                approval_required=False
            ),
            "process_payment": ToolPermission(
                tool_name="process_payment",
                allowed_roles=["billing_agent", "supervisor", "admin"],
                required_permissions=["process_payments"],
                restrictions={"max_amount": 1000.00},
                approval_required=True
            ),
            "apply_credit_adjustment": ToolPermission(
                tool_name="apply_credit_adjustment",
                allowed_roles=["supervisor", "admin"],
                required_permissions=["apply_credits"],
                restrictions={"max_amount": 500.00},
                approval_required=True
            ),
            "transfer_to_human_agent": ToolPermission(
                tool_name="transfer_to_human_agent",
                allowed_roles=["agent", "supervisor", "admin"],
                required_permissions=["transfer_conversations"],
                restrictions={},
                approval_required=False
            ),
            "run_diagnostic_test": ToolPermission(
                tool_name="run_diagnostic_test",
                allowed_roles=["technical_agent", "supervisor", "admin"],
                required_permissions=["run_diagnostics"],
                restrictions={"rate_limit": 50},
                approval_required=False
            ),
            "schedule_technician_visit": ToolPermission(
                tool_name="schedule_technician_visit",
                allowed_roles=["technical_agent", "supervisor", "admin"],
                required_permissions=["schedule_visits"],
                restrictions={},
                approval_required=True
            )
        }
    
    async def _check_tool_permissions(self, tool_name: str, user: User) -> bool:
        """Check if user has permission to execute a tool"""
        try:
            # Get tool permissions
            permissions = await self.get_tool_permissions(tool_name)
            
            # Check if user has required role
            if not any(role in user.roles for role in permissions.allowed_roles):
                return False
            
            # Check if user has required permissions
            for permission in permissions.required_permissions:
                if not user.has_permission(permission):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking tool permissions for {tool_name}: {e}")
            return False
    
    def _requires_approval(self, tool_name: str) -> bool:
        """Check if tool requires approval"""
        permissions = self.tool_permissions.get(tool_name)
        return permissions.approval_required if permissions else False
    
    async def _get_tool_usage_count(self, tool_name: str) -> int:
        """Get usage count for a tool"""
        return len([
            result for result in self.execution_history
            if result.tool_name == tool_name
        ])
    
    async def _get_tool_last_used(self, tool_name: str) -> Optional[datetime]:
        """Get last used timestamp for a tool"""
        executions = [
            result for result in self.execution_history
            if result.tool_name == tool_name
        ]
        
        if not executions:
            return None
        
        return max(executions, key=lambda x: x.timestamp).timestamp
    
    def _validate_parameter_type(self, value: Any, expected_type: str) -> bool:
        """Validate parameter type"""
        type_validators = {
            "string": lambda x: isinstance(x, str),
            "integer": lambda x: isinstance(x, int),
            "number": lambda x: isinstance(x, (int, float)),
            "boolean": lambda x: isinstance(x, bool),
            "array": lambda x: isinstance(x, list),
            "object": lambda x: isinstance(x, dict)
        }
        
        validator = type_validators.get(expected_type)
        return validator(value) if validator else True
    
    async def _log_tool_execution(self, result: ToolExecutionResult):
        """Log tool execution result"""
        try:
            log_data = {
                "execution_id": result.execution_id,
                "tool_name": result.tool_name,
                "user_id": result.user_id,
                "status": result.status.value,
                "execution_time": result.execution_time,
                "timestamp": result.timestamp.isoformat(),
                "success": result.status == ToolExecutionStatus.SUCCESS,
                "error": result.error
            }
            
            if result.status == ToolExecutionStatus.SUCCESS:
                logger.info(f"Tool execution successful: {json.dumps(log_data)}")
            else:
                logger.error(f"Tool execution failed: {json.dumps(log_data)}")
                
        except Exception as e:
            logger.error(f"Error logging tool execution: {e}")
    
    async def cleanup(self):
        """Cleanup tools service resources"""
        try:
            logger.info("Cleaning up Tools Service...")
            
            # Clear execution history
            self.execution_history.clear()
            
            # Cleanup tool registry
            if self.tool_registry:
                await self.tool_registry.cleanup()
            
            self.initialized = False
            logger.info("Tools Service cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during tools service cleanup: {e}")
            raise


# Dependency injection function
async def get_tools_service() -> ToolsService:
    """Get tools service instance"""
    service = ToolsService()
    if not service.initialized:
        await service.initialize()
    return service