"""
Agent Service - Manages agent lifecycle, performance, and operations
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import asyncio
import uuid

from ..models.agent import (
    AgentType,
    AgentStatus,
    AgentMetrics,
    AgentPerformance,
    AgentState,
    AgentConfiguration,
    AgentCapability
)
from ..models.user import User
from ..core.config import get_settings
from ..core.logging import get_logger
from .agent_orchestrator import AgentOrchestrator
from .performance_monitor import PerformanceMonitor

logger = get_logger(__name__)


class AgentService:
    """Service for managing AI agents and their operations"""
    
    def __init__(self):
        self.settings = get_settings()
        self.agent_orchestrator = AgentOrchestrator()
        self.performance_monitor = PerformanceMonitor()
        self.agent_registry: Dict[str, AgentState] = {}
        self.agent_configs: Dict[AgentType, AgentConfiguration] = {}
        self.initialized = False
    
    async def initialize(self):
        """Initialize the agent service"""
        if self.initialized:
            return
        
        logger.info("Initializing Agent Service...")
        
        try:
            # Initialize agent orchestrator
            await self.agent_orchestrator.initialize()
            
            # Initialize performance monitor
            await self.performance_monitor.initialize()
            
            # Load agent configurations
            await self._load_agent_configurations()
            
            # Initialize agent registry
            await self._initialize_agent_registry()
            
            self.initialized = True
            logger.info("Agent Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Agent Service: {e}")
            raise
    
    async def get_agent_performance(
        self,
        time_delta: timedelta,
        agent_type: Optional[AgentType] = None
    ) -> List[AgentPerformance]:
        """Get agent performance metrics for a specific time period"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - time_delta
            
            # Get performance data from performance monitor
            performance_data = await self.performance_monitor.get_agent_performance(
                start_time=start_time,
                end_time=end_time,
                agent_type=agent_type.value if agent_type else None
            )
            
            # Convert to AgentPerformance objects
            performances = []
            for data in performance_data:
                performance = AgentPerformance(
                    agent_id=data.get("agent_id", "unknown"),
                    agent_type=AgentType(data.get("agent_type", "tier1_support")),
                    period_start=start_time,
                    period_end=end_time,
                    metrics=AgentMetrics(
                        agent_id=data.get("agent_id", "unknown"),
                        agent_type=AgentType(data.get("agent_type", "tier1_support")),
                        total_conversations=data.get("total_conversations", 0),
                        active_conversations=data.get("active_conversations", 0),
                        avg_response_time=data.get("avg_response_time", 0.0),
                        avg_resolution_time=data.get("avg_resolution_time", 0.0),
                        successful_resolutions=data.get("successful_resolutions", 0),
                        escalation_count=data.get("escalation_count", 0),
                        avg_customer_satisfaction=data.get("avg_customer_satisfaction", 0.0),
                        error_rate=data.get("error_rate", 0.0),
                        avg_confidence_score=data.get("avg_confidence_score", 0.0),
                        tools_usage=data.get("tools_usage", {}),
                        updated_at=datetime.utcnow()
                    ),
                    cpu_usage=data.get("cpu_usage", 0.0),
                    memory_usage=data.get("memory_usage", 0.0),
                    error_logs=data.get("error_logs", []),
                    performance_score=data.get("performance_score", 0.0)
                )
                performances.append(performance)
            
            return performances
            
        except Exception as e:
            logger.error(f"Error getting agent performance: {e}")
            return []
    
    async def get_agent_metrics(self, agent_id: str) -> Optional[AgentMetrics]:
        """Get detailed metrics for a specific agent"""
        try:
            # Get metrics from performance monitor
            metrics_data = await self.performance_monitor.get_agent_metrics(agent_id)
            
            if not metrics_data:
                return None
            
            return AgentMetrics(
                agent_id=agent_id,
                agent_type=AgentType(metrics_data.get("agent_type", "tier1_support")),
                total_conversations=metrics_data.get("total_conversations", 0),
                active_conversations=metrics_data.get("active_conversations", 0),
                avg_response_time=metrics_data.get("avg_response_time", 0.0),
                avg_resolution_time=metrics_data.get("avg_resolution_time", 0.0),
                successful_resolutions=metrics_data.get("successful_resolutions", 0),
                escalation_count=metrics_data.get("escalation_count", 0),
                avg_customer_satisfaction=metrics_data.get("avg_customer_satisfaction", 0.0),
                error_rate=metrics_data.get("error_rate", 0.0),
                avg_confidence_score=metrics_data.get("avg_confidence_score", 0.0),
                tools_usage=metrics_data.get("tools_usage", {}),
                updated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error getting agent metrics for {agent_id}: {e}")
            return None
    
    async def get_agent_status(
        self,
        agent_type: Optional[AgentType] = None
    ) -> List[AgentState]:
        """Get current status of all agents or filtered by type"""
        try:
            agent_states = []
            
            for agent_id, agent_state in self.agent_registry.items():
                if agent_type is None or agent_state.agent_type == agent_type:
                    # Update current load and health check
                    await self._update_agent_health(agent_state)
                    agent_states.append(agent_state)
            
            return agent_states
            
        except Exception as e:
            logger.error(f"Error getting agent status: {e}")
            return []
    
    async def reload_agent(self, agent_id: str) -> bool:
        """Reload an agent's configuration and models"""
        try:
            logger.info(f"Reloading agent {agent_id}")
            
            # Get agent from registry
            if agent_id not in self.agent_registry:
                logger.error(f"Agent {agent_id} not found in registry")
                return False
            
            agent_state = self.agent_registry[agent_id]
            
            # Update status to maintenance
            agent_state.status = AgentStatus.MAINTENANCE
            agent_state.last_active = datetime.utcnow()
            
            # Reload configuration
            await self._reload_agent_configuration(agent_state)
            
            # Update health check
            await self._update_agent_health(agent_state)
            
            # Set status back to available if healthy
            if agent_state.health_check.get("status") == "healthy":
                agent_state.status = AgentStatus.AVAILABLE
            else:
                agent_state.status = AgentStatus.ERROR
            
            logger.info(f"Agent {agent_id} reloaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error reloading agent {agent_id}: {e}")
            return False
    
    async def stop_agent(self, agent_id: str) -> bool:
        """Stop an agent's operations"""
        try:
            logger.info(f"Stopping agent {agent_id}")
            
            # Get agent from registry
            if agent_id not in self.agent_registry:
                logger.error(f"Agent {agent_id} not found in registry")
                return False
            
            agent_state = self.agent_registry[agent_id]
            
            # Update status to disabled
            agent_state.status = AgentStatus.DISABLED
            agent_state.last_active = datetime.utcnow()
            agent_state.current_conversations = []
            agent_state.current_load = 0.0
            
            # Log the stop event
            await self.performance_monitor.log_agent_event(
                agent_id=agent_id,
                event_type="agent_stopped",
                details={"timestamp": datetime.utcnow().isoformat()}
            )
            
            logger.info(f"Agent {agent_id} stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping agent {agent_id}: {e}")
            return False
    
    async def start_agent(self, agent_id: str) -> bool:
        """Start an agent's operations"""
        try:
            logger.info(f"Starting agent {agent_id}")
            
            # Get agent from registry
            if agent_id not in self.agent_registry:
                logger.error(f"Agent {agent_id} not found in registry")
                return False
            
            agent_state = self.agent_registry[agent_id]
            
            # Update health check
            await self._update_agent_health(agent_state)
            
            # Set status based on health
            if agent_state.health_check.get("status") == "healthy":
                agent_state.status = AgentStatus.AVAILABLE
            else:
                agent_state.status = AgentStatus.ERROR
            
            agent_state.last_active = datetime.utcnow()
            
            # Log the start event
            await self.performance_monitor.log_agent_event(
                agent_id=agent_id,
                event_type="agent_started",
                details={"timestamp": datetime.utcnow().isoformat()}
            )
            
            logger.info(f"Agent {agent_id} started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting agent {agent_id}: {e}")
            return False
    
    async def get_agent_configuration(self, agent_type: AgentType) -> Optional[AgentConfiguration]:
        """Get configuration for an agent type"""
        return self.agent_configs.get(agent_type)
    
    async def update_agent_configuration(
        self,
        agent_type: AgentType,
        configuration: AgentConfiguration
    ) -> bool:
        """Update configuration for an agent type"""
        try:
            self.agent_configs[agent_type] = configuration
            
            # Reload all agents of this type
            agents_to_reload = [
                agent_id for agent_id, agent_state in self.agent_registry.items()
                if agent_state.agent_type == agent_type
            ]
            
            for agent_id in agents_to_reload:
                await self.reload_agent(agent_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating agent configuration for {agent_type}: {e}")
            return False
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        try:
            health_status = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "agent_summary": {
                    "total_agents": len(self.agent_registry),
                    "available_agents": 0,
                    "busy_agents": 0,
                    "error_agents": 0,
                    "disabled_agents": 0
                },
                "performance_summary": {
                    "total_conversations": 0,
                    "active_conversations": 0,
                    "avg_response_time": 0.0,
                    "system_load": 0.0
                }
            }
            
            # Count agent statuses
            for agent_state in self.agent_registry.values():
                if agent_state.status == AgentStatus.AVAILABLE:
                    health_status["agent_summary"]["available_agents"] += 1
                elif agent_state.status == AgentStatus.BUSY:
                    health_status["agent_summary"]["busy_agents"] += 1
                elif agent_state.status == AgentStatus.ERROR:
                    health_status["agent_summary"]["error_agents"] += 1
                elif agent_state.status == AgentStatus.DISABLED:
                    health_status["agent_summary"]["disabled_agents"] += 1
                
                # Accumulate performance data
                health_status["performance_summary"]["active_conversations"] += len(agent_state.current_conversations)
                health_status["performance_summary"]["system_load"] += agent_state.current_load
            
            # Calculate averages
            total_agents = len(self.agent_registry)
            if total_agents > 0:
                health_status["performance_summary"]["system_load"] /= total_agents
            
            # Determine overall status
            error_agents = health_status["agent_summary"]["error_agents"]
            if error_agents > total_agents * 0.5:
                health_status["status"] = "critical"
            elif error_agents > 0:
                health_status["status"] = "degraded"
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    # Private helper methods
    async def _load_agent_configurations(self):
        """Load agent configurations"""
        # Default configurations for each agent type
        self.agent_configs = {
            AgentType.INTENT_CLASSIFIER: AgentConfiguration(
                agent_type=AgentType.INTENT_CLASSIFIER,
                model_name="gemini-pro",
                model_version="1.0",
                capabilities=[
                    AgentCapability(
                        name="intent_classification",
                        description="Classify customer intent from messages",
                        confidence_threshold=0.85,
                        requires_tools=["nlp_processor"],
                        supported_languages=["en", "es", "fr"]
                    )
                ],
                max_concurrent_conversations=100,
                response_timeout=5,
                escalation_threshold=0.7,
                tools_allowed=["nlp_processor", "knowledge_search"]
            ),
            AgentType.TIER1_SUPPORT: AgentConfiguration(
                agent_type=AgentType.TIER1_SUPPORT,
                model_name="gemini-pro",
                model_version="1.0",
                capabilities=[
                    AgentCapability(
                        name="basic_support",
                        description="Handle basic customer support queries",
                        confidence_threshold=0.75,
                        requires_tools=["knowledge_base", "faq_search"],
                        supported_languages=["en"]
                    )
                ],
                max_concurrent_conversations=20,
                response_timeout=30,
                escalation_threshold=0.6,
                tools_allowed=["knowledge_base", "faq_search", "ticket_creation"]
            ),
            AgentType.TIER2_TECHNICAL: AgentConfiguration(
                agent_type=AgentType.TIER2_TECHNICAL,
                model_name="claude-3",
                model_version="1.0",
                capabilities=[
                    AgentCapability(
                        name="technical_support",
                        description="Handle technical issues and troubleshooting",
                        confidence_threshold=0.8,
                        requires_tools=["diagnostic_tools", "system_logs"],
                        supported_languages=["en"]
                    )
                ],
                max_concurrent_conversations=15,
                response_timeout=60,
                escalation_threshold=0.7,
                tools_allowed=["diagnostic_tools", "system_logs", "configuration_tools"]
            ),
            AgentType.SALES: AgentConfiguration(
                agent_type=AgentType.SALES,
                model_name="gemini-pro",
                model_version="1.0",
                capabilities=[
                    AgentCapability(
                        name="sales_assistance",
                        description="Handle sales inquiries and product information",
                        confidence_threshold=0.8,
                        requires_tools=["product_catalog", "pricing_tools"],
                        supported_languages=["en"]
                    )
                ],
                max_concurrent_conversations=25,
                response_timeout=45,
                escalation_threshold=0.6,
                tools_allowed=["product_catalog", "pricing_tools", "quote_generation"]
            ),
            AgentType.BILLING: AgentConfiguration(
                agent_type=AgentType.BILLING,
                model_name="gemini-pro",
                model_version="1.0",
                capabilities=[
                    AgentCapability(
                        name="billing_support",
                        description="Handle billing inquiries and payment issues",
                        confidence_threshold=0.85,
                        requires_tools=["billing_system", "payment_processor"],
                        supported_languages=["en"]
                    )
                ],
                max_concurrent_conversations=20,
                response_timeout=30,
                escalation_threshold=0.7,
                tools_allowed=["billing_system", "payment_processor", "refund_tools"]
            ),
            AgentType.SUPERVISOR: AgentConfiguration(
                agent_type=AgentType.SUPERVISOR,
                model_name="claude-3",
                model_version="1.0",
                capabilities=[
                    AgentCapability(
                        name="supervision",
                        description="Handle escalations and complex routing decisions",
                        confidence_threshold=0.9,
                        requires_tools=["all_tools"],
                        supported_languages=["en"]
                    )
                ],
                max_concurrent_conversations=10,
                response_timeout=60,
                escalation_threshold=0.8,
                tools_allowed=["all_tools"]
            )
        }
    
    async def _initialize_agent_registry(self):
        """Initialize agent registry with default agents"""
        for agent_type, config in self.agent_configs.items():
            # Create multiple instances based on expected load
            instances_count = self._get_agent_instances_count(agent_type)
            
            for i in range(instances_count):
                agent_id = f"{agent_type.value}_{i}"
                
                agent_state = AgentState(
                    agent_id=agent_id,
                    agent_type=agent_type,
                    status=AgentStatus.AVAILABLE,
                    current_conversations=[],
                    last_active=datetime.utcnow(),
                    health_check={"status": "healthy", "last_check": datetime.utcnow().isoformat()},
                    current_load=0.0,
                    metadata={"configuration": config.dict()}
                )
                
                self.agent_registry[agent_id] = agent_state
    
    def _get_agent_instances_count(self, agent_type: AgentType) -> int:
        """Determine number of instances to create for each agent type"""
        instance_counts = {
            AgentType.INTENT_CLASSIFIER: 3,
            AgentType.TIER1_SUPPORT: 5,
            AgentType.TIER2_TECHNICAL: 3,
            AgentType.TIER3_EXPERT: 2,
            AgentType.SALES: 3,
            AgentType.BILLING: 3,
            AgentType.SUPERVISOR: 2
        }
        
        return instance_counts.get(agent_type, 1)
    
    async def _update_agent_health(self, agent_state: AgentState):
        """Update agent health check information"""
        try:
            health_check = {
                "status": "healthy",
                "last_check": datetime.utcnow().isoformat(),
                "response_time": await self._check_agent_response_time(agent_state.agent_id),
                "memory_usage": await self._check_agent_memory_usage(agent_state.agent_id),
                "error_count": await self._get_agent_error_count(agent_state.agent_id)
            }
            
            # Determine health status
            if health_check["error_count"] > 10:
                health_check["status"] = "unhealthy"
            elif health_check["response_time"] > 10.0:
                health_check["status"] = "degraded"
            elif health_check["memory_usage"] > 90.0:
                health_check["status"] = "degraded"
            
            agent_state.health_check = health_check
            agent_state.current_load = len(agent_state.current_conversations) / self.agent_configs[agent_state.agent_type].max_concurrent_conversations * 100
            
        except Exception as e:
            logger.error(f"Error updating health for agent {agent_state.agent_id}: {e}")
            agent_state.health_check = {
                "status": "error",
                "last_check": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    async def _check_agent_response_time(self, agent_id: str) -> float:
        """Check agent response time"""
        # This would typically ping the agent or check recent performance
        return 1.5  # Mock response time
    
    async def _check_agent_memory_usage(self, agent_id: str) -> float:
        """Check agent memory usage"""
        # This would typically check actual memory usage
        return 45.0  # Mock memory usage percentage
    
    async def _get_agent_error_count(self, agent_id: str) -> int:
        """Get recent error count for agent"""
        # This would typically check error logs
        return 0  # Mock error count
    
    async def _reload_agent_configuration(self, agent_state: AgentState):
        """Reload configuration for a specific agent"""
        try:
            config = self.agent_configs.get(agent_state.agent_type)
            if config:
                agent_state.metadata["configuration"] = config.dict()
                agent_state.metadata["last_reload"] = datetime.utcnow().isoformat()
                
        except Exception as e:
            logger.error(f"Error reloading configuration for agent {agent_state.agent_id}: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup agent service resources"""
        try:
            logger.info("Cleaning up Agent Service...")
            
            # Stop all agents
            for agent_id in list(self.agent_registry.keys()):
                await self.stop_agent(agent_id)
            
            # Clear registry
            self.agent_registry.clear()
            
            # Cleanup orchestrator
            if self.agent_orchestrator:
                await self.agent_orchestrator.cleanup()
            
            # Cleanup performance monitor
            if self.performance_monitor:
                await self.performance_monitor.cleanup()
            
            self.initialized = False
            logger.info("Agent Service cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during agent service cleanup: {e}")
            raise


# Dependency injection function
async def get_agent_service() -> AgentService:
    """Get agent service instance"""
    service = AgentService()
    if not service.initialized:
        await service.initialize()
    return service