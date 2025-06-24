"""
Tier 2 Technical Agent for Contact Center Agentic Flow System
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from src.agents.base_agent import BaseAgent
from src.models.state import AgentState, TicketStatus, Sentiment, Priority
from src.core.logging import get_logger

logger = get_logger(__name__)


class Tier2TechnicalAgent(BaseAgent):
    """Agent specialized in advanced technical support and complex troubleshooting"""
    
    def __init__(
        self,
        name: str,
        model: str,
        capabilities: List[str],
        tools: List[str],
        confidence_threshold: float = 0.8
    ):
        super().__init__(name, model, capabilities, tools, confidence_threshold)
        
        # Advanced diagnostic procedures
        self.diagnostic_procedures = self._initialize_diagnostic_procedures()
        
        # System configuration guides
        self.configuration_guides = self._initialize_configuration_guides()
        
        # Integration troubleshooting
        self.integration_guides = self._initialize_integration_guides()
        
        # Performance optimization guides
        self.performance_guides = self._initialize_performance_guides()
    
    async def handle_message(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Handle Tier 2 technical support interactions"""
        try:
            logger.info(f"Tier 2 technical agent handling message for conversation {state.conversation_id}")
            
            # Analyze technical complexity
            complexity_analysis = await self._analyze_technical_complexity(message, state)
            
            # Determine technical approach
            technical_approach = await self._determine_technical_approach(message, state, complexity_analysis)
            
            # Execute technical support action
            response = await self._execute_technical_support(technical_approach, message, state)
            
            # Check if escalation to Tier 3 is needed
            needs_escalation = await self._check_tier3_escalation_needed(response, state)
            
            return {
                "message": response["message"],
                "confidence": response["confidence"],
                "success": response["success"],
                "resolution_attempt": True,
                "actions_taken": response["actions_taken"],
                "tools_used": response["tools_used"],
                "outcome": response["outcome"],
                "new_status": TicketStatus.RESOLVED if response["success"] and not needs_escalation else TicketStatus.IN_PROGRESS,
                "requires_escalation": needs_escalation,
                "technical_approach": technical_approach,
                "complexity_level": complexity_analysis["level"],
                "diagnostic_results": response.get("diagnostic_results", {}),
                "next_steps": response.get("next_steps", []),
                "estimated_resolution_time": response.get("estimated_time", "30-60 minutes")
            }
            
        except Exception as e:
            logger.error(f"Tier 2 technical agent error: {e}")
            return {
                "message": "I'm experiencing technical difficulties analyzing your issue. Let me escalate this to our senior technical team to ensure you get the expert help you need.",
                "confidence": 0.0,
                "success": False,
                "resolution_attempt": True,
                "actions_taken": ["error_handling"],
                "tools_used": [],
                "outcome": "agent_error",
                "requires_escalation": True,
                "error": str(e)
            }
    
    async def can_handle(self, state: AgentState) -> bool:
        """Determine if this agent can handle the current state"""
        # Technical intents that Tier 2 can handle
        tier2_intents = [
            "technical_support", "integration_issue", "performance_issue",
            "configuration_problem", "api_issue", "system_error"
        ]
        
        # Check if intent is technical
        can_handle_intent = (
            state.current_intent in tier2_intents or
            "technical" in state.current_intent.lower()
        )
        
        # Check if escalated from Tier 1
        escalated_from_tier1 = (
            state.escalation_level > 0 and
            any("tier1" in agent.lower() for agent in state.previous_agents)
        )
        
        # Check if not requiring system-level changes
        not_system_level = state.escalation_level < 2
        
        return can_handle_intent or escalated_from_tier1 and not_system_level
    
    def _get_agent_permissions(self) -> List[str]:
        """Get the permissions available to this agent"""
        return [
            "read_customer_data",
            "read_system_logs",
            "run_diagnostics",
            "access_configuration",
            "update_system_settings",
            "schedule_maintenance",
            "create_technical_tickets",
            "access_similar_cases"
        ]
    
    def _initialize_diagnostic_procedures(self) -> Dict[str, Dict[str, Any]]:
        """Initialize advanced diagnostic procedures"""
        return {
            "connectivity_diagnosis": {
                "steps": [
                    "Check network connectivity and latency",
                    "Verify DNS resolution",
                    "Test firewall and port configurations",
                    "Analyze routing tables",
                    "Check SSL/TLS certificate validity"
                ],
                "tools": ["connectivity_test", "dns_lookup", "port_scan", "ssl_check"],
                "estimated_time": "15-20 minutes"
            },
            "performance_diagnosis": {
                "steps": [
                    "Analyze system resource utilization",
                    "Check database query performance",
                    "Review application logs for bottlenecks",
                    "Examine cache hit rates",
                    "Monitor memory and CPU usage patterns"
                ],
                "tools": ["performance_monitor", "query_analyzer", "log_analyzer", "resource_monitor"],
                "estimated_time": "20-30 minutes"
            },
            "integration_diagnosis": {
                "steps": [
                    "Verify API endpoint availability",
                    "Check authentication credentials",
                    "Validate data format and structure",
                    "Test timeout and retry mechanisms",
                    "Review integration logs"
                ],
                "tools": ["api_test", "auth_validator", "data_validator", "integration_monitor"],
                "estimated_time": "25-35 minutes"
            },
            "error_analysis": {
                "steps": [
                    "Collect and analyze error logs",
                    "Identify error patterns and frequency",
                    "Trace error propagation",
                    "Check for known issues and solutions",
                    "Validate error handling mechanisms"
                ],
                "tools": ["log_analyzer", "error_tracker", "pattern_analyzer", "knowledge_search"],
                "estimated_time": "20-25 minutes"
            }
        }
    
    def _initialize_configuration_guides(self) -> Dict[str, Dict[str, Any]]:
        """Initialize system configuration guides"""
        return {
            "network_configuration": {
                "areas": ["firewall_rules", "load_balancer", "dns_settings", "ssl_certificates"],
                "validation_steps": [
                    "Test network connectivity",
                    "Verify security policies",
                    "Check configuration syntax",
                    "Validate against best practices"
                ]
            },
            "application_configuration": {
                "areas": ["environment_variables", "database_connections", "api_endpoints", "caching_settings"],
                "validation_steps": [
                    "Check configuration file syntax",
                    "Validate database connectivity",
                    "Test API endpoint responses",
                    "Verify cache functionality"
                ]
            },
            "security_configuration": {
                "areas": ["authentication", "authorization", "encryption", "audit_logging"],
                "validation_steps": [
                    "Test authentication mechanisms",
                    "Verify permission matrices",
                    "Check encryption settings",
                    "Validate audit log generation"
                ]
            }
        }
    
    def _initialize_integration_guides(self) -> Dict[str, Dict[str, Any]]:
        """Initialize integration troubleshooting guides"""
        return {
            "api_integration": {
                "common_issues": [
                    "Authentication failures",
                    "Rate limiting",
                    "Timeout errors",
                    "Data format mismatches",
                    "Version incompatibilities"
                ],
                "resolution_steps": [
                    "Verify API credentials and tokens",
                    "Check rate limits and quotas",
                    "Adjust timeout settings",
                    "Validate request/response formats",
                    "Review API version compatibility"
                ]
            },
            "database_integration": {
                "common_issues": [
                    "Connection pool exhaustion",
                    "Query performance issues",
                    "Schema mismatches",
                    "Transaction deadlocks",
                    "Replication lag"
                ],
                "resolution_steps": [
                    "Analyze connection pool configuration",
                    "Optimize slow queries",
                    "Validate schema versions",
                    "Review transaction isolation levels",
                    "Check replication status"
                ]
            },
            "third_party_integration": {
                "common_issues": [
                    "Service unavailability",
                    "Configuration drift",
                    "Certificate expiration",
                    "Protocol mismatches",
                    "Data synchronization issues"
                ],
                "resolution_steps": [
                    "Check service health status",
                    "Validate configuration settings",
                    "Verify certificate validity",
                    "Confirm protocol compatibility",
                    "Analyze sync mechanisms"
                ]
            }
        }
    
    def _initialize_performance_guides(self) -> Dict[str, Dict[str, Any]]:
        """Initialize performance optimization guides"""
        return {
            "application_performance": {
                "optimization_areas": [
                    "Code optimization",
                    "Database query tuning",
                    "Caching strategies",
                    "Resource allocation",
                    "Asynchronous processing"
                ],
                "metrics_to_monitor": [
                    "Response time",
                    "Throughput",
                    "Error rate",
                    "Resource utilization",
                    "Concurrent users"
                ]
            },
            "system_performance": {
                "optimization_areas": [
                    "Memory management",
                    "CPU utilization",
                    "Disk I/O optimization",
                    "Network optimization",
                    "Load balancing"
                ],
                "metrics_to_monitor": [
                    "Memory usage",
                    "CPU load",
                    "Disk latency",
                    "Network throughput",
                    "Load distribution"
                ]
            }
        }
    
    async def _analyze_technical_complexity(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Analyze the technical complexity of the issue"""
        complexity_indicators = {
            "high": [
                "system-wide", "multiple services", "data corruption", "security breach",
                "performance degradation", "integration failure", "architecture"
            ],
            "medium": [
                "configuration", "setup", "integration", "performance", "error messages",
                "logs", "monitoring", "alerts"
            ],
            "low": [
                "single feature", "user interface", "minor bug", "cosmetic issue"
            ]
        }
        
        message_lower = message.lower()
        complexity_scores = {"low": 0, "medium": 0, "high": 0}
        
        for level, indicators in complexity_indicators.items():
            for indicator in indicators:
                if indicator in message_lower:
                    complexity_scores[level] += 1
        
        # Determine complexity level
        max_level = max(complexity_scores, key=complexity_scores.get)
        confidence = min(complexity_scores[max_level] / 3.0, 1.0) if complexity_scores[max_level] > 0 else 0.5
        
        return {
            "level": max_level,
            "confidence": confidence,
            "indicators_found": complexity_scores,
            "requires_deep_analysis": complexity_scores["high"] > 0
        }
    
    async def _determine_technical_approach(
        self, 
        message: str, 
        state: AgentState, 
        complexity_analysis: Dict[str, Any]
    ) -> str:
        """Determine the technical approach based on the issue"""
        message_lower = message.lower()
        
        # Map keywords to technical approaches
        if any(word in message_lower for word in ["connect", "network", "timeout", "unreachable"]):
            return "connectivity_diagnosis"
        elif any(word in message_lower for word in ["slow", "performance", "lag", "latency"]):
            return "performance_diagnosis"
        elif any(word in message_lower for word in ["integration", "api", "webhook", "sync"]):
            return "integration_diagnosis"
        elif any(word in message_lower for word in ["error", "exception", "crash", "failure"]):
            return "error_analysis"
        elif any(word in message_lower for word in ["config", "setting", "parameter"]):
            return "configuration_analysis"
        else:
            return "general_technical_analysis"
    
    async def _execute_technical_support(
        self, 
        approach: str, 
        message: str, 
        state: AgentState
    ) -> Dict[str, Any]:
        """Execute the technical support approach"""
        
        if approach in self.diagnostic_procedures:
            return await self._execute_diagnostic_procedure(approach, state)
        elif approach == "configuration_analysis":
            return await self._execute_configuration_analysis(message, state)
        elif approach == "general_technical_analysis":
            return await self._execute_general_technical_analysis(message, state)
        else:
            return await self._execute_fallback_technical_support(message, state)
    
    async def _execute_diagnostic_procedure(self, procedure_name: str, state: AgentState) -> Dict[str, Any]:
        """Execute a specific diagnostic procedure"""
        procedure = self.diagnostic_procedures[procedure_name]
        tools_used = []
        diagnostic_results = {}
        
        try:
            # Execute diagnostic tools
            for tool_name in procedure["tools"]:
                try:
                    if tool_name == "run_diagnostic_test":
                        result = await self.use_tool(
                            "run_diagnostic_test",
                            {
                                "customer_id": state.customer.customer_id if state.customer else "",
                                "test_type": procedure_name,
                                "parameters": {"comprehensive": True}
                            },
                            self.get_agent_context(state)
                        )
                        diagnostic_results[tool_name] = result
                        tools_used.append(tool_name)
                    elif tool_name == "check_system_logs":
                        result = await self.use_tool(
                            "check_system_logs",
                            {
                                "customer_id": state.customer.customer_id if state.customer else "",
                                "log_type": "application",
                                "time_range": "1h"
                            },
                            self.get_agent_context(state)
                        )
                        diagnostic_results[tool_name] = result
                        tools_used.append(tool_name)
                except Exception as e:
                    logger.warning(f"Failed to execute tool {tool_name}: {e}")
            
            # Get similar cases for reference
            try:
                similar_cases = await self.use_tool(
                    "get_similar_cases",
                    {
                        "issue_type": procedure_name,
                        "customer_tier": state.customer.tier.value if state.customer else "bronze",
                        "limit": 5
                    },
                    self.get_agent_context(state)
                )
                diagnostic_results["similar_cases"] = similar_cases
                tools_used.append("get_similar_cases")
            except Exception as e:
                logger.warning(f"Failed to get similar cases: {e}")
            
            # Analyze diagnostic results
            analysis_summary = await self._analyze_diagnostic_results(diagnostic_results, procedure_name)
            
            # Generate response
            response_message = f"I've completed a comprehensive {procedure_name.replace('_', ' ')} analysis. "
            
            if analysis_summary["issues_found"]:
                response_message += f"I found {len(analysis_summary['issues_found'])} potential issues:\n\n"
                for i, issue in enumerate(analysis_summary["issues_found"], 1):
                    response_message += f"{i}. {issue['description']}\n"
                    if issue.get("solution"):
                        response_message += f"   Solution: {issue['solution']}\n"
                
                response_message += f"\nI can help resolve these issues. This will take approximately {procedure['estimated_time']}."
            else:
                response_message += "The diagnostic tests show your system is functioning normally. "
                response_message += "Let me investigate further to identify the root cause of your issue."
            
            return {
                "message": response_message,
                "confidence": 0.85 if analysis_summary["issues_found"] else 0.6,
                "success": len(analysis_summary["issues_found"]) > 0,
                "actions_taken": [f"executed_{procedure_name}"],
                "tools_used": tools_used,
                "outcome": "diagnostic_completed",
                "diagnostic_results": diagnostic_results,
                "issues_found": analysis_summary["issues_found"],
                "estimated_time": procedure["estimated_time"]
            }
            
        except Exception as e:
            logger.error(f"Diagnostic procedure {procedure_name} failed: {e}")
            return {
                "message": f"I encountered an issue while running the {procedure_name.replace('_', ' ')} diagnostic. Let me escalate this to our senior technical team for advanced analysis.",
                "confidence": 0.0,
                "success": False,
                "actions_taken": [f"failed_{procedure_name}"],
                "tools_used": tools_used,
                "outcome": "diagnostic_error",
                "requires_escalation": True
            }
    
    async def _execute_configuration_analysis(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Execute configuration analysis"""
        tools_used = []
        
        try:
            # Check system configuration
            config_result = await self.use_tool(
                "check_system_logs",
                {
                    "customer_id": state.customer.customer_id if state.customer else "",
                    "log_type": "configuration",
                    "time_range": "24h"
                },
                self.get_agent_context(state)
            )
            tools_used.append("check_system_logs")
            
            # Analyze configuration issues
            config_analysis = await self._analyze_configuration_logs(config_result)
            
            response_message = "I've analyzed your system configuration. "
            
            if config_analysis["issues_found"]:
                response_message += f"I found {len(config_analysis['issues_found'])} configuration issues that need attention:\n\n"
                for i, issue in enumerate(config_analysis["issues_found"], 1):
                    response_message += f"{i}. {issue}\n"
                
                response_message += "\nI can help you resolve these configuration issues step by step."
            else:
                response_message += "Your configuration appears to be correct. Let me investigate other potential causes."
            
            return {
                "message": response_message,
                "confidence": 0.8,
                "success": True,
                "actions_taken": ["configuration_analysis"],
                "tools_used": tools_used,
                "outcome": "configuration_analyzed",
                "estimated_time": "20-30 minutes"
            }
            
        except Exception as e:
            logger.error(f"Configuration analysis failed: {e}")
            return {
                "message": "I'm having trouble accessing configuration data. Let me escalate this to ensure you get the technical support you need.",
                "confidence": 0.0,
                "success": False,
                "actions_taken": ["configuration_analysis_failed"],
                "tools_used": tools_used,
                "outcome": "analysis_error",
                "requires_escalation": True
            }
    
    async def _execute_general_technical_analysis(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Execute general technical analysis"""
        tools_used = []
        
        try:
            # Search for similar technical issues
            similar_cases = await self.use_tool(
                "get_similar_cases",
                {
                    "issue_description": message,
                    "category": "technical",
                    "limit": 10
                },
                self.get_agent_context(state)
            )
            tools_used.append("get_similar_cases")
            
            # Run basic diagnostic
            diagnostic_result = await self.use_tool(
                "run_diagnostic_test",
                {
                    "customer_id": state.customer.customer_id if state.customer else "",
                    "test_type": "general_health_check",
                    "parameters": {"basic": True}
                },
                self.get_agent_context(state)
            )
            tools_used.append("run_diagnostic_test")
            
            response_message = "I've performed a technical analysis of your issue. "
            
            if similar_cases.get("success") and similar_cases.get("results"):
                best_match = similar_cases["results"][0]
                response_message += f"I found a similar case that was resolved successfully. "
                response_message += f"The solution involved: {best_match.get('resolution_summary', 'technical adjustments')}.\n\n"
                response_message += "Let me apply this solution to your specific situation."
                confidence = 0.75
            else:
                response_message += "This appears to be a unique technical issue. "
                response_message += "I'll need to perform a more detailed analysis to identify the root cause."
                confidence = 0.6
            
            return {
                "message": response_message,
                "confidence": confidence,
                "success": True,
                "actions_taken": ["general_technical_analysis"],
                "tools_used": tools_used,
                "outcome": "analysis_completed",
                "estimated_time": "30-45 minutes"
            }
            
        except Exception as e:
            logger.error(f"General technical analysis failed: {e}")
            return {
                "message": "I'm having trouble performing the technical analysis. Let me escalate this to our senior technical team for advanced troubleshooting.",
                "confidence": 0.0,
                "success": False,
                "actions_taken": ["general_analysis_failed"],
                "tools_used": tools_used,
                "outcome": "analysis_error",
                "requires_escalation": True
            }
    
    async def _execute_fallback_technical_support(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Execute fallback technical support"""
        return {
            "message": "I understand you're experiencing a technical issue. Let me escalate this to our Tier 3 technical specialists who have advanced tools and expertise to resolve complex technical problems.",
            "confidence": 0.5,
            "success": False,
            "actions_taken": ["fallback_escalation"],
            "tools_used": [],
            "outcome": "escalation_required",
            "requires_escalation": True
        }
    
    async def _analyze_diagnostic_results(self, results: Dict[str, Any], procedure_name: str) -> Dict[str, Any]:
        """Analyze diagnostic results to identify issues"""
        issues_found = []
        
        # Analyze each diagnostic result
        for tool_name, result in results.items():
            if isinstance(result, dict) and result.get("success"):
                # Look for common issue patterns
                if "error" in str(result).lower():
                    issues_found.append({
                        "description": f"Error detected in {tool_name}",
                        "solution": "Investigate error logs and apply appropriate fix"
                    })
                elif "timeout" in str(result).lower():
                    issues_found.append({
                        "description": f"Timeout issue detected in {tool_name}",
                        "solution": "Optimize performance or increase timeout settings"
                    })
                elif "connection" in str(result).lower() and "failed" in str(result).lower():
                    issues_found.append({
                        "description": f"Connection issue detected in {tool_name}",
                        "solution": "Check network connectivity and firewall settings"
                    })
        
        return {
            "issues_found": issues_found,
            "analysis_confidence": 0.8 if issues_found else 0.5
        }
    
    async def _analyze_configuration_logs(self, config_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze configuration logs for issues"""
        issues_found = []
        
        if config_result.get("success") and config_result.get("logs"):
            logs = config_result["logs"]
            
            # Look for common configuration issues
            for log_entry in logs:
                log_message = str(log_entry).lower()
                
                if "deprecated" in log_message:
                    issues_found.append("Deprecated configuration settings detected")
                elif "invalid" in log_message:
                    issues_found.append("Invalid configuration parameters found")
                elif "missing" in log_message:
                    issues_found.append("Missing required configuration values")
                elif "permission" in log_message:
                    issues_found.append("Configuration permission issues")
        
        return {
            "issues_found": issues_found,
            "analysis_confidence": 0.7
        }
    
    async def _check_tier3_escalation_needed(self, response: Dict[str, Any], state: AgentState) -> bool:
        """Check if escalation to Tier 3 is needed"""
        escalation_triggers = [
            # Explicit escalation request
            response.get("requires_escalation", False),
            
            # Complex system-level issues
            response.get("complexity_level") == "high",
            
            # Multiple failed resolution attempts
            len(state.resolution_attempts) >= 3,
            
            # VIP customer with unresolved technical issue
            (state.customer and 
             state.customer.tier.value == "platinum" and
             not response.get("success", True)),
            
            # Critical priority issues
            (state.ticket and state.ticket.priority == Priority.CRITICAL),
            
            # System-wide impact suspected
            any(keyword in response.get("message", "").lower() 
                for keyword in ["system-wide", "architecture", "security", "compliance"])
        ]
        
        return any(escalation_triggers)