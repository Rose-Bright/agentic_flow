"""
LangGraph Integration Module - Central coordination for all LangGraph components
"""

from typing import Dict, Any, Optional
from datetime import datetime
import asyncio

from src.core.langgraph_orchestrator import LangGraphOrchestrator
from src.core.state_checkpointer import ConversationStateManager
from src.core.graph_builder import ConversationGraphBuilder
from src.services.tool_registry import ToolRegistry
from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class LangGraphIntegration:
    """
    Central integration class that coordinates all LangGraph components
    This is the main entry point for LangGraph functionality
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.orchestrator = None
        self.state_manager = None
        self.tool_registry = None
        self.initialized = False
        # Add these from draft version
        self.start_time = datetime.now()
        self.performance_metrics = {
            "total_conversations": 0,
            "successful_resolutions": 0,
            "errors": 0,
            "average_response_time": 0.0,
            "response_times": []  # Track individual response times
        }
        
    async def initialize(self) -> bool:
        """
        Initialize all LangGraph components in proper order
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            logger.info("Starting LangGraph integration initialization...")
            
            # Step 1: Initialize tool registry
            logger.info("Initializing tool registry...")
            self.tool_registry = ToolRegistry()
            
            # Step 2: Initialize state manager
            logger.info("Initializing conversation state manager...")
            self.state_manager = ConversationStateManager()
            await self.state_manager.initialize()
            
            # Step 3: Initialize LangGraph orchestrator
            logger.info("Initializing LangGraph orchestrator...")
            self.orchestrator = LangGraphOrchestrator()
            await self.orchestrator.initialize()
            
            # Step 4: Verify all components are working
            await self._verify_integration()
            
            self.initialized = True
            logger.info("LangGraph integration initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize LangGraph integration: {e}")
            await self._cleanup_partial_initialization()
            return False
    
    async def process_conversation(
        self,
        message: str,
        conversation_id: str,
        customer_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a conversation message through the LangGraph workflow"""
        if not self.initialized:
            raise RuntimeError("LangGraph integration not initialized")
        
        # Track performance metrics
        start_time = datetime.now()
        self.performance_metrics["total_conversations"] += 1

        try:
            # Process through orchestrator
            result = await self.orchestrator.process_conversation(
                message=message,
                conversation_id=conversation_id,
                customer_id=customer_id
            )
            
            # Update performance metrics
            response_time = (datetime.now() - start_time).total_seconds()
            self.performance_metrics["response_times"].append(response_time)

            # Keep only last 100 response times for average calculation
            if len(self.performance_metrics["response_times"]) > 100:
                self.performance_metrics["response_times"] = self.performance_metrics["response_times"][-100:]

            self.performance_metrics["average_response_time"] = (
                sum(self.performance_metrics["response_times"]) /
                len(self.performance_metrics["response_times"])
            )
            
            if result.get("success", True):
                self.performance_metrics["successful_resolutions"] += 1

            # Add integration metadata
            result["integration_metadata"] = {
                "processed_by": "langgraph_integration",
            "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "response_time_seconds": response_time
        }
        
            return result
        except Exception as e:
            self.performance_metrics["errors"] += 1
            logger.error(f"Error processing conversation {conversation_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "conversation_id": conversation_id,
                "message": "I apologize, but I'm experiencing technical difficulties. Please try again in a moment."
                }

    async def get_conversation_state(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get current conversation state"""
        if not self.initialized:
            return None
        try:
            state = await self.orchestrator.get_conversation_state(conversation_id)
            if state:
                return {
                    "conversation_id": conversation_id,
                    "status": state.status.value,
                    "current_agent": state.current_agent_type,
                    "escalation_level": state.escalation_level,
                    "confidence": state.confidence_score,
                    "requires_human": state.requires_human,
                    "message_count": len(state.conversation_history),
                    "last_activity": state.last_activity.isoformat() if state.last_activity else None
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting conversation state {conversation_id}: {e}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check of all components"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "integration_initialized": self.initialized,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "components": {}
        }
        
        try:
            # Check orchestrator
            if self.orchestrator:
                orchestrator_health = await self.orchestrator.health_check()
                health_status["components"]["orchestrator"] = orchestrator_health
            else:
                health_status["components"]["orchestrator"] = {"status": "not_initialized"}
            
            # Check state manager
            if self.state_manager:
                state_manager_health = await self._check_state_manager_health()
                health_status["components"]["state_manager"] = state_manager_health
            else:
                health_status["components"]["state_manager"] = {"status": "not_initialized"}
            
            # Check tool registry
            if self.tool_registry:
                tool_registry_health = await self._check_tool_registry_health()
                health_status["components"]["tool_registry"] = tool_registry_health
            else:
                health_status["components"]["tool_registry"] = {"status": "not_initialized"}
            
            # Determine overall status
            component_statuses = [
                comp.get("status", "error") for comp in health_status["components"].values()
            ]
            
            if any(status == "error" for status in component_statuses):
                health_status["status"] = "error"
            elif any(status == "degraded" for status in component_statuses):
                health_status["status"] = "degraded"
            elif not self.initialized:
                health_status["status"] = "initializing"
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_status["status"] = "error"
            health_status["error"] = str(e)
        
        return health_status
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics from all components"""
        if not self.initialized:
            return {"error": "Integration not initialized"}
        
        try:
            # Enhanced metrics combining both approaches
            uptime_seconds = (datetime.now() - self.start_time).total_seconds()

            metrics = {
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": uptime_seconds,
                "integration_performance": {
                    "total_conversations": self.performance_metrics["total_conversations"],
                    "successful_resolutions": self.performance_metrics["successful_resolutions"],
                    "error_count": self.performance_metrics["errors"],
                    "success_rate": (
                        self.performance_metrics["successful_resolutions"] /
                        max(self.performance_metrics["total_conversations"], 1) * 100
                    ),
                    "average_response_time": self.performance_metrics["average_response_time"]
                },
                "components": {}
            }
            
            # Get orchestrator metrics
            if hasattr(self.orchestrator, 'get_performance_metrics'):
                metrics["components"]["orchestrator"] = await self.orchestrator.get_performance_metrics()
            
            # Get state manager metrics
            if hasattr(self.state_manager, 'get_performance_metrics'):
                metrics["components"]["state_manager"] = await self.state_manager.get_performance_metrics()
            
            # Get tool registry metrics
            if hasattr(self.tool_registry, 'get_performance_metrics'):
                metrics["components"]["tool_registry"] = self.tool_registry.execution_stats
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {"error": str(e)}
    
    async def cleanup(self):
        """Cleanup all components and resources"""
        try:
            logger.info("Cleaning up LangGraph integration...")
            
            # Cleanup orchestrator
            if self.orchestrator:
                await self.orchestrator.cleanup()
                self.orchestrator = None
            
            # Cleanup state manager
            if self.state_manager:
                await self.state_manager.cleanup()
                self.state_manager = None
            
            # Tool registry doesn't need async cleanup
            self.tool_registry = None
            
            self.initialized = False
            logger.info("LangGraph integration cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            raise
    
    # Private helper methods
    async def _verify_integration(self):
        """Verify that all components are properly integrated"""
        logger.info("Verifying LangGraph integration...")
        
        # Test basic workflow functionality
        test_conversation_id = f"test_{int(datetime.now().timestamp())}"
        test_result = await self.orchestrator.process_conversation(
            message="Hello, this is a test",
            conversation_id=test_conversation_id,
            customer_id=None
        )
        
        if not test_result.get("success"):
            raise RuntimeError(f"Integration verification failed: {test_result.get('error')}")
        
        # Cleanup test conversation
        try:
            await self.state_manager.close_conversation(test_conversation_id)
        except:
            pass  # Ignore cleanup errors in verification
        
        logger.info("LangGraph integration verification completed successfully")
    
    async def _cleanup_partial_initialization(self):
        """Cleanup any partially initialized components"""
        try:
            if self.state_manager:
                await self.state_manager.cleanup()
            if self.orchestrator:
                await self.orchestrator.cleanup()
        except Exception as e:
            logger.error(f"Error during partial cleanup: {e}")
    
    async def _check_state_manager_health(self) -> Dict[str, Any]:
        """Check state manager health"""
        try:
            if self.state_manager.checkpointer:
                return {
                    "status": "healthy",
                    "active_conversations": len(self.state_manager.active_conversations),
                    "checkpointer_initialized": bool(self.state_manager.checkpointer)
                }
            else:
                return {"status": "error", "error": "Checkpointer not initialized"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _check_tool_registry_health(self) -> Dict[str, Any]:
        """Check tool registry health"""
        try:
            return {
                "status": "healthy",
                "registered_tools": len(self.tool_registry.tools),
                "execution_stats": {
                    tool: stats for tool, stats in self.tool_registry.execution_stats.items()
                    if stats["total_executions"] > 0
                }
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


# Global instance for easy access
_langgraph_integration = None


async def get_langgraph_integration() -> LangGraphIntegration:
    """
    Get the global LangGraph integration instance
    Initializes it if not already done
    """
    global _langgraph_integration
    
    if _langgraph_integration is None:
        _langgraph_integration = LangGraphIntegration()
        await _langgraph_integration.initialize()
    
    return _langgraph_integration


async def cleanup_langgraph_integration():
    """Cleanup the global LangGraph integration instance"""
    global _langgraph_integration
    
    if _langgraph_integration:
        await _langgraph_integration.cleanup()
        _langgraph_integration = None


# Context manager for easy usage
class LangGraphIntegrationContext:
    """Context manager for LangGraph integration"""
    
    def __init__(self):
        self.integration = None
    
    async def __aenter__(self) -> LangGraphIntegration:
        self.integration = await get_langgraph_integration()
        return self.integration
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Don't cleanup on context exit - let global cleanup handle it
        pass


# Convenience function for quick usage
async def process_message_with_langgraph(
    message: str,
    conversation_id: str,
    customer_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to process a message through LangGraph
    
    Args:
        message: Customer message
        conversation_id: Conversation identifier
        customer_id: Customer identifier (optional)
        
    Returns:
        Dict containing response and conversation state
    """
    async with LangGraphIntegrationContext() as integration:
        return await integration.process_conversation(
            message=message,
            conversation_id=conversation_id,
            customer_id=customer_id
        )
