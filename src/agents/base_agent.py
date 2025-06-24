from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from src.models.state import AgentState
from src.services.tool_registry import Tool, ToolRegistry

class BaseAgent(ABC):
    def __init__(
        self,
        name: str,
        model: str,
        capabilities: List[str],
        tools: List[str],
        confidence_threshold: float = 0.7
    ):
        self.name = name
        self.model = model
        self.capabilities = capabilities
        self.required_tools = tools
        self.confidence_threshold = confidence_threshold
        self.tool_registry: Optional[ToolRegistry] = None
    
    def register_tool_registry(self, registry: ToolRegistry):
        """Register the tool registry with the agent"""
        self.tool_registry = registry
        
    @abstractmethod
    async def handle_message(
        self, 
        message: str, 
        state: AgentState
    ) -> Dict[str, Any]:
        """Handle an incoming message and return response"""
        pass

    @abstractmethod
    async def can_handle(self, state: AgentState) -> bool:
        """Determine if this agent can handle the current state"""
        pass

    async def use_tool(
        self, 
        tool_name: str,
        parameters: Dict[str, Any],
        agent_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a tool from the agent's available tools"""
        if not self.tool_registry:
            raise RuntimeError("Tool registry not initialized")
            
        if tool_name not in self.required_tools:
            raise ValueError(f"Tool {tool_name} not available to this agent")
            
        return await self.tool_registry.execute_tool(
            tool_name=tool_name,
            parameters=parameters,
            agent_context=agent_context
        )
    
    async def should_escalate(self, state: AgentState) -> bool:
        """Determine if the conversation should be escalated"""
        # Basic escalation criteria
        if state.confidence_score < self.confidence_threshold:
            return True
            
        if len(state.resolution_attempts) >= 3:
            return True
            
        if state.customer and state.customer.tier == "PLATINUM":
            if state.sentiment_score < 0.3:  # Negative sentiment
                return True
        
        return False
    
    def get_agent_context(self, state: AgentState) -> Dict[str, Any]:
        """Get the context for tool execution"""
        return {
            "agent_name": self.name,
            "agent_type": self.__class__.__name__,
            "capabilities": self.capabilities,
            "conversation_id": state.conversation_id,
            "customer_id": state.customer.customer_id if state.customer else None,
            "permissions": self._get_agent_permissions()
        }
    
    def _get_agent_permissions(self) -> List[str]:
        """Get the permissions available to this agent"""
        # This should be implemented by each agent type
        return []