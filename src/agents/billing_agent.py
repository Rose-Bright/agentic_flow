"""
Billing Agent for Contact Center Agentic Flow System
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import re

from src.agents.base_agent import BaseAgent
from src.models.state import AgentState, TicketStatus, CustomerTier, Priority
from src.core.logging import get_logger

logger = get_logger(__name__)


class BillingAgent(BaseAgent):
    """Agent specialized in billing, payments, subscriptions, and account management"""
    
    def __init__(
        self,
        name: str,
        model: str,
        capabilities: List[str],
        tools: List[str],
        confidence_threshold: float = 0.85
    ):
        super().__init__(name, model, capabilities, tools, confidence_threshold)
        
        # Billing policies and procedures
        self.billing_policies = self._initialize_billing_policies()
        
        # Payment processing rules
        self.payment_rules = self._initialize_payment_rules()
        
        # Subscription management workflows
        self.subscription_workflows = self._initialize_subscription_workflows()
        
        # Refund and credit policies
        self.refund_policies = self._initialize_refund_policies()
        
        # Billing dispute resolution procedures
        self.dispute_procedures = self._initialize_dispute_procedures()
        
        # Account management actions
        self.account_actions = self._initialize_account_actions()
    
    async def handle_message(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Handle billing-related inquiries and issues"""
        try:
            logger.info(f"Billing agent handling inquiry for conversation {state.conversation_id}")
            
            # Analyze billing inquiry type
            billing_analysis = await self._analyze_billing_inquiry(message, state)
            
            # Determine billing action required
            billing_action = await self._determine_billing_action(message, state, billing_analysis)
            
            # Execute billing resolution
            response = await self._execute_billing_resolution(billing_action, message, state)
            
            # Check for account alerts or issues
            account_alerts = await self._check_account_alerts(state)
            
            # Update billing history
            await self._update_billing_interaction_history(billing_analysis, response, state)
            
            return {
                "message": response["message"],
                "confidence": response["confidence"],
                "success": response["success"],
                "resolution_attempt": True,
                "actions_taken": response["actions_taken"],
                "tools_used": response["tools_used"],
                "outcome": response["outcome"],
                "new_status": TicketStatus.RESOLVED if response["success"] else TicketStatus.IN_PROGRESS,
                "billing_action": billing_action,
                "inquiry_type": billing_analysis.get("inquiry_type"),
                "account_impact": response.get("account_impact", "none"),
                "financial_impact": response.get("financial_impact", 0.0),
                "follow_up_date": response.get("follow_up_date"),
                "documentation_required": response.get("documentation_required", False),
                "approval_needed": response.get("approval_needed", False),
                "account_alerts": account_alerts
            }
            
        except Exception as e:
            logger.error(f"Billing agent error: {e}")
            return {
                "message": "I apologize for the technical difficulty with your billing inquiry. Let me connect you with our billing specialist who can access your account and resolve this issue immediately.",
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
        """Determine if this agent can handle the current billing inquiry"""
        # Billing-related intents
        billing_intents = [
            "billing_inquiry", "payment_issue", "subscription_change", "refund_request",
            "invoice_question", "account_balance", "payment_method_update", "billing_dispute",
            "subscription_cancel", "upgrade_billing", "downgrade_billing", "credit_inquiry"
        ]
        
        # Check if intent is billing-related
        can_handle_intent = (
            state.current_intent in billing_intents or
            any(keyword in state.current_intent.lower() 
                for keyword in ["billing", "payment", "invoice", "subscription", "refund", "charge"])
        )
        
        # Check for billing keywords in recent conversation
        billing_keywords_present = False
        if state.conversation_history:
            recent_messages = [turn.message.lower() for turn in state.conversation_history[-3:]]
            billing_keywords = [
                "bill", "payment", "charge", "invoice", "subscription", "refund", "credit",
                "balance", "card", "bank", "account", "fee", "cost", "price", "money"
            ]
            billing_keywords_present = any(
                keyword in message for message in recent_messages for keyword in billing_keywords
            )
        
        # Check for urgent billing issues
        urgent_billing = (
            state.priority == Priority.HIGH and
            any(keyword in str(state.conversation_history).lower() 
                for keyword in ["overdue", "suspended", "declined", "failed payment"])
        )
        
        return can_handle_intent or billing_keywords_present or urgent_billing
    
    def _get_agent_permissions(self) -> List[str]:
        """Get the permissions available to this agent"""
        return [
            "read_customer_billing_data",
            "view_payment_history",
            "process_refunds",
            "update_payment_methods",
            "modify_subscriptions",
            "apply_credits",
            "generate_invoices",
            "access_billing_system",
            "process_chargebacks",
            "adjust_billing_cycles",
            "apply_billing_adjustments",
            "access_payment_gateway"
        ]
    
    def _initialize_billing_policies(self) -> Dict[str, Dict[str, Any]]:
        """Initialize billing policies and procedures"""
        return {
            "payment_terms": {
                "due_date": "30_days_from_invoice",
                "grace_period": 5,
                "late_fee_percentage": 1.5,
                "suspension_threshold": 60,
                "collection_threshold": 90
            },
            "refund_policy": {
                "full_refund_window": 30,
                "prorated_refund_window": 90,
                "no_refund_after": 180,
                "cancellation_refund": True,
                "downgrade_refund": "prorated"
            },
            "billing_cycles": {
                "monthly": {"day": 1, "advance_notice": 3},
                "quarterly": {"day": 1, "advance_notice": 7},
                "annual": {"day": 1, "advance_notice": 30}
            },
            "dispute_resolution": {
                "investigation_period": 14,
                "response_time": 3,
                "escalation_threshold": 2,
                "documentation_required": True
            }
        }
    
    def _initialize_payment_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize payment processing rules"""
        return {
            "accepted_methods": {
                "credit_cards": ["visa", "mastercard", "amex", "discover"],
                "bank_transfers": ["ach", "wire"],
                "digital_wallets": ["paypal", "stripe"],
                "corporate": ["purchase_order", "invoice"]
            },
            "retry_logic": {
                "failed_payment_retries": 3,
                "retry_intervals": [1, 3, 7],  # days
                "notification_schedule": [1, 7, 14, 30]
            },
            "fraud_prevention": {
                "velocity_checks": True,
                "geolocation_verification": True,
                "cvv_verification": True,
                "address_verification": True
            },
            "limits": {
                "max_transaction": 50000,
                "daily_limit": 100000,
                "monthly_limit": 1000000
            }
        }
    
    def _initialize_subscription_workflows(self) -> Dict[str, List[str]]:
        """Initialize subscription management workflows"""
        return {
            "upgrade": [
                "verify_current_subscription",
                "calculate_prorated_charges",
                "process_upgrade_payment",
                "activate_new_features",
                "send_confirmation"
            ],
            "downgrade": [
                "verify_current_subscription",
                "check_usage_limits",
                "calculate_credit_amount",
                "schedule_downgrade_date",
                "notify_feature_changes"
            ],
            "cancellation": [
                "verify_account_owner",
                "check_outstanding_balance",
                "process_final_billing",
                "schedule_service_termination",
                "export_data_backup"
            ],
            "suspension": [
                "verify_suspension_reason",
                "backup_account_data",
                "disable_service_access",
                "send_suspension_notice",
                "set_reactivation_conditions"
            ],
            "reactivation": [
                "verify_payment_method",
                "process_outstanding_balance",
                "restore_service_access",
                "validate_account_settings",
                "send_welcome_back_notice"
            ]
        }
    
    def _initialize_refund_policies(self) -> Dict[str, Dict[str, Any]]:
        """Initialize refund and credit policies"""
        return {
            "eligibility_criteria": {
                "service_outage": {
                    "minimum_duration": 4,  # hours
                    "refund_percentage": 100,
                    "applies_to": "affected_period"
                },
                "billing_error": {
                    "refund_percentage": 100,
                    "applies_to": "error_amount"
                },
                "dissatisfaction": {
                    "window": 30,  # days
                    "refund_percentage": 100,
                    "conditions": ["first_time_user", "minimal_usage"]
                },
                "downgrade": {
                    "refund_percentage": "prorated",
                    "applies_to": "unused_period"
                }
            },
            "processing_times": {
                "credit_card": "3-5_business_days",
                "bank_transfer": "5-7_business_days",
                "account_credit": "immediate",
                "check": "10-14_business_days"
            },
            "approval_limits": {
                "billing_agent": 500,
                "billing_supervisor": 2500,
                "billing_manager": 10000,
                "finance_director": 50000
            }
        }
    
    def _initialize_dispute_procedures(self) -> Dict[str, List[str]]:
        """Initialize billing dispute resolution procedures"""
        return {
            "chargeback_process": [
                "receive_chargeback_notification",
                "gather_transaction_evidence",
                "compile_dispute_package",
                "submit_representment",
                "monitor_case_status"
            ],
            "billing_dispute": [
                "log_dispute_details",
                "investigate_billing_records",
                "verify_service_delivery",
                "calculate_adjustments",
                "communicate_resolution"
            ],
            "fraud_investigation": [
                "freeze_suspicious_activity",
                "collect_security_evidence",
                "verify_account_ownership",
                "assess_financial_impact",
                "implement_security_measures"
            ]
        }
    
    def _initialize_account_actions(self) -> Dict[str, Dict[str, Any]]:
        """Initialize account management actions"""
        return {
            "payment_update": {
                "verification_required": True,
                "immediate_effect": True,
                "notification_sent": True
            },
            "billing_address_change": {
                "verification_required": True,
                "tax_impact": True,
                "immediate_effect": True
            },
            "subscription_modification": {
                "approval_required": False,
                "prorated_billing": True,
                "feature_access_change": True
            },
            "account_suspension": {
                "approval_required": True,
                "data_retention": 90,
                "reactivation_process": "payment_and_verification"
            },
            "account_closure": {
                "approval_required": True,
                "data_export": True,
                "final_billing": True,
                "retention_period": 30
            }
        }
    
    async def _analyze_billing_inquiry(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Analyze the type and urgency of billing inquiry"""
        message_lower = message.lower()
        
        # Inquiry type classification
        inquiry_types = {
            "payment_failure": [
                "payment failed", "card declined", "payment error", "couldn't charge",
                "payment unsuccessful", "transaction failed"
            ],
            "billing_dispute": [
                "wrong charge", "incorrect bill", "didn't authorize", "dispute charge",
                "billing error", "overcharged", "double charged"
            ],
            "subscription_change": [
                "upgrade", "downgrade", "change plan", "modify subscription",
                "cancel subscription", "pause account"
            ],
            "refund_request": [
                "refund", "money back", "return payment", "credit back",
                "reimburse", "get my money"
            ],
            "invoice_inquiry": [
                "invoice", "bill", "statement", "billing history",
                "payment due", "balance"
            ],
            "payment_method": [
                "update card", "change payment", "new credit card",
                "payment method", "billing info"
            ],
            "account_access": [
                "account suspended", "can't access", "locked out",
                "account disabled", "service stopped"
            ]
        }
        
        # Determine inquiry type
        inquiry_type = "general_billing"
        confidence = 0.0
        
        for inq_type, keywords in inquiry_types.items():
            matches = sum(1 for keyword in keywords if keyword in message_lower)
            if matches > 0:
                current_confidence = matches / len(keywords)
                if current_confidence > confidence:
                    inquiry_type = inq_type
                    confidence = current_confidence
        
        # Urgency assessment
        urgency_indicators = {
            "high": [
                "urgent", "immediately", "asap", "emergency", "critical",
                "suspended", "locked", "can't access", "business down"
            ],
            "medium": [
                "soon", "today", "this week", "important", "need help",
                "overdue", "past due"
            ],
            "low": [
                "when convenient", "no rush", "general question",
                "wondering", "curious"
            ]
        }
        
        urgency = "medium"  # default
        for level, indicators in urgency_indicators.items():
            if any(indicator in message_lower for indicator in indicators):
                urgency = level
                break
        
        # Financial impact assessment
        financial_impact = self._assess_financial_impact(message_lower, state)
        
        return {
            "inquiry_type": inquiry_type,
            "confidence": confidence,
            "urgency": urgency,
            "financial_impact": financial_impact,
            "requires_verification": inquiry_type in ["payment_method", "refund_request", "subscription_change"],
            "potential_escalation": urgency == "high" or financial_impact > 1000
        }
    
    def _assess_financial_impact(self, message_lower: str, state: AgentState) -> float:
        """Assess the potential financial impact of the inquiry"""
        # Extract monetary amounts from message
        amount_pattern = r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        amounts = re.findall(amount_pattern, message_lower)
        
        if amounts:
            # Take the largest amount mentioned
            return max(float(amount.replace(',', '')) for amount in amounts)
        
        # Estimate based on customer tier and inquiry type
        if state.customer:
            tier_estimates = {
                CustomerTier.BRONZE: 50,
                CustomerTier.SILVER: 150,
                CustomerTier.GOLD: 500,
                CustomerTier.PLATINUM: 2000
            }
            return tier_estimates.get(state.customer.tier, 100)
        
        return 100  # Default estimate
    
    async def _determine_billing_action(
        self, 
        message: str, 
        state: AgentState, 
        billing_analysis: Dict[str, Any]
    ) -> str:
        """Determine the billing action needed"""
        inquiry_type = billing_analysis["inquiry_type"]
        urgency = billing_analysis["urgency"]
        
        # Map inquiry types to actions
        action_mapping = {
            "payment_failure": "resolve_payment_failure",
            "billing_dispute": "investigate_dispute",
            "subscription_change": "modify_subscription",
            "refund_request": "process_refund",
            "invoice_inquiry": "provide_billing_info",
            "payment_method": "update_payment_method",
            "account_access": "restore_account_access",
            "general_billing": "provide_billing_support"
        }
        
        base_action = action_mapping.get(inquiry_type, "provide_billing_support")
        
        # Modify action based on urgency
        if urgency == "high":
            if base_action in ["resolve_payment_failure", "restore_account_access"]:
                return f"urgent_{base_action}"
        
        return base_action
    
    async def _execute_billing_resolution(
        self, 
        action: str, 
        message: str, 
        state: AgentState
    ) -> Dict[str, Any]:
        """Execute the billing resolution action"""
        
        action_methods = {
            "resolve_payment_failure": self._resolve_payment_failure,
            "urgent_resolve_payment_failure": self._resolve_urgent_payment_failure,
            "investigate_dispute": self._investigate_billing_dispute,
            "modify_subscription": self._modify_subscription,
            "process_refund": self._process_refund_request,
            "provide_billing_info": self._provide_billing_information,
            "update_payment_method": self._update_payment_method,
            "restore_account_access": self._restore_account_access,
            "urgent_restore_account_access": self._restore_urgent_account_access,
            "provide_billing_support": self._provide_general_billing_support
        }
        
        method = action_methods.get(action, self._provide_general_billing_support)
        return await method(message, state)
    
    async def _resolve_payment_failure(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Resolve payment failure issues"""
        tools_used = []
        
        try:
            # Get payment history and current status
            payment_status = await self.use_tool(
                "get_payment_status",
                {"customer_id": state.customer.customer_id if state.customer else None},
                self.get_agent_context(state)
            )
            tools_used.append("get_payment_status")
            
            if payment_status.get("success"):
                failed_payments = payment_status.get("failed_payments", [])
                
                if failed_payments:
                    latest_failure = failed_payments[0]
                    failure_reason = latest_failure.get("reason", "unknown")
                    
                    # Attempt to retry payment with current method
                    retry_result = await self.use_tool(
                        "retry_payment",
                        {
                            "customer_id": state.customer.customer_id if state.customer else None,
                            "payment_id": latest_failure.get("payment_id"),
                            "retry_reason": "customer_request"
                        },
                        self.get_agent_context(state)
                    )
                    tools_used.append("retry_payment")
                    
                    if retry_result.get("success"):
                        response = f"Great news! I was able to successfully process your payment. "
                        response += f"Your account is now current and all services are active.\n\n"
                        response += f"Payment Details:\n"
                        response += f"• Amount: ${retry_result.get('amount', 0):.2f}\n"
                        response += f"• Transaction ID: {retry_result.get('transaction_id', 'N/A')}\n"
                        response += f"• Payment Method: {retry_result.get('payment_method', 'N/A')}\n\n"
                        response += f"You'll receive a confirmation email shortly. Is there anything else I can help you with?"
                        
                        return {
                            "message": response,
                            "confidence": 0.95,
                            "success": True,
                            "actions_taken": ["payment_retry_successful"],
                            "tools_used": tools_used,
                            "outcome": "payment_resolved",
                            "financial_impact": retry_result.get('amount', 0)
                        }
                    else:
                        # Payment retry failed, offer alternatives
                        response = f"I see there's still an issue with your payment method. "
                        response += f"The error is: {failure_reason}\n\n"
                        
                        if failure_reason in ["insufficient_funds", "card_declined"]:
                            response += f"This typically means:\n"
                            response += f"• Insufficient funds in your account\n"
                            response += f"• Your card has expired or been replaced\n"
                            response += f"• Your bank is blocking the transaction\n\n"
                            response += f"I can help you update your payment method right now. "
                            response += f"Would you like to add a new card or try a different payment option?"
                        else:
                            response += f"Let me help you resolve this. I can:\n"
                            response += f"• Update your payment method\n"
                            response += f"• Try processing with a different card\n"
                            response += f"• Set up a payment plan if needed\n\n"
                            response += f"What would work best for you?"
                        
                        return {
                            "message": response,
                            "confidence": 0.8,
                            "success": False,
                            "actions_taken": ["payment_retry_failed", "alternative_offered"],
                            "tools_used": tools_used,
                            "outcome": "payment_alternatives_offered",
                            "follow_up_required": True
                        }
                else:
                    response = "I've checked your account and don't see any recent payment failures. "
                    response += "Your account appears to be in good standing. Could you provide more details "
                    response += "about the payment issue you're experiencing?"
                    
                    return {
                        "message": response,
                        "confidence": 0.7,
                        "success": True,
                        "actions_taken": ["account_status_verified"],
                        "tools_used": tools_used,
                        "outcome": "no_payment_issues_found"
                    }
            else:
                raise Exception("Unable to retrieve payment status")
                
        except Exception as e:
            logger.error(f"Payment failure resolution failed: {e}")
            return {
                "message": "I'm having trouble accessing your payment information right now. Let me connect you with our billing specialist who can resolve this payment issue immediately and ensure your account stays active.",
                "confidence": 0.5,
                "success": False,
                "actions_taken": ["payment_resolution_failed"],
                "tools_used": tools_used,
                "outcome": "escalation_required",
                "requires_escalation": True
            }
    
    async def _resolve_urgent_payment_failure(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Resolve urgent payment failures that may affect service"""
        tools_used = []
        
        try:
            # Check account suspension status
            account_status = await self.use_tool(
                "get_account_status",
                {"customer_id": state.customer.customer_id if state.customer else None},
                self.get_agent_context(state)
            )
            tools_used.append("get_account_status")
            
            if account_status.get("suspended") or account_status.get("at_risk"):
                # Apply temporary service extension
                extension_result = await self.use_tool(
                    "apply_service_extension",
                    {
                        "customer_id": state.customer.customer_id if state.customer else None,
                        "extension_days": 7,
                        "reason": "payment_resolution_in_progress"
                    },
                    self.get_agent_context(state)
                )
                tools_used.append("apply_service_extension")
                
                response = "🚨 I understand this is urgent and affects your business operations. "
                response += "I've immediately applied a 7-day service extension to keep your account active "
                response += "while we resolve the payment issue.\n\n"
                response += "Your services will remain fully functional during this period. "
                response += "Now let's get your payment sorted out. I can:\n\n"
                response += "• Process payment with a different card immediately\n"
                response += "• Set up a payment plan if cash flow is an issue\n"
                response += "• Connect you with our enterprise billing team for flexible options\n\n"
                response += "What's the best way to resolve this for you right now?"
                
                return {
                    "message": response,
                    "confidence": 0.9,
                    "success": True,
                    "actions_taken": ["service_extension_applied", "urgent_payment_assistance"],
                    "tools_used": tools_used,
                    "outcome": "urgent_issue_stabilized",
                    "account_impact": "service_extended",
                    "follow_up_required": True
                }
            else:
                # Account not at risk, proceed with standard resolution
                return await self._resolve_payment_failure(message, state)
                
        except Exception as e:
            logger.error(f"Urgent payment failure resolution failed: {e}")
            return {
                "message": "This is a critical billing issue affecting your service. I'm immediately connecting you with our emergency billing team who can resolve this within minutes and ensure your business operations continue uninterrupted.",
                "confidence": 0.6,
                "success": False,
                "actions_taken": ["urgent_escalation"],
                "tools_used": tools_used,
                "outcome": "emergency_escalation",
                "requires_escalation": True,
                "priority_escalation": True
            }
    
    async def _investigate_billing_dispute(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Investigate billing disputes and discrepancies"""
        tools_used = []
        
        try:
            # Get detailed billing history
            billing_history = await self.use_tool(
                "get_billing_history",
                {
                    "customer_id": state.customer.customer_id if state.customer else None,
                    "include_details": True,
                    "period": "last_6_months"
                },
                self.get_agent_context(state)
            )
            tools_used.append("get_billing_history")
            
            # Analyze the dispute claim
            dispute_analysis = self._analyze_dispute_claim(message, billing_history)
            
            if dispute_analysis["valid_concern"]:
                if dispute_analysis["clear_error"]:
                    # Clear billing error - process immediate adjustment
                    adjustment_result = await self.use_tool(
                        "process_billing_adjustment",
                        {
                            "customer_id": state.customer.customer_id if state.customer else None,
                            "adjustment_amount": -abs(dispute_analysis["error_amount"]),
                            "reason": "billing_error_correction",
                            "description": dispute_analysis["error_description"]
                        },
                        self.get_agent_context(state)
                    )
                    tools_used.append("process_billing_adjustment")
                    
                    response = f"I've reviewed your billing and you're absolutely right - there was an error. "
                    response += f"I've immediately processed a credit adjustment of ${abs(dispute_analysis['error_amount']):.2f} "
                    response += f"to your account.\n\n"
                    response += f"Error Details:\n"
                    response += f"• Issue: {dispute_analysis['error_description']}\n"
                    response += f"• Credit Amount: ${abs(dispute_analysis['error_amount']):.2f}\n"
                    response += f"• Applied: Immediately\n\n"
                    
                    if dispute_analysis["error_amount"] > 0:
                        response += f"The credit will appear on your next statement, and if you've already paid, "
                        response += f"we can process a refund instead. Would you prefer a refund or account credit?"
                    else:
                        response += f"Your account balance has been corrected. I sincerely apologize for this error."
                    
                    return {
                        "message": response,
                        "confidence": 0.95,
                        "success": True,
                        "actions_taken": ["billing_error_corrected", "credit_applied"],
                        "tools_used": tools_used,
                        "outcome": "dispute_resolved",
                        "financial_impact": dispute_analysis["error_amount"],
                        "account_impact": "credit_applied"
                    }
                else:
                    # Requires investigation
                    investigation_result = await self.use_tool(
                        "create_billing_investigation",
                        {
                            "customer_id": state.customer.customer_id if state.customer else None,
                            "dispute_details": dispute_analysis["dispute_summary"],
                            "priority": "high" if dispute_analysis["amount"] > 500 else "normal"
                        },
                        self.get_agent_context(state)
                    )
                    tools_used.append("create_billing_investigation")
                    
                    response = f"I understand your concern about this charge, and I want to make sure we get this resolved properly. "
                    response += f"I've started a detailed investigation into your billing (Case #{investigation_result.get('case_id', 'BIL-' + str(datetime.now().timestamp())[:10])}).\n\n"
                    response += f"What I'm investigating:\n"
                    response += f"• {dispute_analysis['dispute_summary']}\n"
                    response += f"• Amount in question: ${dispute_analysis['amount']:.2f}\n"
                    response += f"• Billing period: {dispute_analysis.get('period', 'Recent')}\n\n"
                    response += f"I'll have a complete analysis within 2 business days. In the meantime, "
                    response += f"I can place a temporary hold on this charge so it won't affect your account. "
                    response += f"Would you like me to do that?"
                    
                    return {
                        "message": response,
                        "confidence": 0.85,
                        "success": True,
                        "actions_taken": ["investigation_started"],
                        "tools_used": tools_used,
                        "outcome": "investigation_in_progress",
                        "follow_up_date": (datetime.now() + timedelta(days=2)).isoformat(),
                        "documentation_required": True
                    }
            else:
                # No valid dispute found
                response = f"I've carefully reviewed your billing history and the charges appear to be accurate "
                response += f"based on your service usage and subscription. Let me walk you through what I found:\n\n"
                
                if billing_history.get("recent_charges"):
                    response += f"Recent Charges:\n"
                    for charge in billing_history["recent_charges"][:5]:  # Show last 5 charges
                        response += f"• {charge.get('date', 'N/A')}: ${charge.get('amount', 0):.2f} - {charge.get('description', 'Service charge')}\n"
                
                response += f"\nIf you have specific questions about any of these charges, I'm happy to explain them in detail. "
                response += f"Is there a particular charge you'd like me to break down for you?"
                
                return {
                    "message": response,
                    "confidence": 0.8,
                    "success": True,
                    "actions_taken": ["billing_reviewed", "charges_explained"],
                    "tools_used": tools_used,
                    "outcome": "no_dispute_found",
                    "follow_up_required": True
                }
                
        except Exception as e:
            logger.error(f"Billing dispute investigation failed: {e}")
            return {
                "message": "I want to make sure your billing concern is properly addressed. Let me connect you with our billing specialist who can do a thorough review of your account and resolve any discrepancies immediately.",
                "confidence": 0.5,
                "success": False,
                "actions_taken": ["dispute_investigation_failed"],
                "tools_used": tools_used,
                "outcome": "escalation_required",
                "requires_escalation": True
            }
    
    def _analyze_dispute_claim(self, message: str, billing_history: Dict) -> Dict[str, Any]:
        """Analyze the customer's dispute claim"""
        message_lower = message.lower()
        
        # Extract disputed amount
        amount_pattern = r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        amounts = re.findall(amount_pattern, message_lower)
        disputed_amount = float(amounts[0].replace(',', '')) if amounts else 0.0
        
        # Common billing error patterns
        error_patterns = {
            "double_charge": ["charged twice", "double charge", "billed twice", "duplicate charge"],
            "wrong_amount": ["wrong amount", "incorrect charge", "overcharged", "too much"],
            "unauthorized": ["didn't authorize", "never agreed", "unauthorized", "fraudulent"],
            "cancelled_service": ["already cancelled", "stopped service", "cancelled subscription"],
            "downgrade_issue": ["downgraded", "changed plan", "reduced service"]
        }
        
        # Check for error patterns
        error_type = None
        for pattern_type, keywords in error_patterns.items():
            if any(keyword in message_lower for keyword in keywords):
                error_type = pattern_type
                break
        
        # Analyze billing history for potential errors
        clear_error = False
        error_amount = 0.0
        error_description = ""
        
        if error_type and billing_history.get("recent_charges"):
            recent_charges = billing_history["recent_charges"]
            
            if error_type == "double_charge":
                # Check for duplicate charges
                charge_amounts = [charge.get("amount", 0) for charge in recent_charges]
                if disputed_amount in charge_amounts and charge_amounts.count(disputed_amount) > 1:
                    clear_error = True
                    error_amount = disputed_amount
                    error_description = "Duplicate charge detected"
            
            elif error_type == "cancelled_service":
                # Check if service was cancelled but still charged
                if billing_history.get("cancellation_date"):
                    cancellation_date = datetime.fromisoformat(billing_history["cancellation_date"])
                    for charge in recent_charges:
                        charge_date = datetime.fromisoformat(charge.get("date", "2023-01-01"))
                        if charge_date > cancellation_date:
                            clear_error = True
                            error_amount = charge.get("amount", 0)
                            error_description = "Charge after cancellation date"
                            break
        
        return {
            "valid_concern": error_type is not None or disputed_amount > 0,
            "clear_error": clear_error,
            "error_amount": error_amount,
            "error_description": error_description,
            "dispute_summary": f"Customer disputes {error_type or 'charge'} of ${disputed_amount:.2f}",
            "amount": disputed_amount,
            "error_type": error_type
        }
    
    async def _modify_subscription(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Handle subscription modifications"""
        tools_used = []
        
        try:
            # Get current subscription details
            subscription_info = await self.use_tool(
                "get_subscription_details",
                {"customer_id": state.customer.customer_id if state.customer else None},
                self.get_agent_context(state)
            )
            tools_used.append("get_subscription_details")
            
            # Determine modification type
            modification_type = self._determine_modification_type(message)
            
            if modification_type == "upgrade":
                return await self._process_subscription_upgrade(message, state, subscription_info, tools_used)
            elif modification_type == "downgrade":
                return await self._process_subscription_downgrade(message, state, subscription_info, tools_used)
            elif modification_type == "cancel":
                return await self._process_subscription_cancellation(message, state, subscription_info, tools_used)
            elif modification_type == "pause":
                return await self._process_subscription_pause(message, state, subscription_info, tools_used)
            else:
                # General subscription inquiry
                current_plan = subscription_info.get("plan_name", "Current Plan")
                monthly_cost = subscription_info.get("monthly_cost", 0)
                next_billing = subscription_info.get("next_billing_date", "Unknown")
                
                response = f"I can help you with your subscription! Here's your current setup:\n\n"
                response += f"• Plan: {current_plan}\n"
                response += f"• Monthly Cost: ${monthly_cost:.2f}\n"
                response += f"• Next Billing: {next_billing}\n"
                response += f"• Status: {subscription_info.get('status', 'Active')}\n\n"
                response += f"I can help you:\n"
                response += f"• Upgrade to a higher plan with more features\n"
                response += f"• Downgrade to save money\n"
                response += f"• Pause your subscription temporarily\n"
                response += f"• Cancel if needed (with proper notice)\n\n"
                response += f"What would you like to do with your subscription?"
                
                return {
                    "message": response,
                    "confidence": 0.8,
                    "success": True,
                    "actions_taken": ["subscription_info_provided"],
                    "tools_used": tools_used,
                    "outcome": "subscription_options_presented",
                    "follow_up_required": True
                }
                
        except Exception as e:
            logger.error(f"Subscription modification failed: {e}")
            return {
                "message": "I'm having trouble accessing your subscription details right now. Let me connect you with our subscription specialist who can make any changes you need immediately.",
                "confidence": 0.5,
                "success": False,
                "actions_taken": ["subscription_modification_failed"],
                "tools_used": tools_used,
                "outcome": "escalation_required",
                "requires_escalation": True
            }
    
    def _determine_modification_type(self, message: str) -> str:
        """Determine what type of subscription modification is requested"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["upgrade", "higher plan", "more features", "premium"]):
            return "upgrade"
        elif any(word in message_lower for word in ["downgrade", "lower plan", "cheaper", "reduce", "basic"]):
            return "downgrade"
        elif any(word in message_lower for word in ["cancel", "close account", "terminate", "end subscription"]):
            return "cancel"
        elif any(word in message_lower for word in ["pause", "suspend", "hold", "temporary stop"]):
            return "pause"
        else:
            return "general"
    
    async def _process_subscription_upgrade(self, message: str, state: AgentState, subscription_info: Dict, tools_used: List[str]) -> Dict[str, Any]:
        """Process subscription upgrade"""
        try:
            # Get available upgrade options
            upgrade_options = await self.use_tool(
                "get_upgrade_options",
                {
                    "customer_id": state.customer.customer_id if state.customer else None,
                    "current_plan": subscription_info.get("plan_id")
                },
                self.get_agent_context(state)
            )
            tools_used.append("get_upgrade_options")
            
            if upgrade_options.get("available_plans"):
                response = f"Great! I can help you upgrade your subscription. Based on your current {subscription_info.get('plan_name', 'plan')}, "
                response += f"here are your upgrade options:\n\n"
                
                for plan in upgrade_options["available_plans"]:
                    monthly_increase = plan.get("monthly_cost", 0) - subscription_info.get("monthly_cost", 0)
                    response += f"• {plan.get('name', 'Plan')}: ${plan.get('monthly_cost', 0):.2f}/month (+${monthly_increase:.2f})\n"
                    response += f"  New features: {', '.join(plan.get('new_features', [])[:3])}\n\n"
                
                response += f"I can process the upgrade immediately, and you'll only pay the prorated difference "
                response += f"for this billing cycle. Which plan interests you most?"
                
                return {
                    "message": response,
                    "confidence": 0.9,
                    "success": True,
                    "actions_taken": ["upgrade_options_presented"],
                    "tools_used": tools_used,
                    "outcome": "upgrade_options_provided",
                    "follow_up_required": True
                }
            else:
                response = f"You're already on our highest tier plan! Your current {subscription_info.get('plan_name', 'plan')} "
                response += f"includes all our premium features. However, I can help you with add-ons or custom enterprise features "
                response += f"if you have specific needs. What additional capabilities are you looking for?"
                
                return {
                    "message": response,
                    "confidence": 0.8,
                    "success": True,
                    "actions_taken": ["max_plan_notification"],
                    "tools_used": tools_used,
                    "outcome": "no_upgrades_available"
                }
                
        except Exception as e:
            logger.error(f"Subscription upgrade processing failed: {e}")
            return {
                "message": "I'd be happy to help you upgrade your subscription! Let me connect you with our sales team who can show you all available options and process the upgrade with any applicable discounts.",
                "confidence": 0.6,
                "success": False,
                "actions_taken": ["upgrade_processing_failed"],
                "tools_used": tools_used,
                "outcome": "sales_escalation_required",
                "requires_escalation": True
            }
    
    async def _process_subscription_downgrade(self, message: str, state: AgentState, subscription_info: Dict, tools_used: List[str]) -> Dict[str, Any]:
        """Process subscription downgrade"""
        try:
            # Get downgrade options and impact analysis
            downgrade_options = await self.use_tool(
                "get_downgrade_options",
                {
                    "customer_id": state.customer.customer_id if state.customer else None,
                    "current_plan": subscription_info.get("plan_id")
                },
                self.get_agent_context(state)
            )
            tools_used.append("get_downgrade_options")
            
            if downgrade_options.get("available_plans"):
                response = f"I can help you downgrade to save money. Here are your options:\n\n"
                
                for plan in downgrade_options["available_plans"]:
                    monthly_savings = subscription_info.get("monthly_cost", 0) - plan.get("monthly_cost", 0)
                    response += f"• {plan.get('name', 'Plan')}: ${plan.get('monthly_cost', 0):.2f}/month (Save ${monthly_savings:.2f})\n"
                    
                    if plan.get("limitations"):
                        response += f"  Note: {', '.join(plan.get('limitations', [])[:2])}\n"
                    response += f"\n"
                
                # Check for credit eligibility
                if downgrade_options.get("credit_eligible"):
                    credit_amount = downgrade_options.get("credit_amount", 0)
                    response += f"Good news! You'll receive a ${credit_amount:.2f} credit for the unused portion "
                    response += f"of your current billing period.\n\n"
                
                response += f"I can process this change immediately. The downgrade will take effect at your next billing cycle "
                response += f"so you can continue using all current features until then. Which plan would you prefer?"
                
                return {
                    "message": response,
                    "confidence": 0.9,
                    "success": True,
                    "actions_taken": ["downgrade_options_presented"],
                    "tools_used": tools_used,
                    "outcome": "downgrade_options_provided",
                    "follow_up_required": True
                }
            else:
                response = f"You're currently on our most basic plan, so there aren't any lower-tier options available. "
                response += f"However, I can help you with:\n\n"
                response += f"• Pausing your subscription temporarily\n"
                response += f"• Switching to annual billing for a discount\n"
                response += f"• Exploring if there are any current promotions\n\n"
                response += f"What would work best for your situation?"
                
                return {
                    "message": response,
                    "confidence": 0.8,
                    "success": True,
                    "actions_taken": ["min_plan_notification"],
                    "tools_used": tools_used,
                    "outcome": "no_downgrades_available",
                    "follow_up_required": True
                }
                
        except Exception as e:
            logger.error(f"Subscription downgrade processing failed: {e}")
            return {
                "message": "I understand you'd like to reduce your costs. Let me connect you with our retention specialist who can explore all money-saving options including special discounts that might be available for your account.",
                "confidence": 0.6,
                "success": False,
                "actions_taken": ["downgrade_processing_failed"],
                "tools_used": tools_used,
                "outcome": "retention_escalation_required",
                "requires_escalation": True
            }
    
    async def _process_subscription_cancellation(self, message: str, state: AgentState, subscription_info: Dict, tools_used: List[str]) -> Dict[str, Any]:
        """Process subscription cancellation"""
        try:
            # Check cancellation eligibility and terms
            cancellation_info = await self.use_tool(
                "check_cancellation_terms",
                {
                    "customer_id": state.customer.customer_id if state.customer else None,
                    "subscription_id": subscription_info.get("subscription_id")
                },
                self.get_agent_context(state)
            )
            tools_used.append("check_cancellation_terms")
            
            # Calculate any fees or credits
            financial_impact = cancellation_info.get("financial_impact", {})
            
            response = f"I can help you with your cancellation. Here's what you need to know:\n\n"
            
            # Notice period
            notice_period = cancellation_info.get("notice_period", 30)
            effective_date = (datetime.now() + timedelta(days=notice_period)).strftime("%B %d, %Y")
            response += f"• Cancellation will be effective: {effective_date}\n"
            response += f"• You'll continue to have full access until then\n"
            
            # Financial implications
            if financial_impact.get("early_termination_fee", 0) > 0:
                response += f"• Early termination fee: ${financial_impact['early_termination_fee']:.2f}\n"
            
            if financial_impact.get("credit_amount", 0) > 0:
                response += f"• Credit for unused time: ${financial_impact['credit_amount']:.2f}\n"
            
            if financial_impact.get("refund_amount", 0) > 0:
                response += f"• Refund amount: ${financial_impact['refund_amount']:.2f}\n"
            
            # Data and export options
            response += f"\nBefore I process this:\n"
            response += f"• I can help you export your data\n"
            response += f"• Would you like to explore pause options instead?\n"
            response += f"• Are there any issues I can help resolve to keep your account?\n\n"
            
            response += f"If you're sure about cancelling, I can process this now. What would you prefer?"
            
            return {
                "message": response,
                "confidence": 0.85,
                "success": True,
                "actions_taken": ["cancellation_terms_provided"],
                "tools_used": tools_used,
                "outcome": "cancellation_options_presented",
                "financial_impact": financial_impact.get("net_impact", 0),
                "follow_up_required": True,
                "approval_needed": financial_impact.get("early_termination_fee", 0) > 0
            }
            
        except Exception as e:
            logger.error(f"Subscription cancellation processing failed: {e}")
            return {
                "message": "I want to make sure your cancellation is handled properly and you understand all your options. Let me connect you with our customer retention specialist who can process this and ensure you don't lose any data or credits you're entitled to.",
                "confidence": 0.6,
                "success": False,
                "actions_taken": ["cancellation_processing_failed"],
                "tools_used": tools_used,
                "outcome": "retention_escalation_required",
                "requires_escalation": True
            }
    
    async def _process_subscription_pause(self, message: str, state: AgentState, subscription_info: Dict, tools_used: List[str]) -> Dict[str, Any]:
        """Process subscription pause/hold"""
        try:
            # Check pause eligibility
            pause_options = await self.use_tool(
                "check_pause_eligibility",
                {
                    "customer_id": state.customer.customer_id if state.customer else None,
                    "subscription_id": subscription_info.get("subscription_id")
                },
                self.get_agent_context(state)
            )
            tools_used.append("check_pause_eligibility")
            
            if pause_options.get("eligible"):
                max_pause_days = pause_options.get("max_pause_days", 90)
                
                response = f"Yes! I can pause your subscription temporarily. Here are your options:\n\n"
                response += f"• Maximum pause period: {max_pause_days} days\n"
                response += f"• Your data will be safely preserved\n"
                response += f"• No charges during the pause period\n"
                response += f"• You can reactivate anytime\n\n"
                
                if pause_options.get("pause_fee", 0) > 0:
                    response += f"• Small maintenance fee: ${pause_options['pause_fee']:.2f}/month\n\n"
                
                response += f"How long would you like to pause your subscription? "
                response += f"I can set it up to automatically reactivate on a specific date if you'd like."
                
                return {
                    "message": response,
                    "confidence": 0.9,
                    "success": True,
                    "actions_taken": ["pause_options_provided"],
                    "tools_used": tools_used,
                    "outcome": "pause_available",
                    "follow_up_required": True
                }
            else:
                reason = pause_options.get("ineligible_reason", "Policy restrictions")
                response = f"I'm sorry, but your account isn't eligible for subscription pause due to: {reason}\n\n"
                response += f"However, I can offer these alternatives:\n"
                response += f"• Downgrade to a lower-cost plan temporarily\n"
                response += f"• Switch to annual billing for savings\n"
                response += f"• Explore special retention offers\n\n"
                response += f"What would work best for your situation?"
                
                return {
                    "message": response,
                    "confidence": 0.8,
                    "success": True,
                    "actions_taken": ["pause_not_available", "alternatives_offered"],
                    "tools_used": tools_used,
                    "outcome": "pause_ineligible",
                    "follow_up_required": True
                }
                
        except Exception as e:
            logger.error(f"Subscription pause processing failed: {e}")
            return {
                "message": "I'd like to help you pause your subscription. Let me connect you with our account management team who can set up a temporary hold and ensure your account is preserved exactly as you need it.",
                "confidence": 0.6,
                "success": False,
                "actions_taken": ["pause_processing_failed"],
                "tools_used": tools_used,
                "outcome": "account_management_escalation",
                "requires_escalation": True
            }
    
    async def _process_refund_request(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Process refund requests"""
        tools_used = []
        
        try:
            # Get refund eligibility information
            refund_eligibility = await self.use_tool(
                "check_refund_eligibility",
                {"customer_id": state.customer.customer_id if state.customer else None},
                self.get_agent_context(state)
            )
            tools_used.append("check_refund_eligibility")
            
            if refund_eligibility.get("eligible"):
                refund_amount = refund_eligibility.get("refund_amount", 0)
                refund_reason = self._determine_refund_reason(message)
                
                # Process eligible refund
                if refund_amount <= self.refund_policies["approval_limits"]["billing_agent"]:
                    # Can process immediately
                    refund_result = await self.use_tool(
                        "process_refund",
                        {
                            "customer_id": state.customer.customer_id if state.customer else None,
                            "refund_amount": refund_amount,
                            "reason": refund_reason,
                            "method": refund_eligibility.get("preferred_method", "original_payment")
                        },
                        self.get_agent_context(state)
                    )
                    tools_used.append("process_refund")
                    
                    if refund_result.get("success"):
                        processing_time = self.refund_policies["processing_times"].get(
                            refund_result.get("method", "credit_card"), "3-5_business_days"
                        )
                        
                        response = f"✅ Your refund has been approved and processed!\n\n"
                        response += f"Refund Details:\n"
                        response += f"• Amount: ${refund_amount:.2f}\n"
                        response += f"• Method: {refund_result.get('method', 'Original payment method')}\n"
                        response += f"• Processing Time: {processing_time}\n"
                        response += f"• Reference ID: {refund_result.get('reference_id', 'REF-' + str(datetime.now().timestamp())[:10])}\n\n"
                        response += f"You'll receive an email confirmation shortly. Is there anything else I can help you with?"
                        
                        return {
                            "message": response,
                            "confidence": 0.95,
                            "success": True,
                            "actions_taken": ["refund_processed"],
                            "tools_used": tools_used,
                            "outcome": "refund_completed",
                            "financial_impact": refund_amount,
                            "account_impact": "refund_issued"
                        }
                    else:
                        raise Exception("Refund processing failed")
                else:
                    # Requires approval
                    response = f"I can see you're eligible for a ${refund_amount:.2f} refund. "
                    response += f"Since this amount requires supervisor approval, I'm sending this to our billing manager for immediate review. "
                    response += f"You'll receive approval and processing confirmation within 24 hours.\n\n"
                    response += f"I've prioritized your request due to the amount involved. "
                    response += f"Is there anything else I can help you with while this processes?"
                    
                    return {
                        "message": response,
                        "confidence": 0.8,
                        "success": True,
                        "actions_taken": ["refund_submitted_for_approval"],
                        "tools_used": tools_used,
                        "outcome": "refund_pending_approval",
                        "financial_impact": refund_amount,
                        "approval_needed": True,
                        "follow_up_date": (datetime.now() + timedelta(hours=24)).isoformat()
                    }
            else:
                # Not eligible for refund
                ineligible_reason = refund_eligibility.get("reason", "Policy restrictions")
                alternative_options = refund_eligibility.get("alternatives", [])
                
                response = f"I've reviewed your account for refund eligibility. Unfortunately, "
                response += f"your request doesn't qualify for a full refund due to: {ineligible_reason}\n\n"
                
                if alternative_options:
                    response += f"However, I can offer these alternatives:\n"
                    for option in alternative_options:
                        response += f"• {option}\n"
                    response += f"\nWould any of these options work for your situation?"
                else:
                    response += f"I understand this may be disappointing. Let me connect you with our billing supervisor "
                    response += f"who can review your specific circumstances and see if there are any exceptions that might apply."
                
                return {
                    "message": response,
                    "confidence": 0.8,
                    "success": alternative_options is not None and len(alternative_options) > 0,
                    "actions_taken": ["refund_eligibility_checked"],
                    "tools_used": tools_used,
                    "outcome": "refund_not_eligible",
                    "requires_escalation": len(alternative_options) == 0,
                    "follow_up_required": len(alternative_options) > 0
                }
                
        except Exception as e:
            logger.error(f"Refund processing failed: {e}")
            return {
                "message": "I want to make sure your refund request is handled properly. Let me connect you with our billing supervisor who can review your account and process any eligible refunds immediately.",
                "confidence": 0.5,
                "success": False,
                "actions_taken": ["refund_processing_error"],
                "tools_used": tools_used,
                "outcome": "escalation_required",
                "requires_escalation": True
            }
    
    def _determine_refund_reason(self, message: str) -> str:
        """Determine the reason for the refund request"""
        message_lower = message.lower()
        
        reason_keywords = {
            "service_issue": ["not working", "down", "outage", "broken", "problems"],
            "billing_error": ["wrong charge", "error", "mistake", "incorrect"],
            "dissatisfaction": ["unhappy", "disappointed", "not satisfied", "doesn't work"],
            "cancellation": ["cancelled", "don't want", "no longer need"],
            "duplicate_payment": ["charged twice", "double payment", "duplicate"]
        }
        
        for reason, keywords in reason_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return reason
        
        return "customer_request"
    
    async def _provide_billing_information(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Provide billing information and account details"""
        tools_used = []
        
        try:
            # Get comprehensive billing information
            billing_summary = await self.use_tool(
                "get_billing_summary",
                {
                    "customer_id": state.customer.customer_id if state.customer else None,
                    "include_history": True,
                    "include_upcoming": True
                },
                self.get_agent_context(state)
            )
            tools_used.append("get_billing_summary")
            
            response = f"Here's your current billing information:\n\n"
            
            # Current account status
            response += f"📊 Account Status:\n"
            response += f"• Balance: ${billing_summary.get('current_balance', 0):.2f}\n"
            response += f"• Status: {billing_summary.get('account_status', 'Active')}\n"
            response += f"• Next billing date: {billing_summary.get('next_billing_date', 'Not scheduled')}\n\n"
            
            # Current subscription
            if billing_summary.get('current_subscription'):
                sub = billing_summary['current_subscription']
                response += f"💳 Current Subscription:\n"
                response += f"• Plan: {sub.get('plan_name', 'N/A')}\n"
                response += f"• Monthly cost: ${sub.get('monthly_cost', 0):.2f}\n"
                response += f"• Billing cycle: {sub.get('billing_cycle', 'Monthly')}\n\n"
            
            # Recent transactions
            if billing_summary.get('recent_transactions'):
                response += f"💰 Recent Transactions:\n"
                for transaction in billing_summary['recent_transactions'][:3]:
                    response += f"• {transaction.get('date', 'N/A')}: ${transaction.get('amount', 0):.2f} - {transaction.get('description', 'Payment')}\n"
                response += f"\n"
            
            # Payment method
            if billing_summary.get('payment_method'):
                payment = billing_summary['payment_method']
                response += f"💳 Payment Method:\n"
                response += f"• Type: {payment.get('type', 'N/A')}\n"
                response += f"• Last 4 digits: {payment.get('last_four', 'N/A')}\n"
                response += f"• Expires: {payment.get('expiry', 'N/A')}\n\n"
            
            # Upcoming charges
            if billing_summary.get('upcoming_charges'):
                response += f"📅 Upcoming Charges:\n"
                for charge in billing_summary['upcoming_charges']:
                    response += f"• {charge.get('date', 'N/A')}: ${charge.get('amount', 0):.2f} - {charge.get('description', 'Subscription')}\n"
                response += f"\n"
            
            response += f"Need more details about any of these items? I can provide detailed breakdowns or help with any billing questions you have!"
            
            return {
                "message": response,
                "confidence": 0.9,
                "success": True,
                "actions_taken": ["billing_information_provided"],
                "tools_used": tools_used,
                "outcome": "information_delivered",
                "follow_up_required": True
            }
            
        except Exception as e:
            logger.error(f"Billing information retrieval failed: {e}")
            return {
                "message": "I'm having trouble accessing your billing information right now. Let me connect you with our billing specialist who can provide you with a complete account summary and answer any billing questions you have.",
                "confidence": 0.5,
                "success": False,
                "actions_taken": ["billing_info_retrieval_failed"],
                "tools_used": tools_used,
                "outcome": "escalation_required",
                "requires_escalation": True
            }
    
    async def _update_payment_method(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Update customer payment method"""
        tools_used = []
        
        try:
            # Verify customer identity for payment method changes
            verification_result = await self.use_tool(
                "verify_customer_identity",
                {
                    "customer_id": state.customer.customer_id if state.customer else None,
                    "verification_type": "payment_method_update"
                },
                self.get_agent_context(state)
            )
            tools_used.append("verify_customer_identity")
            
            if not verification_result.get("verified"):
                response = "For security purposes, I need to verify your identity before updating payment information. "
                response += "I'm going to connect you with our secure billing line where you can safely update your payment method "
                response += "after completing our standard verification process."
                
                return {
                    "message": response,
                    "confidence": 0.8,
                    "success": False,
                    "actions_taken": ["identity_verification_required"],
                    "tools_used": tools_used,
                    "outcome": "verification_required",
                    "requires_escalation": True
                }
            
            # Get current payment method info
            current_payment = await self.use_tool(
                "get_payment_methods",
                {"customer_id": state.customer.customer_id if state.customer else None},
                self.get_agent_context(state)
            )
            tools_used.append("get_payment_methods")
            
            response = "I can help you update your payment method securely. Here's what's currently on file:\n\n"
            
            if current_payment.get("methods"):
                for method in current_payment["methods"]:
                    response += f"• {method.get('type', 'Card')}: ****{method.get('last_four', 'XXXX')} "
                    response += f"(Expires: {method.get('expiry', 'Unknown')})\n"
            
            response += f"\nI can help you:\n"
            response += f"• Add a new credit/debit card\n"
            response += f"• Update your existing card information\n"
            response += f"• Set up bank account (ACH) payments\n"
            response += f"• Add PayPal or other digital wallets\n\n"
            
            response += f"For security, I'll need to send you to our secure payment portal to enter the new information. "
            response += f"This ensures your financial data is protected with bank-level encryption.\n\n"
            response += f"Would you like me to generate a secure link for you to update your payment method?"
            
            return {
                "message": response,
                "confidence": 0.85,
                "success": True,
                "actions_taken": ["payment_method_options_provided"],
                "tools_used": tools_used,
                "outcome": "secure_update_offered",
                "follow_up_required": True
            }
            
        except Exception as e:
            logger.error(f"Payment method update failed: {e}")
            return {
                "message": "I want to make sure your payment information is updated securely. Let me connect you with our billing team who can safely process payment method changes and ensure your account continues without interruption.",
                "confidence": 0.6,
                "success": False,
                "actions_taken": ["payment_update_failed"],
                "tools_used": tools_used,
                "outcome": "secure_escalation_required",
                "requires_escalation": True
            }
    
    async def _restore_account_access(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Restore account access for suspended accounts"""
        tools_used = []
        
        try:
            # Check account suspension status and reason
            account_status = await self.use_tool(
                "get_account_suspension_details",
                {"customer_id": state.customer.customer_id if state.customer else None},
                self.get_agent_context(state)
            )
            tools_used.append("get_account_suspension_details")
            
            if not account_status.get("suspended"):
                response = "Good news! Your account is actually active and not suspended. "
                response += "If you're having trouble accessing your account, this might be a technical issue or login problem. "
                response += "Let me help you troubleshoot:\n\n"
                response += "• Try clearing your browser cache and cookies\n"
                response += "• Make sure you're using the correct login URL\n"
                response += "• Check if you need to reset your password\n\n"
                response += "Are you getting any specific error messages when trying to log in?"
                
                return {
                    "message": response,
                    "confidence": 0.8,
                    "success": True,
                    "actions_taken": ["account_status_verified"],
                    "tools_used": tools_used,
                    "outcome": "account_not_suspended",
                    "follow_up_required": True
                }
            
            # Account is suspended - check reason and resolution options
            suspension_reason = account_status.get("reason", "unknown")
            outstanding_balance = account_status.get("outstanding_balance", 0)
            
            response = f"I can see your account is currently suspended due to: {suspension_reason}\n\n"
            
            if suspension_reason == "payment_failure" and outstanding_balance > 0:
                response += f"Outstanding Balance: ${outstanding_balance:.2f}\n\n"
                response += f"To restore your account immediately, I can:\n"
                response += f"• Process payment for the outstanding balance\n"
                response += f"• Set up a payment plan if needed\n"
                response += f"• Update your payment method if that's the issue\n\n"
                
                response += f"Once payment is resolved, your account will be reactivated within minutes. "
                response += f"Would you like to take care of this now?"
                
                return {
                    "message": response,
                    "confidence": 0.9,
                    "success": True,
                    "actions_taken": ["suspension_reason_identified"],
                    "tools_used": tools_used,
                    "outcome": "payment_resolution_offered",
                    "financial_impact": outstanding_balance,
                    "follow_up_required": True
                }
            
            elif suspension_reason == "policy_violation":
                response += f"This type of suspension requires review by our compliance team. "
                response += f"Let me connect you with a supervisor who can review your case and work on getting "
                response += f"your account restored as quickly as possible."
                
                return {
                    "message": response,
                    "confidence": 0.7,
                    "success": False,
                    "actions_taken": ["policy_suspension_identified"],
                    "tools_used": tools_used,
                    "outcome": "compliance_review_required",
                    "requires_escalation": True
                }
            
            else:
                # General suspension - attempt automatic restoration
                restoration_result = await self.use_tool(
                    "attempt_account_restoration",
                    {
                        "customer_id": state.customer.customer_id if state.customer else None,
                        "reason": "customer_request"
                    },
                    self.get_agent_context(state)
                )
                tools_used.append("attempt_account_restoration")
                
                if restoration_result.get("success"):
                    response += f"Great news! I was able to restore your account access immediately. "
                    response += f"Your account is now fully active and you should be able to log in normally.\n\n"
                    response += f"Please try logging in again, and let me know if you encounter any issues."
                    
                    return {
                        "message": response,
                        "confidence": 0.95,
                        "success": True,
                        "actions_taken": ["account_restored"],
                        "tools_used": tools_used,
                        "outcome": "access_restored",
                        "account_impact": "reactivated"
                    }
                else:
                    response += f"I'm unable to automatically restore your account. Let me connect you with "
                    response += f"our account restoration specialist who can manually review and reactivate your account."
                    
                    return {
                        "message": response,
                        "confidence": 0.6,
                        "success": False,
                        "actions_taken": ["automatic_restoration_failed"],
                        "tools_used": tools_used,
                        "outcome": "manual_restoration_required",
                        "requires_escalation": True
                    }
            
        except Exception as e:
            logger.error(f"Account access restoration failed: {e}")
            return {
                "message": "I understand you need to regain access to your account urgently. Let me connect you immediately with our account restoration team who can resolve this and get you back up and running.",
                "confidence": 0.5,
                "success": False,
                "actions_taken": ["account_restoration_error"],
                "tools_used": tools_used,
                "outcome": "urgent_escalation_required",
                "requires_escalation": True
            }
    
    async def _restore_urgent_account_access(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Handle urgent account access restoration"""
        tools_used = []
        
        try:
            # For urgent cases, bypass some checks and prioritize restoration
            urgent_restoration = await self.use_tool(
                "urgent_account_restoration",
                {
                    "customer_id": state.customer.customer_id if state.customer else None,
                    "agent_override": True,
                    "business_impact": "high"
                },
                self.get_agent_context(state)
            )
            tools_used.append("urgent_account_restoration")
            
            if urgent_restoration.get("success"):
                response = "🚨 URGENT RESTORATION COMPLETED 🚨\n\n"
                response += "Your account has been immediately reactivated with full access. "
                response += "I understand this was business-critical, so I've:\n\n"
                response += "• Restored all services immediately\n"
                response += "• Applied a 72-hour grace period for any outstanding issues\n"
                response += "• Flagged your account for priority support\n\n"
                
                if urgent_restoration.get("follow_up_required"):
                    response += "Important: Please resolve any outstanding billing matters within 72 hours "
                    response += "to prevent future interruptions. I'll have our billing team contact you today "
                    response += "to ensure everything stays resolved.\n\n"
                
                response += "Your business operations should be fully restored now. Please confirm everything is working properly."
                
                return {
                    "message": response,
                    "confidence": 0.95,
                    "success": True,
                    "actions_taken": ["urgent_restoration_completed", "grace_period_applied"],
                    "tools_used": tools_used,
                    "outcome": "urgent_access_restored",
                    "account_impact": "immediately_reactivated",
                    "follow_up_required": urgent_restoration.get("follow_up_required", False),
                    "follow_up_date": (datetime.now() + timedelta(hours=24)).isoformat()
                }
            else:
                # Even urgent restoration failed - immediate escalation
                response = "🚨 URGENT ESCALATION 🚨\n\n"
                response += "I understand this is a critical business issue. I'm immediately connecting you "
                response += "with our emergency account restoration team. You'll be transferred within 30 seconds "
                response += "to a specialist who has override authority to restore your access immediately.\n\n"
                response += "Reference this conversation ID when you speak with them: " + state.conversation_id
                
                return {
                    "message": response,
                    "confidence": 0.8,
                    "success": False,
                    "actions_taken": ["emergency_escalation"],
                    "tools_used": tools_used,
                    "outcome": "emergency_escalation_initiated",
                    "requires_escalation": True,
                    "priority_escalation": True
                }
                
        except Exception as e:
            logger.error(f"Urgent account restoration failed: {e}")
            return {
                "message": "🚨 CRITICAL ISSUE 🚨 I'm immediately transferring you to our emergency response team. They will call you within 2 minutes to restore your access. Please stay on the line.",
                "confidence": 0.7,
                "success": False,
                "actions_taken": ["critical_escalation"],
                "tools_used": tools_used,
                "outcome": "critical_escalation_required",
                "requires_escalation": True,
                "priority_escalation": True
            }
    
    async def _provide_general_billing_support(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Provide general billing support and guidance"""
        tools_used = []
        
        try:
            # Get basic account overview
            account_overview = await self.use_tool(
                "get_account_overview",
                {"customer_id": state.customer.customer_id if state.customer else None},
                self.get_agent_context(state)
            )
            tools_used.append("get_account_overview")
            
            response = "I'm here to help with any billing questions you have! "
            
            if account_overview.get("success"):
                response += f"I can see your account is in good standing. Here's what I can help you with:\n\n"
                response += f"💳 Billing & Payments:\n"
                response += f"• View your current balance and payment history\n"
                response += f"• Update payment methods securely\n"
                response += f"• Set up automatic payments\n"
                response += f"• Download invoices and tax documents\n\n"
                
                response += f"📋 Subscription Management:\n"
                response += f"• Upgrade or downgrade your plan\n"
                response += f"• Change billing cycles (monthly/annual)\n"
                response += f"• Add or remove features\n"
                response += f"• Pause or cancel subscriptions\n\n"
                
                response += f"💰 Refunds & Credits:\n"
                response += f"• Process eligible refunds\n"
                response += f"• Apply account credits\n"
                response += f"• Resolve billing disputes\n"
                response += f"• Explain charges and fees\n\n"
                
                response += f"🔒 Account Security:\n"
                response += f"• Update billing address\n"
                response += f"• Manage authorized users\n"
                response += f"• Review account access logs\n\n"
            else:
                response += f"Here are the billing services I can help you with:\n\n"
                response += f"• Payment issues and failed transactions\n"
                response += f"• Subscription changes and upgrades\n"
                response += f"• Refund requests and billing disputes\n"
                response += f"• Invoice questions and payment history\n"
                response += f"• Account access and security issues\n\n"
            
            response += f"What specific billing question can I answer for you today?"
            
            return {
                "message": response,
                "confidence": 0.8,
                "success": True,
                "actions_taken": ["billing_support_menu_provided"],
                "tools_used": tools_used,
                "outcome": "support_options_presented",
                "follow_up_required": True
            }
            
        except Exception as e:
            logger.error(f"General billing support failed: {e}")
            return {
                "message": "I'm here to help with all your billing needs! I can assist with payments, subscriptions, refunds, account issues, and any other billing questions. What specific area would you like help with today?",
                "confidence": 0.7,
                "success": True,
                "actions_taken": ["fallback_billing_support"],
                "tools_used": tools_used,
                "outcome": "general_support_offered",
                "follow_up_required": True
            }
    
    async def _check_account_alerts(self, state: AgentState) -> List[Dict[str, Any]]:
        """Check for any account alerts or issues that need attention"""
        alerts = []
        
        try:
            # This would typically check various systems for alerts
            alert_check = await self.use_tool(
                "check_account_alerts",
                {"customer_id": state.customer.customer_id if state.customer else None},
                self.get_agent_context(state)
            )
            
            if alert_check.get("alerts"):
                for alert in alert_check["alerts"]:
                    alerts.append({
                        "type": alert.get("type", "general"),
                        "severity": alert.get("severity", "low"),
                        "message": alert.get("message", "Account alert"),
                        "action_required": alert.get("action_required", False),
                        "due_date": alert.get("due_date")
                    })
            
        except Exception as e:
            logger.warning(f"Account alerts check failed: {e}")
            # Don't fail the main operation if alerts check fails
        
        return alerts
    
    async def _update_billing_interaction_history(
        self, 
        billing_analysis: Dict[str, Any], 
        response: Dict[str, Any], 
        state: AgentState
    ):
        """Update billing interaction history for future reference"""
        try:
            interaction_data = {
                "conversation_id": state.conversation_id,
                "customer_id": state.customer.customer_id if state.customer else None,
                "inquiry_type": billing_analysis.get("inquiry_type"),
                "resolution_outcome": response.get("outcome"),
                "financial_impact": response.get("financial_impact", 0),
                "agent_actions": response.get("actions_taken", []),
                "success": response.get("success", False),
                "escalated": response.get("requires_escalation", False),
                "timestamp": datetime.now().isoformat()
            }
            
            # This would typically update a billing CRM or history system
            logger.info(f"Billing interaction recorded: {interaction_data}")
            
        except Exception as e:
            logger.warning(f"Failed to update billing interaction history: {e}")