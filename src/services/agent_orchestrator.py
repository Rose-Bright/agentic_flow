"""
Enhanced Agent Orchestrator with LangGraph Integration
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from src.models.state import AgentState, TicketStatus, Sentiment, CustomerTier
from src.core.langgraph_orchestrator import LangGraphOrchestrator
from src.core.state_checkpointer import ConversationStateManager
from src.services.tool_registry import ToolRegistry
from src.services.performance_monitor import PerformanceMonitor
from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class AgentOrchestrator:
    """Enhanced orchestrator with LangGraph integration for conversation management"""
    
    def __init__(self):
        self.settings = get_settings()
        self.langgraph_orchestrator = LangGraphOrchestrator()
        self.state_manager = ConversationStateManager()
        self.tool_registry = ToolRegistry()
        self.performance_monitor = PerformanceMonitor()
        self.initialized = False
    
    async def initialize(self):
        """Initialize all orchestrator components"""
        if self.initialized:
            return
        
        logger.info("Initializing Agent Orchestrator with LangGraph...")
        
        try:
            # Initialize state manager
            await self.state_manager.initialize()
            
            # Initialize LangGraph orchestrator
            await self.langgraph_orchestrator.initialize()
            
            # Initialize performance monitor
            await self.performance_monitor.initialize()
            
            self.initialized = True
            logger.info("Agent Orchestrator initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Agent Orchestrator: {e}")
            raise
    
    async def process_message(
        self,
        message: str,
        conversation_id: str,
        customer_id: Optional[str] = None,
        channel: str = "web",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a customer message through the LangGraph workflow
        
        Args:
            message: Customer message content
            conversation_id: Unique conversation identifier
            customer_id: Customer identifier (optional)
            channel: Communication channel
            metadata: Additional metadata
            
        Returns:
            Dict containing response and conversation state
        """
        if not self.initialized:
            await self.initialize()
        
        start_time = datetime.now()
        
        try:
            logger.info(f"Processing message for conversation {conversation_id}")
            
            # Process through LangGraph workflow
            result = await self.langgraph_orchestrator.process_conversation(
                message=message,
                conversation_id=conversation_id,
                customer_id=customer_id
            )
            
            # Log performance metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            await self._log_performance_metrics(
                conversation_id=conversation_id,
                processing_time=processing_time,
                result=result
            )
            
            # Extract response from result
            response_data = {
                "success": result.get("success", True),
                "message": result.get("response", ""),
                "conversation_id": conversation_id,
                "agent_type": result.get("agent_type", "unknown"),
                "confidence": result.get("confidence", 0.0),
                "status": result.get("status", "active"),
                "requires_human": result.get("final_state", {}).get("requires_human", False),
                "processing_time": processing_time,
                "metadata": {
                    "intent": result.get("final_state", {}).get("current_intent", ""),
                    "sentiment": result.get("final_state", {}).get("sentiment", "neutral"),
                    "escalation_level": result.get("final_state", {}).get("escalation_level", 0),
                    "channel": channel,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # Handle error cases
            if not result.get("success"):
                response_data.update({
                    "error": result.get("error", "Unknown error occurred"),
                    "error_type": result.get("error_type", "ProcessingError")
                })
            
            logger.info(f"Message processed successfully for conversation {conversation_id}")
            return response_data
            
        except Exception as e:
            logger.error(f"Error processing message for conversation {conversation_id}: {e}")
            
            # Return error response
            return {
                "success": False,
                "message": "I apologize, but I'm experiencing technical difficulties. Please try again in a moment.",
                "conversation_id": conversation_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "processing_time": (datetime.now() - start_time).total_seconds(),
                "requires_human": True
            }
    
    async def get_conversation_status(self, conversation_id: str) -> Dict[str, Any]:
        """Get current status of a conversation"""
        try:
            # Get conversation state from LangGraph
            state = await self.langgraph_orchestrator.get_conversation_state(conversation_id)
            
            if not state:
                return {
                    "conversation_id": conversation_id,
                    "status": "not_found",
                    "message": "Conversation not found"
                }
            
            return {
                "conversation_id": conversation_id,
                "status": state.status.value,
                "current_agent": state.current_agent_type,
                "escalation_level": state.escalation_level,
                "sentiment": state.sentiment.value,
                "confidence": state.confidence_score,
                "requires_human": state.requires_human,
                "session_duration": (
                    datetime.now() - state.session_start
                ).total_seconds() if state.session_start else 0,
                "message_count": len(state.conversation_history),
                "resolution_attempts": len(state.resolution_attempts),
                "last_activity": state.last_activity.isoformat() if state.last_activity else None
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation status for {conversation_id}: {e}")
            return {
                "conversation_id": conversation_id,
                "status": "error",
                "error": str(e)
            }
    
    async def transfer_to_human(
        self,
        conversation_id: str,
        reason: str = "customer_request",
        priority: str = "medium"
    ) -> Dict[str, Any]:
        """Transfer conversation to human agent"""
        try:
            logger.info(f"Transferring conversation {conversation_id} to human agent")
            
            # Get current state
            state = await self.langgraph_orchestrator.get_conversation_state(conversation_id)
            
            if not state:
                return {
                    "success": False,
                    "message": "Conversation not found",
                    "conversation_id": conversation_id
                }
            
            # Update state for human transfer
            state.requires_human = True
            state.status = TicketStatus.ESCALATED
            
            # Add transfer record to escalation history
            transfer_record = {
                "from_agent": state.current_agent_type,
                "to_agent": "human_agent",
                "timestamp": datetime.now(),
                "reason": reason,
                "context_transfer": {
                    "conversation_summary": await self._generate_conversation_summary(state),
                    "customer_context": state.customer.__dict__ if state.customer else {},
                    "priority": priority,
                    "urgency_indicators": await self._assess_urgency_indicators(state)
                }
            }
            
            state.escalation_history.append(transfer_record)
            
            # Execute transfer tool if available
            try:
                await self.tool_registry.execute_tool(
                    "transfer_to_human_agent",
                    {
                        "conversation_id": conversation_id,
                        "transfer_context": transfer_record["context_transfer"],
                        "priority": priority,
                        "reason": reason
                    },
                    {"agent_type": "system", "permissions": ["transfer_conversations"]}
                )
            except Exception as tool_error:
                logger.warning(f"Human transfer tool execution failed: {tool_error}")
            
            return {
                "success": True,
                "message": "Conversation transferred to human agent",
                "conversation_id": conversation_id,
                "transfer_id": f"transfer_{conversation_id}_{int(datetime.now().timestamp())}",
                "priority": priority,
                "estimated_wait_time": await self._estimate_human_agent_wait_time(priority)
            }
            
        except Exception as e:
            logger.error(f"Error transferring conversation {conversation_id} to human: {e}")
            return {
                "success": False,
                "message": "Failed to transfer to human agent",
                "conversation_id": conversation_id,
                "error": str(e)
            }
    
    async def close_conversation(
        self,
        conversation_id: str,
        reason: str = "resolved",
        satisfaction_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """Close a conversation"""
        try:
            logger.info(f"Closing conversation {conversation_id}")
            
            # Get current state
            state = await self.langgraph_orchestrator.get_conversation_state(conversation_id)
            
            if not state:
                return {
                    "success": False,
                    "message": "Conversation not found",
                    "conversation_id": conversation_id
                }
            
            # Update state
            state.status = TicketStatus.CLOSED
            
            # Add final conversation summary
            conversation_summary = await self._generate_final_conversation_summary(
                state, reason, satisfaction_score
            )
            
            # Log final metrics
            await self.performance_monitor.log_conversation_closure(
                conversation_id=conversation_id,
                state=state,
                reason=reason,
                satisfaction_score=satisfaction_score
            )
            
            # Close conversation in state manager
            await self.state_manager.close_conversation(conversation_id)
            
            return {
                "success": True,
                "message": "Conversation closed successfully",
                "conversation_id": conversation_id,
                "summary": conversation_summary,
                "final_status": state.status.value,
                "duration": (
                    datetime.now() - state.session_start
                ).total_seconds() if state.session_start else 0,
                "resolution_attempts": len(state.resolution_attempts),
                "satisfaction_score": satisfaction_score
            }
            
        except Exception as e:
            logger.error(f"Error closing conversation {conversation_id}: {e}")
            return {
                "success": False,
                "message": "Failed to close conversation",
                "conversation_id": conversation_id,
                "error": str(e)
            }
    
    async def get_agent_performance_metrics(
        self,
        time_range: str = "24h",
        agent_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get performance metrics for agents"""
        try:
            return await self.performance_monitor.get_performance_report(
                time_range=time_range,
                agent_type=agent_type
            )
            
        except Exception as e:
            logger.error(f"Error getting agent performance metrics: {e}")
            return {
                "error": str(e),
                "time_range": time_range,
                "agent_type": agent_type
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform system health check"""
        try:
            health_status = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "components": {}
            }
            
            # Check LangGraph orchestrator
            try:
                if self.langgraph_orchestrator.compiled_graph:
                    health_status["components"]["langgraph"] = "healthy"
                else:
                    health_status["components"]["langgraph"] = "not_initialized"
            except:
                health_status["components"]["langgraph"] = "error"
            
            # Check state manager
            try:
                if self.state_manager.checkpointer:
                    health_status["components"]["state_manager"] = "healthy"
                else:
                    health_status["components"]["state_manager"] = "not_initialized"
            except:
                health_status["components"]["state_manager"] = "error"
            
            # Check tool registry
            try:
                tool_count = len(self.tool_registry.tools)
                health_status["components"]["tool_registry"] = f"healthy ({tool_count} tools)"
            except:
                health_status["components"]["tool_registry"] = "error"
            
            # Overall status
            if any(status == "error" for status in health_status["components"].values()):
                health_status["status"] = "degraded"
            elif any("not_initialized" in status for status in health_status["components"].values()):
                health_status["status"] = "initializing"
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error in health check: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    # Helper methods
    async def _log_performance_metrics(
        self,
        conversation_id: str,
        processing_time: float,
        result: Dict[str, Any]
    ):
        """Log performance metrics for the conversation"""
        try:
            metrics = {
                "conversation_id": conversation_id,
                "processing_time": processing_time,
                "success": result.get("success", True),
                "agent_type": result.get("agent_type", "unknown"),
                "confidence": result.get("confidence", 0.0),
                "timestamp": datetime.now().isoformat()
            }
            
            await self.performance_monitor.log_interaction_metrics(metrics)
            
        except Exception as e:
            logger.error(f"Failed to log performance metrics: {e}")
    
    async def _generate_conversation_summary(self, state: AgentState) -> str:
        """Generate conversation summary for transfer"""
        summary_parts = [
            f"Intent: {state.current_intent}",
            f"Status: {state.status.value}",
            f"Agent: {state.current_agent_type}",
            f"Escalation Level: {state.escalation_level}",
            f"Sentiment: {state.sentiment.value}",
            f"Messages: {len(state.conversation_history)}",
            f"Resolution Attempts: {len(state.resolution_attempts)}"
        ]
        
        if state.customer:
            summary_parts.append(f"Customer Tier: {state.customer.tier.value}")
        
        return " | ".join(summary_parts)
    
    async def _generate_final_conversation_summary(
        self,
        state: AgentState,
        reason: str,
        satisfaction_score: Optional[float]
    ) -> Dict[str, Any]:
        """Generate final conversation summary"""
        return {
            "reason": reason,
            "final_status": state.status.value,
            "total_messages": len(state.conversation_history),
            "resolution_attempts": len(state.resolution_attempts),
            "escalation_level": state.escalation_level,
            "agents_involved": list(set(state.previous_agents + [state.current_agent_type])),
            "tools_used": list(set(state.tools_used)),
            "duration_seconds": (
                datetime.now() - state.session_start
            ).total_seconds() if state.session_start else 0,
            "satisfaction_score": satisfaction_score,
            "final_sentiment": state.sentiment.value,
            "customer_tier": state.customer.tier.value if state.customer else "unknown"
        }
    
    async def _assess_urgency_indicators(self, state: AgentState) -> List[str]:
        """Assess urgency indicators for human transfer"""
        indicators = []
        
        if state.customer and state.customer.tier == CustomerTier.PLATINUM:
            indicators.append("vip_customer")
        
        if state.sentiment in [Sentiment.NEGATIVE, Sentiment.FRUSTRATED]:
            indicators.append("negative_sentiment")
        
        if state.escalation_level >= 2:
            indicators.append("multiple_escalations")
        
        if len(state.resolution_attempts) >= 3:
            indicators.append("multiple_failed_attempts")
        
        if state.sla_breach_risk:
            indicators.append("sla_breach_risk")
        
        if len(state.error_log) > 0:
            indicators.append("system_errors")
        
        return indicators
    
    async def _estimate_human_agent_wait_time(self, priority: str) -> str:
        """Estimate wait time for human agent based on priority"""
        # This would typically integrate with workforce management systems
        wait_times = {
            "high": "< 5 minutes",
            "medium": "5-15 minutes", 
            "low": "15-30 minutes"
        }
        
        return wait_times.get(priority, "15-30 minutes")
    
    async def cleanup(self):
        """Cleanup orchestrator resources"""
        try:
            logger.info("Cleaning up Agent Orchestrator...")
            
            # Cleanup LangGraph orchestrator
            if self.langgraph_orchestrator:
                await self.langgraph_orchestrator.cleanup()
            
            # Cleanup state manager
            if self.state_manager:
                await self.state_manager.cleanup()
            
            # Cleanup performance monitor
            if self.performance_monitor:
                await self.performance_monitor.cleanup()
            
            self.initialized = False
            logger.info("Agent Orchestrator cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during orchestrator cleanup: {e}")
            raise
