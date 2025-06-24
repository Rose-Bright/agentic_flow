from datetime import datetime
from typing import Dict, Any, List
from dataclasses import dataclass
from src.models.state import AgentState, Priority, CustomerTier, Sentiment, TicketStatus

@dataclass
class PerformanceMetrics:
    """Container for conversation performance metrics"""
    conversation_id: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    initial_response_time: float
    total_agent_responses: int
    resolution_time: float
    customer_sentiment_final: Sentiment
    resolution_success: bool
    escalation_count: int
    tools_used: List[str]
    agent_types_involved: List[str]

class PerformanceMonitor:
    """Monitors and analyzes system performance metrics"""
    
    def __init__(self):
        self.metrics_store = {}
        self.error_store = {}
        self.thresholds = self._initialize_thresholds()
        self.alert_manager = AlertManager()
    
    async def log_interaction(self, state: AgentState):
        """Log metrics for a conversation interaction"""
        
        # Calculate metrics for this interaction
        metrics = await self._calculate_interaction_metrics(state)
        
        # Store metrics
        self.metrics_store[state.conversation_id] = metrics
        
        # Check thresholds and send alerts if needed
        await self._check_thresholds(metrics)
        
        # Update real-time dashboard
        await self._update_dashboard(metrics)
    
    async def log_error(self, error_log: Dict[str, Any]):
        """Log error information for monitoring"""
        
        error_id = f"{error_log['conversation_id']}_{datetime.utcnow().isoformat()}"
        self.error_store[error_id] = error_log
        
        # Check if error requires immediate attention
        if await self._is_critical_error(error_log):
            await self.alert_manager.send_alert(
                level="critical",
                message=f"Critical error in conversation {error_log['conversation_id']}",
                details=error_log
            )
    
    async def get_performance_report(self, time_range: str = "1h") -> Dict[str, Any]:
        """Generate performance report for specified time range"""
        
        metrics = await self._aggregate_metrics(time_range)
        
        return {
            "time_range": time_range,
            "generated_at": datetime.utcnow().isoformat(),
            "metrics": {
                "average_response_time": metrics["avg_response_time"],
                "resolution_rate": metrics["resolution_rate"],
                "escalation_rate": metrics["escalation_rate"],
                "customer_satisfaction": metrics["customer_satisfaction"],
                "error_rate": metrics["error_rate"],
                "tool_usage": metrics["tool_usage"],
                "agent_performance": metrics["agent_performance"]
            },
            "alerts": await self._get_active_alerts(),
            "recommendations": await self._generate_recommendations(metrics)
        }
    
    def _initialize_thresholds(self) -> Dict[str, Any]:
        """Initialize monitoring thresholds"""
        return {
            "response_time": {
                "warning": 30.0,  # seconds
                "critical": 60.0
            },
            "resolution_time": {
                "warning": 600.0,  # 10 minutes
                "critical": 1800.0  # 30 minutes
            },
            "escalation_rate": {
                "warning": 0.15,  # 15%
                "critical": 0.25  # 25%
            },
            "error_rate": {
                "warning": 0.05,  # 5%
                "critical": 0.10  # 10%
            },
            "customer_satisfaction": {
                "warning": 3.5,  # out of 5
                "critical": 3.0
            }
        }
    
    async def _calculate_interaction_metrics(self, state: AgentState) -> Dict[str, Any]:
        """Calculate metrics for current interaction"""
        
        duration = (datetime.utcnow() - state.session_start).total_seconds()
        
        # Calculate response times
        response_times = []
        for i in range(1, len(state.conversation_history), 2):
            response_time = (
                state.conversation_history[i].timestamp -
                state.conversation_history[i-1].timestamp
            ).total_seconds()
            response_times.append(response_time)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "conversation_id": state.conversation_id,
            "duration": duration,
            "response_times": response_times,
            "avg_response_time": avg_response_time,
            "resolution_attempts": len(state.resolution_attempts),
            "escalation_count": len(state.escalation_history),
            "tools_used": len(state.tools_used),
            "sentiment_score": state.sentiment_score,
            "confidence_score": state.confidence_score,
            "status": state.status,
            "customer_tier": state.customer.tier if state.customer else None,
            "current_agent": state.current_agent_type
        }
    
    async def _check_thresholds(self, metrics: Dict[str, Any]):
        """Check if metrics exceed defined thresholds"""
        
        alerts = []
        
        # Check response time
        if metrics["avg_response_time"] > self.thresholds["response_time"]["critical"]:
            alerts.append({
                "level": "critical",
                "metric": "response_time",
                "value": metrics["avg_response_time"],
                "threshold": self.thresholds["response_time"]["critical"]
            })
        elif metrics["avg_response_time"] > self.thresholds["response_time"]["warning"]:
            alerts.append({
                "level": "warning",
                "metric": "response_time",
                "value": metrics["avg_response_time"],
                "threshold": self.thresholds["response_time"]["warning"]
            })
        
        # Check escalation rate
        escalation_rate = metrics["escalation_count"] / metrics["resolution_attempts"] \
            if metrics["resolution_attempts"] > 0 else 0
            
        if escalation_rate > self.thresholds["escalation_rate"]["critical"]:
            alerts.append({
                "level": "critical",
                "metric": "escalation_rate",
                "value": escalation_rate,
                "threshold": self.thresholds["escalation_rate"]["critical"]
            })
        
        # Send alerts if needed
        for alert in alerts:
            await self.alert_manager.send_alert(
                level=alert["level"],
                message=f"{alert['metric']} threshold exceeded",
                details=alert
            )
    
    async def _aggregate_metrics(self, time_range: str) -> Dict[str, Any]:
        """Aggregate metrics over specified time range"""
        
        # Convert time range to timedelta
        from datetime import timedelta
        range_mapping = {
            "1h": timedelta(hours=1),
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30)
        }
        time_delta = range_mapping.get(time_range, timedelta(hours=1))
        start_time = datetime.utcnow() - time_delta
        
        # Filter metrics within time range
        relevant_metrics = {
            k: v for k, v in self.metrics_store.items()
            if datetime.fromisoformat(v["timestamp"]) > start_time
        }
        
        # Calculate aggregated metrics
        total_conversations = len(relevant_metrics)
        if total_conversations == 0:
            return self._empty_metrics_template()
        
        aggregated = {
            "avg_response_time": sum(m["avg_response_time"] for m in relevant_metrics.values()) / total_conversations,
            "resolution_rate": len([m for m in relevant_metrics.values() if m["status"] == TicketStatus.RESOLVED]) / total_conversations,
            "escalation_rate": sum(m["escalation_count"] for m in relevant_metrics.values()) / total_conversations,
            "customer_satisfaction": sum(m["sentiment_score"] for m in relevant_metrics.values()) / total_conversations,
            "error_rate": len(self.error_store) / total_conversations,
            "tool_usage": self._aggregate_tool_usage(relevant_metrics),
            "agent_performance": self._aggregate_agent_performance(relevant_metrics)
        }
        
        return aggregated
    
    def _empty_metrics_template(self) -> Dict[str, Any]:
        """Return empty metrics template when no data available"""
        return {
            "avg_response_time": 0.0,
            "resolution_rate": 0.0,
            "escalation_rate": 0.0,
            "customer_satisfaction": 0.0,
            "error_rate": 0.0,
            "tool_usage": {},
            "agent_performance": {}
        }
    
    async def _is_critical_error(self, error_log: Dict[str, Any]) -> bool:
        """Determine if an error is critical"""
        critical_conditions = [
            error_log.get("error_type") in ["SystemError", "DatabaseError", "SecurityError"],
            error_log.get("customer_tier") == CustomerTier.PLATINUM,
            error_log.get("priority") == Priority.CRITICAL,
            "security" in error_log.get("error_message", "").lower(),
            "data_loss" in error_log.get("error_message", "").lower()
        ]
        
        return any(critical_conditions)

class AlertManager:
    """Manages alert generation and distribution"""
    
    async def send_alert(self, level: str, message: str, details: Dict[str, Any]):
        """Send alert to appropriate channels"""
        alert = {
            "level": level,
            "message": message,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # TODO: Implement actual alert distribution
        if level == "critical":
            # Send to urgent notification channel
            pass
        else:
            # Send to standard monitoring channel
            pass