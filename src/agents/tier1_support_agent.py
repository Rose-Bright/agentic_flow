"""
Tier 1 Support Agent for Contact Center Agentic Flow System
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from src.agents.base_agent import BaseAgent
from src.models.state import AgentState, TicketStatus, Sentiment
from src.core.logging import get_logger

logger = get_logger(__name__)


class Tier1SupportAgent(BaseAgent):
    """Agent specialized in handling basic customer support inquiries"""
    
    def __init__(
        self,
        name: str,
        model: str,
        capabilities: List[str],
        tools: List[str],
        confidence_threshold: float = 0.7
    ):
        super().__init__(name, model, capabilities, tools, confidence_threshold)
        
        # FAQ database for quick responses
        self.faq_responses = self._initialize_faq_responses()
        
        # Common troubleshooting steps
        self.troubleshooting_guides = self._initialize_troubleshooting_guides()
        
        # Account-related helpers
        self.account_helpers = self._initialize_account_helpers()
    
    async def handle_message(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Handle Tier 1 support interactions"""
        try:
            logger.info(f"Tier 1 agent handling message for conversation {state.conversation_id}")
            
            # Determine the type of support needed
            support_type = await self._determine_support_type(message, state)
            
            # Execute appropriate support action
            response = await self._execute_support_action(support_type, message, state)
            
            # Determine if escalation is needed
            needs_escalation = await self._check_escalation_needed(response, state)
            
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
                "support_type": support_type,
                "next_steps": response.get("next_steps", [])
            }
            
        except Exception as e:
            logger.error(f"Tier 1 support agent error: {e}")
            return {
                "message": "I apologize, but I'm having trouble processing your request. Let me escalate this to a specialist who can help you better.",
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
        # Check if the intent is within Tier 1 capabilities
        tier1_intents = [
            "account_access", "password_reset", "general_inquiry", 
            "billing_inquiry", "service_status", "basic_troubleshooting"
        ]
        
        can_handle_intent = state.current_intent in tier1_intents
        
        # Check if not too complex (no previous escalations)
        not_too_complex = state.escalation_level == 0
        
        # Check if customer sentiment is not too negative
        sentiment_ok = state.sentiment not in [Sentiment.FRUSTRATED]
        
        return can_handle_intent and not_too_complex and sentiment_ok
    
    def _get_agent_permissions(self) -> List[str]:
        """Get the permissions available to this agent"""
        return [
            "read_customer_data",
            "read_knowledge_base",
            "create_tickets",
            "update_tickets",
            "send_notifications",
            "basic_account_operations"
        ]
    
    def _initialize_faq_responses(self) -> Dict[str, Dict[str, Any]]:
        """Initialize FAQ responses for common questions"""
        return {
            "account_access": {
                "message": "I can help you with account access issues. Let me walk you through some quick steps to get you back into your account.",
                "steps": [
                    "First, let's try resetting your password using the 'Forgot Password' link",
                    "If that doesn't work, I can send a temporary access code to your registered email",
                    "Make sure you're using the correct username or email address"
                ],
                "confidence": 0.85
            },
            "password_reset": {
                "message": "I'll help you reset your password right away. This is a simple process that should take just a few minutes.",
                "steps": [
                    "I can send a password reset link to your registered email address",
                    "Click the link in the email within 30 minutes",
                    "Create a new password that meets our security requirements",
                    "Log in with your new password"
                ],
                "confidence": 0.9
            },
            "billing_inquiry": {
                "message": "I can help you understand your billing and account charges. Let me pull up your account information.",
                "steps": [
                    "Let me review your current billing information",
                    "I'll explain any charges or fees on your account",
                    "If you have questions about specific charges, I can provide details"
                ],
                "confidence": 0.75
            },
            "service_status": {
                "message": "Let me check the current status of our services and see if there are any known issues affecting your area.",
                "steps": [
                    "Checking service status in your region",
                    "Looking for any reported outages or maintenance",
                    "I'll provide updates on any ongoing issues"
                ],
                "confidence": 0.8
            }
        }
    
    def _initialize_troubleshooting_guides(self) -> Dict[str, Dict[str, Any]]:
        """Initialize basic troubleshooting guides"""
        return {
            "connection_issue": {
                "steps": [
                    "Check if your internet connection is working properly",
                    "Try refreshing the page or restarting the application",
                    "Clear your browser cache and cookies",
                    "Try using a different browser or device",
                    "Restart your router or modem if the issue persists"
                ],
                "estimated_time": "5-10 minutes"
            },
            "login_problem": {
                "steps": [
                    "Verify you're using the correct username and password",
                    "Check if Caps Lock is enabled",
                    "Try clearing your browser cache",
                    "Disable any browser extensions temporarily",
                    "Use the password reset option if needed"
                ],
                "estimated_time": "3-5 minutes"
            },
            "slow_performance": {
                "steps": [
                    "Close unnecessary browser tabs and applications",
                    "Check your internet connection speed",
                    "Clear browser cache and temporary files",
                    "Restart your browser",
                    "Try using a different browser"
                ],
                "estimated_time": "5-10 minutes"
            }
        }
    
    def _initialize_account_helpers(self) -> Dict[str, str]:
        """Initialize account-related helper messages"""
        return {
            "account_locked": "Your account appears to be temporarily locked for security reasons. I can help unlock it for you.",
            "expired_session": "Your session has expired for security. Please log in again to continue.",
            "invalid_credentials": "The credentials you're using don't match our records. Let's verify your account information.",
            "account_suspended": "I see there may be an issue with your account status. Let me check this for you and get it resolved."
        }
    
    async def _determine_support_type(self, message: str, state: AgentState) -> str:
        """Determine the type of support needed based on message and intent"""
        intent = state.current_intent.lower()
        message_lower = message.lower()
        
        # Map intents to support types
        intent_mapping = {
            "account_access": "account_access",
            "password_reset": "password_reset",
            "billing_inquiry": "billing_inquiry",
            "service_status": "service_status",
            "general_inquiry": "general_inquiry"
        }
        
        # Check for specific keywords that might override intent
        if any(word in message_lower for word in ["slow", "loading", "not working"]):
            return "troubleshooting"
        elif any(word in message_lower for word in ["locked", "can't login", "access denied"]):
            return "account_access"
        elif any(word in message_lower for word in ["bill", "charge", "payment", "cost"]):
            return "billing_inquiry"
        
        return intent_mapping.get(intent, "general_inquiry")
    
    async def _execute_support_action(
        self, 
        support_type: str, 
        message: str, 
        state: AgentState
    ) -> Dict[str, Any]:
        """Execute the appropriate support action"""
        
        if support_type in self.faq_responses:
            return await self._handle_faq_response(support_type, state)
        elif support_type == "troubleshooting":
            return await self._handle_troubleshooting(message, state)
        elif support_type == "account_verification":
            return await self._handle_account_verification(state)
        else:
            return await self._handle_general_inquiry(message, state)
    
    async def _handle_faq_response(self, support_type: str, state: AgentState) -> Dict[str, Any]:
        """Handle FAQ-type responses"""
        faq_data = self.faq_responses[support_type]
        
        # Get customer information if needed
        tools_used = []
        if support_type in ["account_access", "billing_inquiry"]:
            try:
                customer_data = await self.use_tool(
                    "get_customer_profile",
                    {"customer_id": state.customer.customer_id if state.customer else ""},
                    self.get_agent_context(state)
                )
                tools_used.append("get_customer_profile")
            except Exception as e:
                logger.warning(f"Failed to get customer profile: {e}")
        
        # Format response with steps
        response_message = faq_data["message"]
        if "steps" in faq_data:
            response_message += "\n\nHere are the steps I recommend:\n"
            for i, step in enumerate(faq_data["steps"], 1):
                response_message += f"{i}. {step}\n"
        
        return {
            "message": response_message,
            "confidence": faq_data["confidence"],
            "success": True,
            "actions_taken": [f"provided_{support_type}_guidance"],
            "tools_used": tools_used,
            "outcome": "guidance_provided",
            "next_steps": faq_data.get("steps", [])
        }
    
    async def _handle_troubleshooting(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Handle basic troubleshooting scenarios"""
        # Determine troubleshooting type
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["connect", "connection", "network"]):
            guide_type = "connection_issue"
        elif any(word in message_lower for word in ["login", "log in", "sign in"]):
            guide_type = "login_problem"
        elif any(word in message_lower for word in ["slow", "loading", "performance"]):
            guide_type = "slow_performance"
        else:
            guide_type = "connection_issue"  # Default
        
        guide = self.troubleshooting_guides[guide_type]
        
        # Try to get troubleshooting guide from knowledge base
        tools_used = []
        try:
            kb_result = await self.use_tool(
                "get_troubleshooting_guide",
                {
                    "issue_category": guide_type,
                    "product_type": "general",
                    "severity": "medium"
                },
                self.get_agent_context(state)
            )
            tools_used.append("get_troubleshooting_guide")
        except Exception as e:
            logger.warning(f"Failed to get troubleshooting guide: {e}")
        
        # Format response
        response_message = f"I'll help you troubleshoot this {guide_type.replace('_', ' ')}. "
        response_message += f"This should take about {guide['estimated_time']}.\n\n"
        response_message += "Please try these steps in order:\n"
        
        for i, step in enumerate(guide["steps"], 1):
            response_message += f"{i}. {step}\n"
        
        response_message += "\nPlease let me know which step resolves the issue, or if you need help with any of these steps."
        
        return {
            "message": response_message,
            "confidence": 0.8,
            "success": True,
            "actions_taken": [f"provided_{guide_type}_troubleshooting"],
            "tools_used": tools_used,
            "outcome": "troubleshooting_steps_provided",
            "next_steps": guide["steps"]
        }
    
    async def _handle_account_verification(self, state: AgentState) -> Dict[str, Any]:
        """Handle account verification scenarios"""
        tools_used = []
        
        try:
            # Get customer account information
            if state.customer:
                account_data = await self.use_tool(
                    "get_account_services",
                    {"customer_id": state.customer.customer_id},
                    self.get_agent_context(state)
                )
                tools_used.append("get_account_services")
                
                response_message = "I've verified your account information. "
                if account_data.get("success"):
                    response_message += "Your account is active and in good standing. "
                    if account_data.get("recent_activity"):
                        response_message += "I can see your recent account activity and everything looks normal."
                else:
                    response_message += "I notice there may be an issue with your account that requires attention."
                
                return {
                    "message": response_message,
                    "confidence": 0.85,
                    "success": account_data.get("success", False),
                    "actions_taken": ["account_verification"],
                    "tools_used": tools_used,
                    "outcome": "account_verified" if account_data.get("success") else "account_issue_detected"
                }
            else:
                return {
                    "message": "I'll need to verify some information to help you with your account. Could you please provide your account email or customer ID?",
                    "confidence": 0.6,
                    "success": False,
                    "actions_taken": ["requested_account_info"],
                    "tools_used": tools_used,
                    "outcome": "additional_info_needed"
                }
                
        except Exception as e:
            logger.error(f"Account verification failed: {e}")
            return {
                "message": "I'm having trouble accessing account information right now. Let me escalate this to a specialist who can help you.",
                "confidence": 0.0,
                "success": False,
                "actions_taken": ["account_verification_failed"],
                "tools_used": tools_used,
                "outcome": "verification_error",
                "requires_escalation": True
            }
    
    async def _handle_general_inquiry(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Handle general inquiries using knowledge base"""
        tools_used = []
        
        try:
            # Search knowledge base for relevant information
            kb_result = await self.use_tool(
                "search_knowledge_base",
                {
                    "query": message,
                    "category_filter": ["faq", "getting_started", "basic_support"],
                    "max_results": 3
                },
                self.get_agent_context(state)
            )
            tools_used.append("search_knowledge_base")
            
            if kb_result.get("success") and kb_result.get("results"):
                # Use the best matching result
                best_result = kb_result["results"][0]
                
                response_message = f"Based on your question, here's what I found:\n\n"
                response_message += best_result.get("content", "")
                
                if len(kb_result["results"]) > 1:
                    response_message += "\n\nI also found some related information that might be helpful. "
                    response_message += "Would you like me to share those details as well?"
                
                confidence = min(kb_result.get("confidence", 0.7), 0.8)
                
                return {
                    "message": response_message,
                    "confidence": confidence,
                    "success": True,
                    "actions_taken": ["knowledge_base_search"],
                    "tools_used": tools_used,
                    "outcome": "information_provided"
                }
            else:
                # No good matches found
                return {
                    "message": "I understand you're looking for information, but I don't have specific details about that topic in my knowledge base. Let me connect you with a specialist who can provide more detailed assistance.",
                    "confidence": 0.3,
                    "success": False,
                    "actions_taken": ["knowledge_base_search_no_results"],
                    "tools_used": tools_used,
                    "outcome": "no_information_found",
                    "requires_escalation": True
                }
                
        except Exception as e:
            logger.error(f"General inquiry handling failed: {e}")
            return {
                "message": "I'd like to help you with your question, but I'm having trouble accessing my knowledge base right now. Let me escalate this to ensure you get the information you need.",
                "confidence": 0.0,
                "success": False,
                "actions_taken": ["knowledge_base_error"],
                "tools_used": tools_used,
                "outcome": "search_error",
                "requires_escalation": True
            }
    
    async def _check_escalation_needed(self, response: Dict[str, Any], state: AgentState) -> bool:
        """Check if escalation is needed based on response and state"""
        escalation_triggers = [
            # Explicit escalation request in response
            response.get("requires_escalation", False),
            
            # Low confidence resolution
            response.get("confidence", 1.0) < 0.6,
            
            # Failed resolution attempt
            not response.get("success", True),
            
            # Customer has been through multiple resolution attempts
            len(state.resolution_attempts) >= 2,
            
            # Customer sentiment is negative/frustrated
            state.sentiment in [Sentiment.NEGATIVE, Sentiment.FRUSTRATED],
            
            # VIP customer with any issue
            (state.customer and 
             state.customer.tier.value in ["platinum", "gold"] and 
             response.get("confidence", 1.0) < 0.8)
        ]
        
        return any(escalation_triggers)