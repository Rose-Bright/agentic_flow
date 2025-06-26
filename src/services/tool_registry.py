from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

# Import the tool implementations
from src.tools.email_tools import EmailTools
from src.tools.phone_tools import PhoneTools
from src.tools.smartpath_tools import SmartPathTools
from src.tools.customer_tools import CustomerTools

@dataclass
class Tool:
    name: str
    description: str
    required_permissions: List[str]
    timeout_seconds: int
    retry_attempts: int
    async_execution: bool = False
    rate_limit: Optional[int] = None  # calls per minute

class ToolRegistry:
    """Registry for all available tools with access control and execution management"""
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.execution_stats: Dict[str, Dict[str, Any]] = {}
        
        self._register_default_tools()
    
    def register_tool(self, tool: Tool):
        """Register a new tool in the registry"""
        self.tools[tool.name] = tool
        self.execution_stats[tool.name] = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_execution_time": 0.0,
            "last_execution": None
        }
    
    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self.tools.get(tool_name)
    
    def _register_default_tools(self):
        """Register the default set of tools"""
        
        # Customer Profile Tools
        self.register_tool(Tool(
            name="get_customer_profile",
            description="Retrieve customer profile information",
            required_permissions=["read_customer_data"],
            timeout_seconds=5,
            retry_attempts=2
        ))
        
        self.register_tool(Tool(
            name="get_account_services",
            description="Get customer's subscribed services",
            required_permissions=["read_customer_data"],
            timeout_seconds=5,
            retry_attempts=2
        ))
        
        # Knowledge Base Tools
        self.register_tool(Tool(
            name="search_knowledge_base",
            description="Search internal knowledge base",
            required_permissions=["read_knowledge_base"],
            timeout_seconds=10,
            retry_attempts=2
        ))
        
        self.register_tool(Tool(
            name="get_troubleshooting_guide",
            description="Retrieve troubleshooting procedures",
            required_permissions=["read_knowledge_base"],
            timeout_seconds=8,
            retry_attempts=2
        ))
        
        # Ticket Management Tools
        self.register_tool(Tool(
            name="create_ticket",
            description="Create a new support ticket",
            required_permissions=["create_tickets"],
            timeout_seconds=10,
            retry_attempts=3
        ))
        
        self.register_tool(Tool(
            name="update_ticket_status",
            description="Update ticket status",
            required_permissions=["update_tickets"],
            timeout_seconds=5,
            retry_attempts=2
        ))
        
        # Diagnostic Tools
        self.register_tool(Tool(
            name="run_diagnostic_test",
            description="Run system diagnostics",
            required_permissions=["execute_diagnostics"],
            timeout_seconds=30,
            retry_attempts=1,
            async_execution=True
        ))
        
        self.register_tool(Tool(
            name="check_system_logs",
            description="Analyze system logs",
            required_permissions=["read_system_logs"],
            timeout_seconds=15,
            retry_attempts=2
        ))
        
        # Billing Tools
        self.register_tool(Tool(
            name="get_billing_information",
            description="Retrieve billing details",
            required_permissions=["read_billing_data"],
            timeout_seconds=10,
            retry_attempts=2
        ))
        
        self.register_tool(Tool(
            name="process_payment",
            description="Process customer payment",
            required_permissions=["process_payments"],
            timeout_seconds=20,
            retry_attempts=3
        ))
        
        # Notification Tools
        self.register_tool(Tool(
            name="send_customer_notification",
            description="Send notification to customer",
            required_permissions=["send_notifications"],
            timeout_seconds=5,
            retry_attempts=2
        ))
        
        # Analytics Tools
        self.register_tool(Tool(
            name="log_interaction_metrics",
            description="Log conversation metrics",
            required_permissions=["write_analytics"],
            timeout_seconds=5,
            retry_attempts=1
        ))

        # === TELECOM SERVICE TOOLS ===
        
        # Email Tools
        self.register_tool(Tool(
            name="validate_email_format",
            description="Validate email address format",
            required_permissions=["validate_communications"],
            timeout_seconds=3,
            retry_attempts=1
        ))
        
        self.register_tool(Tool(
            name="lookup_customer_by_email",
            description="Look up customer profile by email address",
            required_permissions=["read_customer_data"],
            timeout_seconds=5,
            retry_attempts=2
        ))
        
        self.register_tool(Tool(
            name="send_email_reply",
            description="Send email reply to customer",
            required_permissions=["send_notifications"],
            timeout_seconds=10,
            retry_attempts=3
        ))
        
        # Phone Management Tools
        self.register_tool(Tool(
            name="validate_phone_number",
            description="Validate phone number format and structure",
            required_permissions=["validate_service_requests"],
            timeout_seconds=3,
            retry_attempts=1
        ))
        
        self.register_tool(Tool(
            name="get_customer_phone_services",
            description="Get all phone services for a customer",
            required_permissions=["read_phone_services"],
            timeout_seconds=5,
            retry_attempts=2
        ))
        
        self.register_tool(Tool(
            name="check_disconnect_eligibility",
            description="Check if a phone number is eligible for disconnection",
            required_permissions=["read_phone_services", "validate_service_requests"],
            timeout_seconds=8,
            retry_attempts=2
        ))
        
        self.register_tool(Tool(
            name="check_add_line_capacity",
            description="Check if customer can add additional phone lines",
            required_permissions=["read_phone_services", "validate_service_requests"],
            timeout_seconds=5,
            retry_attempts=2
        ))
        
        # SmartPath Integration Tools
        self.register_tool(Tool(
            name="create_smartpath_ticket",
            description="Create a new ticket in SmartPath system",
            required_permissions=["create_tickets"],
            timeout_seconds=15,
            retry_attempts=3
        ))
        
        self.register_tool(Tool(
            name="add_ticket_notes",
            description="Add notes to an existing SmartPath ticket",
            required_permissions=["update_tickets"],
            timeout_seconds=5,
            retry_attempts=2
        ))
        
        self.register_tool(Tool(
            name="set_ticket_priority",
            description="Update ticket priority in SmartPath",
            required_permissions=["update_tickets"],
            timeout_seconds=5,
            retry_attempts=2
        ))
        
        # Enhanced Customer Tools
        self.register_tool(Tool(
            name="update_customer_notes",
            description="Add notes to customer profile",
            required_permissions=["update_customer_data"],
            timeout_seconds=5,
            retry_attempts=2
        ))
        
        self.register_tool(Tool(
            name="log_customer_interaction",
            description="Log customer interaction for analytics and tracking",
            required_permissions=["write_analytics"],
            timeout_seconds=3,
            retry_attempts=2
        ))
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        agent_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a tool with monitoring and error handling"""
        
        tool = self.tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")
        
        # Check permissions
        if not await self._check_permissions(tool, agent_context):
            raise PermissionError(f"Insufficient permissions for tool: {tool_name}")
        
        # Check rate limits
        if not await self._check_rate_limit(tool):
            raise Exception(f"Rate limit exceeded for tool: {tool_name}")
        
        start_time = datetime.utcnow()
        attempt = 0
        last_error = None
        
        while attempt <= tool.retry_attempts:
            try:
                # Execute tool implementation
                result = await self._execute_tool_implementation(tool_name, parameters)
                
                # Update stats
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                await self._update_execution_stats(tool, True, execution_time)
                
                return result
                
            except Exception as e:
                last_error = e
                attempt += 1
                
                if attempt > tool.retry_attempts:
                    # Update stats with failure
                    await self._update_execution_stats(tool, False, 0)
                    raise last_error
                
                # Wait before retry
                await self._wait_before_retry(attempt)

    async def _execute_tool_implementation(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the actual tool implementation"""
        
        # Email Tools
        if tool_name == "validate_email_format":
            return await EmailTools.validate_email_format(parameters["email"])
        elif tool_name == "lookup_customer_by_email":
            return await EmailTools.lookup_customer_by_email(parameters["email"])
        elif tool_name == "send_email_reply":
            return await EmailTools.send_email_reply(
                parameters["to_email"],
                parameters["subject"],
                parameters["body"],
                parameters.get("email_type", "general"),
                parameters.get("priority", "normal")
            )
        
        # Phone Tools
        elif tool_name == "validate_phone_number":
            return await PhoneTools.validate_phone_number(parameters["phone_number"])
        elif tool_name == "get_customer_phone_services":
            return await PhoneTools.get_customer_phone_services(parameters["customer_id"])
        elif tool_name == "check_disconnect_eligibility":
            return await PhoneTools.check_disconnect_eligibility(
                parameters["customer_id"],
                parameters["phone_number"]
            )
        elif tool_name == "check_add_line_capacity":
            return await PhoneTools.check_add_line_capacity(parameters["customer_id"])
        
        # SmartPath Tools
        elif tool_name == "create_smartpath_ticket":
            return await SmartPathTools.create_smartpath_ticket(**parameters)
        elif tool_name == "add_ticket_notes":
            return await SmartPathTools.add_ticket_notes(
                parameters["ticket_id"],
                parameters["notes"],
                parameters["agent_id"],
                parameters.get("note_type", "agent_note")
            )
        elif tool_name == "set_ticket_priority":
            return await SmartPathTools.set_ticket_priority(
                parameters["ticket_id"],
                parameters["priority"],
                parameters.get("reason")
            )
        
        # Customer Tools
        elif tool_name == "get_customer_profile":
            return await CustomerTools.get_customer_profile(parameters["customer_id"])
        elif tool_name == "update_customer_notes":
            return await CustomerTools.update_customer_notes(
                parameters["customer_id"],
                parameters["notes"],
                parameters.get("note_type", "service_interaction")
            )
        elif tool_name == "log_customer_interaction":
            return await CustomerTools.log_customer_interaction(**parameters)
        
        # Default tools (mock implementations for existing tools)
        else:
            # Return mock implementation for existing tools
            return {
                "result": "mock_implementation",
                "tool_name": tool_name,
                "parameters": parameters,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _check_permissions(self, tool: Tool, agent_context: Dict[str, Any]) -> bool:
        """Check if the agent has required permissions for the tool"""
        agent_permissions = agent_context.get("permissions", [])
        return all(perm in agent_permissions for perm in tool.required_permissions)
    
    async def _check_rate_limit(self, tool: Tool) -> bool:
        """Check if tool execution is within rate limits"""
        if not tool.rate_limit:
            return True
            
        stats = self.execution_stats[tool.name]
        recent_executions = 0  # Implement actual rate limiting logic
        
        return recent_executions < tool.rate_limit
    
    async def _update_execution_stats(self, tool: Tool, success: bool, execution_time: float):
        """Update tool execution statistics"""
        stats = self.execution_stats[tool.name]
        stats["total_executions"] += 1
        if success:
            stats["successful_executions"] += 1
        else:
            stats["failed_executions"] += 1
        
        # Update average execution time
        prev_avg = stats["average_execution_time"]
        prev_total = stats["total_executions"] - 1
        if prev_total > 0:
            stats["average_execution_time"] = (prev_avg * prev_total + execution_time) / stats["total_executions"]
        else:
            stats["average_execution_time"] = execution_time
        
        stats["last_execution"] = datetime.utcnow()
    
    async def _wait_before_retry(self, attempt: int):
        """Implement exponential backoff for retries"""
        import asyncio
        wait_time = min(2 ** attempt, 30)  # Max 30 seconds
        await asyncio.sleep(wait_time)