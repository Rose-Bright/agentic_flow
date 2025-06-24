"""
Tier 3 Expert Agent for Contact Center Agentic Flow System
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from src.agents.base_agent import BaseAgent
from src.models.state import AgentState, TicketStatus, Priority, CustomerTier
from src.core.logging import get_logger

logger = get_logger(__name__)


class Tier3ExpertAgent(BaseAgent):
    """Agent specialized in critical issues, system modifications, and complex problem resolution"""
    
    def __init__(
        self,
        name: str,
        model: str,
        capabilities: List[str],
        tools: List[str],
        confidence_threshold: float = 0.9
    ):
        super().__init__(name, model, capabilities, tools, confidence_threshold)
        
        # Critical issue handling procedures
        self.critical_procedures = self._initialize_critical_procedures()
        
        # System modification protocols
        self.system_protocols = self._initialize_system_protocols()
        
        # Compliance and regulatory procedures
        self.compliance_procedures = self._initialize_compliance_procedures()
        
        # Executive escalation procedures
        self.executive_procedures = self._initialize_executive_procedures()
    
    async def handle_message(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Handle Tier 3 expert-level interactions"""
        try:
            logger.info(f"Tier 3 expert agent handling critical issue for conversation {state.conversation_id}")
            
            # Assess criticality and impact
            criticality_assessment = await self._assess_criticality(message, state)
            
            # Determine expert approach
            expert_approach = await self._determine_expert_approach(message, state, criticality_assessment)
            
            # Execute expert-level support
            response = await self._execute_expert_support(expert_approach, message, state)
            
            # Check if human escalation is needed
            needs_human_escalation = await self._check_human_escalation_needed(response, state)
            
            # Log critical action if needed
            if criticality_assessment["level"] == "critical":
                await self._log_critical_action(response, state)
            
            return {
                "message": response["message"],
                "confidence": response["confidence"],
                "success": response["success"],
                "resolution_attempt": True,
                "actions_taken": response["actions_taken"],
                "tools_used": response["tools_used"],
                "outcome": response["outcome"],
                "new_status": TicketStatus.RESOLVED if response["success"] and not needs_human_escalation else TicketStatus.ESCALATED,
                "requires_escalation": needs_human_escalation,
                "expert_approach": expert_approach,
                "criticality_level": criticality_assessment["level"],
                "impact_assessment": criticality_assessment["impact"],
                "next_steps": response.get("next_steps", []),
                "estimated_resolution_time": response.get("estimated_time", "1-4 hours"),
                "approval_required": response.get("approval_required", False)
            }
            
        except Exception as e:
            logger.error(f"Tier 3 expert agent error: {e}")
            return {
                "message": "I'm experiencing an issue analyzing this critical problem. I'm immediately escalating this to our human expert team and management to ensure your issue receives the highest priority attention.",
                "confidence": 0.0,
                "success": False,
                "resolution_attempt": True,
                "actions_taken": ["emergency_escalation"],
                "tools_used": [],
                "outcome": "agent_error",
                "requires_escalation": True,
                "criticality_level": "high",
                "error": str(e)
            }
    
    async def can_handle(self, state: AgentState) -> bool:
        """Determine if this agent can handle the current state"""
        # Critical intents that require Tier 3
        tier3_intents = [
            "system_modification", "security_issue", "compliance_issue",
            "data_breach", "system_outage", "architecture_change"
        ]
        
        # Check if intent requires Tier 3
        requires_tier3_intent = (
            state.current_intent in tier3_intents or
            any(keyword in state.current_intent.lower() 
                for keyword in ["critical", "system", "security", "compliance"])
        )
        
        # Check if escalated from Tier 2
        escalated_from_tier2 = (
            state.escalation_level >= 2 and
            any("tier2" in agent.lower() for agent in state.previous_agents)
        )
        
        # Check if VIP customer with high-impact issue
        vip_high_impact = (
            state.customer and
            state.customer.tier == CustomerTier.PLATINUM and
            state.ticket and
            state.ticket.priority in [Priority.HIGH, Priority.CRITICAL]
        )
        
        # Check if SLA breach risk
        sla_breach_risk = getattr(state, 'sla_breach_risk', False)
        
        return (requires_tier3_intent or escalated_from_tier2 or 
                vip_high_impact or sla_breach_risk)
    
    def _get_agent_permissions(self) -> List[str]:
        """Get the permissions available to this agent"""
        return [
            "all_customer_operations",
            "system_modifications",
            "security_operations",
            "compliance_operations",
            "executive_escalation",
            "emergency_procedures",
            "financial_adjustments",
            "service_modifications",
            "audit_log_access",
            "emergency_override"
        ]
    
    def _initialize_critical_procedures(self) -> Dict[str, Dict[str, Any]]:
        """Initialize critical issue handling procedures"""
        return {
            "system_outage": {
                "immediate_actions": [
                    "Activate incident response protocol",
                    "Notify system administrators",
                    "Begin impact assessment",
                    "Prepare customer communications",
                    "Establish incident command center"
                ],
                "priority": Priority.CRITICAL,
                "estimated_time": "30 minutes - 4 hours",
                "stakeholders": ["operations", "engineering", "management", "communications"]
            },
            "security_breach": {
                "immediate_actions": [
                    "Isolate affected systems",
                    "Begin forensic analysis",
                    "Notify security team",
                    "Assess data exposure",
                    "Prepare regulatory notifications"
                ],
                "priority": Priority.CRITICAL,
                "estimated_time": "1-8 hours",
                "stakeholders": ["security", "legal", "compliance", "management"]
            },
            "data_corruption": {
                "immediate_actions": [
                    "Stop data processing",
                    "Assess corruption extent",
                    "Initiate backup recovery",
                    "Verify data integrity",
                    "Plan recovery timeline"
                ],
                "priority": Priority.HIGH,
                "estimated_time": "2-6 hours",
                "stakeholders": ["database_admin", "engineering", "operations"]
            },
            "compliance_violation": {
                "immediate_actions": [
                    "Document violation details",
                    "Assess regulatory impact",
                    "Notify compliance team",
                    "Begin remediation plan",
                    "Prepare audit documentation"
                ],
                "priority": Priority.HIGH,
                "estimated_time": "1-4 hours",
                "stakeholders": ["compliance", "legal", "management", "audit"]
            }
        }
    
    def _initialize_system_protocols(self) -> Dict[str, Dict[str, Any]]:
        """Initialize system modification protocols"""
        return {
            "emergency_change": {
                "approval_required": True,
                "steps": [
                    "Document change justification",
                    "Assess impact and risks",
                    "Get emergency approval",
                    "Execute change with monitoring",
                    "Validate change success",
                    "Document post-change status"
                ],
                "rollback_plan": "required"
            },
            "configuration_update": {
                "approval_required": True,
                "steps": [
                    "Backup current configuration",
                    "Test configuration changes",
                    "Schedule maintenance window",
                    "Apply configuration updates",
                    "Verify system functionality",
                    "Monitor for issues"
                ],
                "rollback_plan": "automated"
            },
            "architecture_change": {
                "approval_required": True,
                "steps": [
                    "Create architecture proposal",
                    "Review with technical committee",
                    "Plan migration strategy",
                    "Execute phased implementation",
                    "Validate system performance",
                    "Complete documentation"
                ],
                "rollback_plan": "manual"
            }
        }
    
    def _initialize_compliance_procedures(self) -> Dict[str, Dict[str, Any]]:
        """Initialize compliance and regulatory procedures"""
        return {
            "gdpr_request": {
                "response_time": "72 hours",
                "steps": [
                    "Verify customer identity",
                    "Locate all customer data",
                    "Prepare data export/deletion",
                    "Execute request",
                    "Confirm completion",
                    "Document compliance"
                ],
                "documentation_required": True
            },
            "audit_preparation": {
                "response_time": "24 hours",
                "steps": [
                    "Gather audit requirements",
                    "Collect relevant documentation",
                    "Prepare system access",
                    "Schedule audit activities",
                    "Coordinate with stakeholders"
                ],
                "documentation_required": True
            },
            "regulatory_reporting": {
                "response_time": "depends on regulation",
                "steps": [
                    "Identify reporting requirements",
                    "Collect necessary data",
                    "Prepare report format",
                    "Review for accuracy",
                    "Submit to authorities",
                    "Maintain records"
                ],
                "documentation_required": True
            }
        }
    
    def _initialize_executive_procedures(self) -> Dict[str, Dict[str, Any]]:
        """Initialize executive escalation procedures"""
        return {
            "vip_escalation": {
                "notification_time": "immediate",
                "stakeholders": ["account_manager", "vp_customer_success", "ceo"],
                "communication_plan": "hourly updates until resolved"
            },
            "revenue_impact": {
                "notification_time": "15 minutes",
                "stakeholders": ["sales_director", "cfo", "ceo"],
                "impact_assessment": "required"
            },
            "media_attention": {
                "notification_time": "immediate",
                "stakeholders": ["pr_team", "legal", "ceo"],
                "response_plan": "coordinate with PR team"
            }
        }
    
    async def _assess_criticality(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Assess the criticality and impact of the issue"""
        message_lower = message.lower()
        
        # Critical keywords
        critical_keywords = [
            "system down", "outage", "security breach", "data loss", "hack",
            "compliance violation", "regulatory", "legal action", "lawsuit"
        ]
        
        high_keywords = [
            "urgent", "critical", "emergency", "escalate", "manager",
            "revenue loss", "business impact", "customers affected"
        ]
        
        # Score criticality
        critical_score = sum(1 for keyword in critical_keywords if keyword in message_lower)
        high_score = sum(1 for keyword in high_keywords if keyword in message_lower)
        
        # Customer tier impact
        tier_multiplier = 1.0
        if state.customer:
            if state.customer.tier == CustomerTier.PLATINUM:
                tier_multiplier = 2.0
            elif state.customer.tier == CustomerTier.GOLD:
                tier_multiplier = 1.5
        
        # Determine criticality level
        if critical_score > 0:
            level = "critical"
            impact = "system_wide"
        elif high_score > 1 or (high_score > 0 and tier_multiplier >= 1.5):
            level = "high"
            impact = "customer_specific"
        else:
            level = "medium"
            impact = "limited"
        
        return {
            "level": level,
            "impact": impact,
            "tier_multiplier": tier_multiplier,
            "critical_indicators": critical_score,
            "high_indicators": high_score
        }
    
    async def _determine_expert_approach(
        self, 
        message: str, 
        state: AgentState, 
        criticality: Dict[str, Any]
    ) -> str:
        """Determine the expert approach based on issue analysis"""
        message_lower = message.lower()
        
        # Map issues to expert approaches
        if any(word in message_lower for word in ["outage", "system down", "not working"]):
            return "system_outage"
        elif any(word in message_lower for word in ["security", "breach", "hack", "unauthorized"]):
            return "security_incident"
        elif any(word in message_lower for word in ["compliance", "gdpr", "audit", "regulation"]):
            return "compliance_issue"
        elif any(word in message_lower for word in ["data", "corruption", "loss", "backup"]):
            return "data_issue"
        elif any(word in message_lower for word in ["architecture", "design", "system change"]):
            return "architecture_change"
        elif criticality["level"] == "critical":
            return "critical_incident"
        else:
            return "expert_analysis"
    
    async def _execute_expert_support(
        self, 
        approach: str, 
        message: str, 
        state: AgentState
    ) -> Dict[str, Any]:
        """Execute expert-level support based on approach"""
        
        if approach in self.critical_procedures:
            return await self._handle_critical_procedure(approach, state)
        elif approach == "compliance_issue":
            return await self._handle_compliance_issue(message, state)
        elif approach == "security_incident":
            return await self._handle_security_incident(message, state)
        elif approach == "architecture_change":
            return await self._handle_architecture_change(message, state)
        else:
            return await self._handle_expert_analysis(message, state)
    
    async def _handle_critical_procedure(self, procedure_name: str, state: AgentState) -> Dict[str, Any]:
        """Handle critical procedures"""
        procedure = self.critical_procedures[procedure_name]
        tools_used = []
        
        try:
            # Log critical incident
            await self.use_tool(
                "audit_log_action",
                {
                    "action": f"critical_procedure_{procedure_name}",
                    "details": {
                        "procedure": procedure_name,
                        "customer_id": state.customer.customer_id if state.customer else None,
                        "conversation_id": state.conversation_id,
                        "priority": procedure["priority"].value
                    },
                    "severity": "critical"
                },
                self.get_agent_context(state)
            )
            tools_used.append("audit_log_action")
            
            # Check compliance requirements if needed
            if procedure_name in ["security_breach", "compliance_violation"]:
                compliance_check = await self.use_tool(
                    "check_compliance_requirements",
                    {
                        "incident_type": procedure_name,
                        "customer_tier": state.customer.tier.value if state.customer else "bronze"
                    },
                    self.get_agent_context(state)
                )
                tools_used.append("check_compliance_requirements")
            
            # Generate response
            response_message = f"I've initiated our {procedure_name.replace('_', ' ')} protocol. "
            response_message += "This is being treated as a critical incident with the highest priority.\n\n"
            
            response_message += "Immediate actions being taken:\n"
            for i, action in enumerate(procedure["immediate_actions"], 1):
                response_message += f"{i}. {action}\n"
            
            response_message += f"\nEstimated resolution time: {procedure['estimated_time']}\n"
            response_message += "You will receive regular updates every 30 minutes until this is resolved.\n"
            response_message += "A senior manager has been notified and will contact you directly."
            
            return {
                "message": response_message,
                "confidence": 0.95,
                "success": True,
                "actions_taken": [f"initiated_{procedure_name}_protocol"],
                "tools_used": tools_used,
                "outcome": "critical_procedure_initiated",
                "estimated_time": procedure["estimated_time"],
                "approval_required": False,
                "priority_escalation": True
            }
            
        except Exception as e:
            logger.error(f"Critical procedure {procedure_name} failed: {e}")
            return {
                "message": f"I'm having difficulty initiating the {procedure_name.replace('_', ' ')} protocol. I'm immediately escalating this to our emergency response team and senior management.",
                "confidence": 0.0,
                "success": False,
                "actions_taken": [f"failed_{procedure_name}_protocol"],
                "tools_used": tools_used,
                "outcome": "critical_procedure_error",
                "requires_escalation": True
            }
    
    async def _handle_compliance_issue(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Handle compliance-related issues"""
        tools_used = []
        
        try:
            # Check compliance requirements
            compliance_result = await self.use_tool(
                "check_compliance_requirements",
                {
                    "issue_description": message,
                    "customer_id": state.customer.customer_id if state.customer else "",
                    "jurisdiction": "all"
                },
                self.get_agent_context(state)
            )
            tools_used.append("check_compliance_requirements")
            
            # Log compliance action
            await self.use_tool(
                "audit_log_action",
                {
                    "action": "compliance_review",
                    "details": {
                        "issue": message[:200],
                        "customer_id": state.customer.customer_id if state.customer else None,
                        "compliance_requirements": compliance_result.get("requirements", [])
                    },
                    "severity": "high"
                },
                self.get_agent_context(state)
            )
            tools_used.append("audit_log_action")
            
            response_message = "I've reviewed your compliance-related concern and initiated our regulatory response protocol.\n\n"
            
            if compliance_result.get("success") and compliance_result.get("requirements"):
                requirements = compliance_result["requirements"]
                response_message += f"Based on our analysis, this involves {len(requirements)} compliance requirement(s):\n"
                for i, req in enumerate(requirements, 1):
                    response_message += f"{i}. {req.get('regulation', 'Regulatory requirement')}\n"
                
                response_message += "\nI'm coordinating with our compliance and legal teams to ensure full regulatory adherence. "
                response_message += "You will receive a comprehensive response within the required timeframe."
            else:
                response_message += "While I'm reviewing the specific compliance requirements, I've already engaged our compliance team. "
                response_message += "We take all regulatory matters seriously and will provide a complete response."
            
            return {
                "message": response_message,
                "confidence": 0.9,
                "success": True,
                "actions_taken": ["compliance_review_initiated"],
                "tools_used": tools_used,
                "outcome": "compliance_protocol_active",
                "estimated_time": "24-72 hours",
                "approval_required": True
            }
            
        except Exception as e:
            logger.error(f"Compliance issue handling failed: {e}")
            return {
                "message": "I'm having difficulty accessing our compliance systems. Given the regulatory nature of your concern, I'm immediately escalating this to our Chief Compliance Officer and legal team.",
                "confidence": 0.0,
                "success": False,
                "actions_taken": ["compliance_escalation"],
                "tools_used": tools_used,
                "outcome": "compliance_error",
                "requires_escalation": True
            }
    
    async def _handle_security_incident(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Handle security-related incidents"""
        tools_used = []
        
        try:
            # Log security incident
            await self.use_tool(
                "audit_log_action",
                {
                    "action": "security_incident_reported",
                    "details": {
                        "incident_description": message[:200],
                        "customer_id": state.customer.customer_id if state.customer else None,
                        "timestamp": datetime.now().isoformat(),
                        "reporter_tier": state.customer.tier.value if state.customer else "unknown"
                    },
                    "severity": "critical"
                },
                self.get_agent_context(state)
            )
            tools_used.append("audit_log_action")
            
            response_message = "I've received your security-related report and have immediately activated our security incident response protocol.\n\n"
            response_message += "Actions being taken right now:\n"
            response_message += "1. Security team has been notified\n"
            response_message += "2. Incident tracking has been initiated\n"
            response_message += "3. Preliminary security assessment is underway\n"
            response_message += "4. Senior security personnel are being briefed\n\n"
            response_message += "A security specialist will contact you within 15 minutes to discuss this matter in detail. "
            response_message += "Please do not share details of this security concern with anyone else at this time."
            
            return {
                "message": response_message,
                "confidence": 0.95,
                "success": True,
                "actions_taken": ["security_incident_protocol"],
                "tools_used": tools_used,
                "outcome": "security_protocol_active",
                "estimated_time": "immediate response - ongoing investigation",
                "approval_required": False,
                "priority_escalation": True
            }
            
        except Exception as e:
            logger.error(f"Security incident handling failed: {e}")
            return {
                "message": "Due to the security-sensitive nature of your report, I'm immediately connecting you with our Chief Security Officer. Please hold for immediate transfer.",
                "confidence": 0.0,
                "success": False,
                "actions_taken": ["emergency_security_escalation"],
                "tools_used": tools_used,
                "outcome": "security_emergency_escalation",
                "requires_escalation": True
            }
    
    async def _handle_architecture_change(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Handle architecture change requests"""
        tools_used = []
        
        try:
            response_message = "I understand you're requesting a system architecture change. "
            response_message += "This requires careful analysis and approval from our technical architecture committee.\n\n"
            response_message += "I'm initiating the architecture review process:\n"
            response_message += "1. Documenting your requirements\n"
            response_message += "2. Scheduling technical assessment\n"
            response_message += "3. Coordinating with architecture team\n"
            response_message += "4. Preparing impact analysis\n\n"
            response_message += "A senior solutions architect will contact you within 2 business hours to discuss your requirements in detail."
            
            return {
                "message": response_message,
                "confidence": 0.85,
                "success": True,
                "actions_taken": ["architecture_review_initiated"],
                "tools_used": tools_used,
                "outcome": "architecture_review_process",
                "estimated_time": "2-5 business days",
                "approval_required": True
            }
            
        except Exception as e:
            logger.error(f"Architecture change handling failed: {e}")
            return {
                "message": "I'm having difficulty processing your architecture change request. Let me escalate this directly to our Chief Technology Officer for immediate attention.",
                "confidence": 0.0,
                "success": False,
                "actions_taken": ["architecture_escalation"],
                "tools_used": tools_used,
                "outcome": "architecture_error",
                "requires_escalation": True
            }
    
    async def _handle_expert_analysis(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Handle general expert-level analysis"""
        tools_used = []
        
        try:
            # Apply credit adjustment if appropriate (high-value customer with service issue)
            if (state.customer and 
                state.customer.tier in [CustomerTier.PLATINUM, CustomerTier.GOLD] and
                any(word in message.lower() for word in ["service", "down", "problem", "issue"])):
                
                credit_result = await self.use_tool(
                    "apply_credit_adjustment",
                    {
                        "customer_id": state.customer.customer_id,
                        "amount": 50.0,  # Goodwill credit
                        "reason": "Service inconvenience - expert level resolution",
                        "approval_level": "tier3_expert"
                    },
                    self.get_agent_context(state)
                )
                tools_used.append("apply_credit_adjustment")
            
            response_message = "I've conducted an expert-level analysis of your situation. "
            response_message += "Given the complexity, I'm implementing our premium resolution process.\n\n"
            
            if state.customer and state.customer.tier == CustomerTier.PLATINUM:
                response_message += "As a Platinum customer, you're receiving our highest level of expert attention. "
                response_message += "I've applied a service credit to your account as a gesture of goodwill while we resolve this.\n\n"
            
            response_message += "I'm coordinating with multiple specialist teams to ensure comprehensive resolution. "
            response_message += "A senior manager will personally oversee this case and contact you with updates."
            
            return {
                "message": response_message,
                "confidence": 0.8,
                "success": True,
                "actions_taken": ["expert_analysis_completed"],
                "tools_used": tools_used,
                "outcome": "expert_resolution_process",
                "estimated_time": "2-4 hours"
            }
            
        except Exception as e:
            logger.error(f"Expert analysis failed: {e}")
            return {
                "message": "Given the complexity of your situation, I'm escalating this directly to our executive team for immediate personal attention.",
                "confidence": 0.0,
                "success": False,
                "actions_taken": ["executive_escalation"],
                "tools_used": tools_used,
                "outcome": "executive_escalation",
                "requires_escalation": True
            }
    
    async def _log_critical_action(self, response: Dict[str, Any], state: AgentState):
        """Log critical actions taken by Tier 3 agent"""
        try:
            await self.use_tool(
                "audit_log_action",
                {
                    "action": "tier3_critical_resolution",
                    "details": {
                        "conversation_id": state.conversation_id,
                        "customer_id": state.customer.customer_id if state.customer else None,
                        "actions_taken": response.get("actions_taken", []),
                        "tools_used": response.get("tools_used", []),
                        "outcome": response.get("outcome"),
                        "success": response.get("success"),
                        "confidence": response.get("confidence")
                    },
                    "severity": "critical",
                    "requires_review": True
                },
                self.get_agent_context(state)
            )
        except Exception as e:
            logger.error(f"Failed to log critical action: {e}")
    
    async def _check_human_escalation_needed(self, response: Dict[str, Any], state: AgentState) -> bool:
        """Check if human escalation is needed"""
        escalation_triggers = [
            # Explicit escalation request
            response.get("requires_escalation", False),
            
            # Failed critical procedure
            not response.get("success", True) and "critical" in response.get("outcome", ""),
            
            # Security incidents always require human oversight
            "security" in response.get("outcome", "").lower(),
            
            # Compliance issues requiring legal review
            response.get("approval_required", False) and "compliance" in response.get("outcome", ""),
            
            # Executive-level customer with unresolved issue
            (state.customer and 
             state.customer.tier == CustomerTier.PLATINUM and
             state.customer.lifetime_value > 100000 and
             not response.get("success", True)),
            
            # Multiple Tier 3 attempts failed
            len([ra for ra in state.resolution_attempts if "tier3" in ra.agent_type.lower()]) >= 2
        ]
        
        return any(escalation_triggers)