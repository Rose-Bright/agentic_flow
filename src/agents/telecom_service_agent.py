"""
Telecom Service Agent for handling phone number management requests via email
Specialized for disconnect and add line requests with SmartPath integration
"""

from typing import Dict, Any, List, Optional
import re
import asyncio
from datetime import datetime
from dataclasses import dataclass

from src.agents.base_agent import BaseAgent
from src.models.state import AgentState, Priority, CustomerTier, TicketStatus
from src.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PhoneNumberRequest:
    phone_number: str
    action: str  # 'disconnect' or 'add'
    service_type: str = "voice"  # voice, data, etc.
    validation_status: str = "pending"
    error_reason: Optional[str] = None


@dataclass
class EmailValidationResult:
    is_valid: bool
    customer_match: bool
    customer_id: Optional[str] = None
    validation_errors: List[str] = None


class TelecomServiceAgent(BaseAgent):
    """
    Specialized agent for handling telecom service requests via email.
    Handles phone number disconnection and addition requests with comprehensive validation.
    """
    
    def __init__(self):
        super().__init__(
            name="TelecomServiceAgent",
            model="gpt-4",
            capabilities=[
                "email_validation",
                "phone_number_management", 
                "service_requests",
                "smartpath_integration",
                "customer_verification"
            ],
            tools=[
                "validate_email_format",
                "lookup_customer_by_email",
                "send_email_reply",
                "validate_phone_number", 
                "get_customer_phone_services",
                "check_disconnect_eligibility",
                "check_add_line_capacity",
                "create_smartpath_ticket",
                "add_ticket_notes",
                "set_ticket_priority",
                "get_customer_profile",
                "update_customer_notes",
                "log_customer_interaction"
            ],
            confidence_threshold=0.8
        )
        
        # Phone number patterns for different formats
        self.phone_patterns = [
            r'\b(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})\b',  # 123-456-7890, 123.456.7890, 123 456 7890
            r'\b(\(\d{3}\)\s?\d{3}[-.\s]?\d{4})\b',  # (123) 456-7890
            r'\b(\+1[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4})\b',  # +1-123-456-7890
        ]
        
        # Intent keywords for service requests
        self.disconnect_keywords = [
            "disconnect", "cancel", "remove", "deactivate", "terminate", 
            "stop service", "discontinue", "suspend"
        ]
        
        self.add_keywords = [
            "add", "new line", "additional", "extra line", "another number",
            "second line", "activate", "connect", "install"
        ]
        
        # Email templates
        self.email_templates = {
            "invalid_email": {
                "subject": "Verification Required - Service Request",
                "body": """Dear Customer,

We received your service request but need to verify your identity. The email address you used ({email}) does not match our records for any active account.

Please:
1. Reply from your registered email address, or
2. Include your account number in your response, or
3. Contact us at 1-800-XXX-XXXX for immediate assistance

We're here to help!

Best regards,
Customer Service Team"""
            },
            "invalid_phone_numbers": {
                "subject": "Clarification Needed - Phone Number Request", 
                "body": """Dear {customer_name},

Thank you for your service request. We need clarification on the following phone numbers:

{invalid_numbers_list}

Please reply with:
1. The correct phone numbers you'd like to modify
2. Confirmation that these numbers are on your account
3. Your account number for verification

We'll process your request as soon as we receive this information.

Best regards,
Customer Service Team"""
            },
            "request_confirmation": {
                "subject": "Service Request Confirmed - Ticket #{ticket_id}",
                "body": """Dear {customer_name},

Your service request has been received and confirmed:

Request Details:
- Customer Account: {account_id}
- Request Type: {request_type}
- Phone Numbers: {phone_numbers}
- Ticket Number: {ticket_id}

Next Steps:
Our service team will process your request within 1-2 business days. You'll receive an email confirmation once the changes are complete.

If you have questions, reference ticket #{ticket_id} when contacting us.

Best regards,
Customer Service Team"""
            }
        }

    async def can_handle(self, state: AgentState) -> bool:
        """Determine if this agent can handle the current request"""
        # Check if it's an email-based telecom service request
        if not state.current_message:
            return False
            
        message_lower = state.current_message.lower()
        
        # Look for phone number patterns
        has_phone_numbers = any(
            re.search(pattern, state.current_message) 
            for pattern in self.phone_patterns
        )
        
        # Look for service request intent
        has_service_intent = (
            any(keyword in message_lower for keyword in self.disconnect_keywords) or
            any(keyword in message_lower for keyword in self.add_keywords)
        )
        
        # Check if it's from email channel
        is_email_channel = state.context.get("channel") == "email"
        
        return has_phone_numbers and has_service_intent and is_email_channel

    async def handle_message(self, message: str, state: AgentState) -> Dict[str, Any]:
        """Handle telecom service request from email"""
        try:
            logger.info(f"TelecomServiceAgent processing message for conversation {state.conversation_id}")
            
            # Step 1: Validate email and customer
            email_validation = await self._validate_email_and_customer(message, state)
            
            if not email_validation.is_valid or not email_validation.customer_match:
                return await self._handle_invalid_email(email_validation, state)
            
            # Step 2: Extract and validate phone numbers and service requests
            phone_requests = await self._extract_phone_requests(message)
            
            if not phone_requests:
                return await self._handle_no_phone_numbers_found(state)
            
            # Step 3: Validate phone numbers against customer profile
            validation_results = await self._validate_phone_numbers(phone_requests, state)
            
            invalid_requests = [req for req in validation_results if req.validation_status == "invalid"]
            if invalid_requests:
                return await self._handle_invalid_phone_numbers(invalid_requests, state)
            
            # Step 4: Process valid service requests
            processed_requests = await self._process_service_requests(validation_results, state)
            
            # Step 5: Create SmartPath tickets
            tickets = await self._create_smartpath_tickets(processed_requests, state)
            
            # Step 6: Send confirmation email
            await self._send_confirmation_email(tickets, processed_requests, state)
            
            # Step 7: Update state and prepare response
            return {
                "message": f"Successfully processed {len(processed_requests)} service request(s). Tickets created and customer notified via email.",
                "action": "service_request_processed",
                "confidence": 0.95,
                "data": {
                    "tickets_created": len(tickets),
                    "requests_processed": len(processed_requests),
                    "email_sent": True,
                    "next_agent": "human_service_center"
                },
                "should_escalate": False,
                "requires_human": True,  # Human agents will handle the actual service changes
                "next_action": "queue_for_service_center"
            }
            
        except Exception as e:
            logger.error(f"Error in TelecomServiceAgent: {e}")
            return {
                "message": "I encountered an issue processing your service request. Let me escalate this to a human agent who can assist you immediately.",
                "action": "error_escalation",
                "confidence": 0.3,
                "should_escalate": True,
                "error": str(e)
            }

    async def _validate_email_and_customer(self, message: str, state: AgentState) -> EmailValidationResult:
        """Validate sender email and match to customer profile"""
        sender_email = state.context.get("sender_email", "")
        
        if not sender_email:
            return EmailValidationResult(
                is_valid=False,
                customer_match=False,
                validation_errors=["No sender email found"]
            )
        
        # Validate email format
        email_format_result = await self.use_tool(
            "validate_email_format",
            {"email": sender_email},
            self.get_agent_context(state)
        )
        
        if not email_format_result.get("is_valid", False):
            return EmailValidationResult(
                is_valid=False,
                customer_match=False,
                validation_errors=["Invalid email format"]
            )
        
        # Look up customer by email
        customer_lookup_result = await self.use_tool(
            "lookup_customer_by_email", 
            {"email": sender_email},
            self.get_agent_context(state)
        )
        
        if customer_lookup_result.get("customer_found", False):
            return EmailValidationResult(
                is_valid=True,
                customer_match=True,
                customer_id=customer_lookup_result.get("customer_id")
            )
        else:
            return EmailValidationResult(
                is_valid=True,
                customer_match=False,
                validation_errors=["Email not associated with any customer account"]
            )

    async def _extract_phone_requests(self, message: str) -> List[PhoneNumberRequest]:
        """Extract phone numbers and determine requested actions"""
        phone_requests = []
        message_lower = message.lower()
        
        # Find all phone numbers
        phone_numbers = []
        for pattern in self.phone_patterns:
            matches = re.findall(pattern, message)
            phone_numbers.extend(matches)
        
        # Clean and normalize phone numbers
        normalized_numbers = []
        for number in phone_numbers:
            # Remove all non-digit characters except +
            clean_number = re.sub(r'[^\d+]', '', number)
            if clean_number.startswith('+1'):
                clean_number = clean_number[2:]  # Remove +1
            elif len(clean_number) == 11 and clean_number.startswith('1'):
                clean_number = clean_number[1:]  # Remove leading 1
            
            if len(clean_number) == 10:
                normalized_numbers.append(clean_number)
        
        # Determine action for each number based on context
        for number in normalized_numbers:
            action = self._determine_action_for_number(number, message_lower)
            phone_requests.append(PhoneNumberRequest(
                phone_number=number,
                action=action
            ))
        
        return phone_requests

    def _determine_action_for_number(self, phone_number: str, message_lower: str) -> str:
        """Determine whether to disconnect or add based on message context"""
        # Look for disconnect indicators near the phone number
        disconnect_indicators = sum(1 for keyword in self.disconnect_keywords if keyword in message_lower)
        add_indicators = sum(1 for keyword in self.add_keywords if keyword in message_lower)
        
        # Simple heuristic: if more disconnect keywords, assume disconnect
        if disconnect_indicators > add_indicators:
            return "disconnect"
        elif add_indicators > disconnect_indicators:
            return "add"
        else:
            # Default to disconnect if ambiguous (safer option)
            return "disconnect"

    async def _validate_phone_numbers(self, phone_requests: List[PhoneNumberRequest], state: AgentState) -> List[PhoneNumberRequest]:
        """Validate phone numbers against customer profile"""
        validated_requests = []
        
        # Get customer's current phone services
        phone_services_result = await self.use_tool(
            "get_customer_phone_services",
            {"customer_id": state.customer.customer_id if state.customer else None},
            self.get_agent_context(state)
        )
        
        customer_numbers = phone_services_result.get("phone_numbers", [])
        
        for request in phone_requests:
            # Validate the phone number format
            validation_result = await self.use_tool(
                "validate_phone_number",
                {"phone_number": request.phone_number},
                self.get_agent_context(state)
            )
            
            if not validation_result.get("is_valid", False):
                request.validation_status = "invalid"
                request.error_reason = "Invalid phone number format"
            elif request.action == "disconnect" and request.phone_number not in customer_numbers:
                request.validation_status = "invalid"
                request.error_reason = "Phone number not found on customer account"
            elif request.action == "add":
                # Check if customer can add more lines
                capacity_result = await self.use_tool(
                    "check_add_line_capacity",
                    {"customer_id": state.customer.customer_id if state.customer else None},
                    self.get_agent_context(state)
                )
                
                if not capacity_result.get("can_add_line", False):
                    request.validation_status = "invalid"
                    request.error_reason = capacity_result.get("reason", "Cannot add additional lines")
                else:
                    request.validation_status = "valid"
            else:
                # Disconnect request for valid number
                eligibility_result = await self.use_tool(
                    "check_disconnect_eligibility",
                    {
                        "customer_id": state.customer.customer_id if state.customer else None,
                        "phone_number": request.phone_number
                    },
                    self.get_agent_context(state)
                )
                
                if eligibility_result.get("eligible", False):
                    request.validation_status = "valid"
                else:
                    request.validation_status = "invalid"
                    request.error_reason = eligibility_result.get("reason", "Not eligible for disconnection")
            
            validated_requests.append(request)
        
        return validated_requests

    async def _process_service_requests(self, phone_requests: List[PhoneNumberRequest], state: AgentState) -> List[PhoneNumberRequest]:
        """Process valid service requests"""
        processed_requests = []
        
        for request in phone_requests:
            if request.validation_status == "valid":
                # Log the interaction
                await self.use_tool(
                    "log_customer_interaction",
                    {
                        "customer_id": state.customer.customer_id if state.customer else None,
                        "interaction_type": f"phone_{request.action}_request",
                        "phone_number": request.phone_number,
                        "channel": "email",
                        "timestamp": datetime.now().isoformat()
                    },
                    self.get_agent_context(state)
                )
                
                processed_requests.append(request)
        
        return processed_requests

    async def _create_smartpath_tickets(self, requests: List[PhoneNumberRequest], state: AgentState) -> List[Dict[str, Any]]:
        """Create SmartPath tickets for each valid request"""
        tickets = []
        
        for request in requests:
            # Determine priority based on customer tier and request type
            priority = self._determine_ticket_priority(request, state)
            
            # Create ticket
            ticket_result = await self.use_tool(
                "create_smartpath_ticket",
                {
                    "customer_id": state.customer.customer_id if state.customer else None,
                    "category": "Service Change",
                    "subcategory": f"Phone {request.action.title()}",
                    "description": f"Customer requested to {request.action} phone number {request.phone_number}",
                    "priority": priority.value,
                    "channel": "email",
                    "phone_number": request.phone_number,
                    "service_type": request.service_type
                },
                self.get_agent_context(state)
            )
            
            ticket_id = ticket_result.get("ticket_id")
            if ticket_id:
                # Add detailed notes
                notes = self._generate_ticket_notes(request, state)
                await self.use_tool(
                    "add_ticket_notes",
                    {
                        "ticket_id": ticket_id,
                        "notes": notes,
                        "agent_id": self.name
                    },
                    self.get_agent_context(state)
                )
                
                tickets.append({
                    "ticket_id": ticket_id,
                    "request": request,
                    "priority": priority
                })
        
        return tickets

    def _determine_ticket_priority(self, request: PhoneNumberRequest, state: AgentState) -> Priority:
        """Determine ticket priority based on customer and request"""
        if state.customer and state.customer.tier == CustomerTier.PLATINUM:
            return Priority.HIGH
        elif state.customer and state.customer.tier == CustomerTier.GOLD:
            return Priority.MEDIUM
        elif request.action == "disconnect":
            return Priority.MEDIUM  # Disconnects are typically higher priority
        else:
            return Priority.LOW

    def _generate_ticket_notes(self, request: PhoneNumberRequest, state: AgentState) -> str:
        """Generate detailed notes for the SmartPath ticket"""
        notes = f"""=== TELECOM SERVICE REQUEST ===
Request Type: {request.action.upper()} phone line
Phone Number: {request.phone_number}
Service Type: {request.service_type}
Channel: Email
Customer Email: {state.context.get('sender_email', 'N/A')}
Request Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

=== VALIDATION COMPLETED ===
- Email validated and matched to customer profile
- Phone number validated against customer account
- Service eligibility confirmed
- Customer permissions verified

=== REQUIRED ACTIONS ===
"""
        
        if request.action == "disconnect":
            notes += """1. Verify final customer authorization
2. Check for any outstanding balances
3. Process line disconnection
4. Update billing for pro-rated charges
5. Send service termination confirmation
6. Update customer profile"""
        else:  # add
            notes += """1. Verify customer credit and account standing
2. Provision new phone line
3. Configure service features
4. Update billing for new line charges
5. Send service activation confirmation
6. Update customer profile"""
        
        notes += f"""

=== CUSTOMER CONTEXT ===
Customer Tier: {state.customer.tier.value if state.customer else 'Unknown'}
Account Status: {state.customer.account_status if state.customer else 'Unknown'}
Previous Interactions: {len(state.customer.previous_interactions) if state.customer else 0}

Process immediately - Customer verified via email channel."""
        
        return notes

    async def _send_confirmation_email(self, tickets: List[Dict[str, Any]], requests: List[PhoneNumberRequest], state: AgentState):
        """Send confirmation email to customer"""
        if not tickets:
            return
        
        customer_name = state.customer.name if state.customer else "Valued Customer"
        sender_email = state.context.get("sender_email", "")
        account_id = state.customer.customer_id if state.customer else "N/A"
        
        # Prepare request summary
        request_summary = []
        ticket_numbers = []
        
        for ticket_info in tickets:
            request = ticket_info["request"]
            ticket_id = ticket_info["ticket_id"]
            request_summary.append(f"{request.action.title()} - {request.phone_number}")
            ticket_numbers.append(ticket_id)
        
        # Send confirmation email
        await self.use_tool(
            "send_email_reply",
            {
                "to_email": sender_email,
                "subject": self.email_templates["request_confirmation"]["subject"].format(
                    ticket_id=ticket_numbers[0] if ticket_numbers else "TBD"
                ),
                "body": self.email_templates["request_confirmation"]["body"].format(
                    customer_name=customer_name,
                    account_id=account_id,
                    request_type=", ".join(request_summary),
                    phone_numbers=", ".join([req.phone_number for req in requests]),
                    ticket_id=", ".join(ticket_numbers)
                ),
                "email_type": "service_confirmation"
            },
            self.get_agent_context(state)
        )

    async def _handle_invalid_email(self, validation_result: EmailValidationResult, state: AgentState) -> Dict[str, Any]:
        """Handle invalid email or customer mismatch"""
        sender_email = state.context.get("sender_email", "unknown@email.com")
        
        await self.use_tool(
            "send_email_reply",
            {
                "to_email": sender_email,
                "subject": self.email_templates["invalid_email"]["subject"],
                "body": self.email_templates["invalid_email"]["body"].format(email=sender_email),
                "email_type": "verification_required"
            },
            self.get_agent_context(state)
        )
        
        return {
            "message": "Email validation failed. Customer verification email sent.",
            "action": "email_verification_required",
            "confidence": 0.9,
            "should_escalate": False,
            "data": {"verification_email_sent": True}
        }

    async def _handle_invalid_phone_numbers(self, invalid_requests: List[PhoneNumberRequest], state: AgentState) -> Dict[str, Any]:
        """Handle invalid phone number requests"""
        sender_email = state.context.get("sender_email", "")
        customer_name = state.customer.name if state.customer else "Valued Customer"
        
        # Format invalid numbers list
        invalid_numbers_list = []
        for request in invalid_requests:
            invalid_numbers_list.append(f"- {request.phone_number}: {request.error_reason}")
        
        await self.use_tool(
            "send_email_reply",
            {
                "to_email": sender_email,
                "subject": self.email_templates["invalid_phone_numbers"]["subject"],
                "body": self.email_templates["invalid_phone_numbers"]["body"].format(
                    customer_name=customer_name,
                    invalid_numbers_list="\n".join(invalid_numbers_list)
                ),
                "email_type": "clarification_required"
            },
            self.get_agent_context(state)
        )
        
        return {
            "message": f"Phone number validation failed for {len(invalid_requests)} number(s). Clarification email sent to customer.",
            "action": "phone_validation_failed",
            "confidence": 0.85,
            "should_escalate": False,
            "data": {"clarification_email_sent": True, "invalid_count": len(invalid_requests)}
        }

    async def _handle_no_phone_numbers_found(self, state: AgentState) -> Dict[str, Any]:
        """Handle case where no phone numbers were found in the message"""
        return {
            "message": "No valid phone numbers found in the service request. This may require human review.",
            "action": "no_phone_numbers_found",
            "confidence": 0.4,
            "should_escalate": True,
            "escalation_reason": "Unable to extract phone numbers from service request"
        }

    def _get_agent_permissions(self) -> List[str]:
        """Get the permissions available to this agent"""
        return [
            "read_customer_data",
            "read_phone_services",
            "create_tickets",
            "update_tickets",
            "send_notifications",
            "write_analytics",
            "validate_service_requests"
        ]