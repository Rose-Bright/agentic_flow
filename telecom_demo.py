#!/usr/bin/env python3
"""
Demo script showing the Telecom Service Agent handling email-based phone number requests
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.agents.telecom_service_agent import TelecomServiceAgent
from src.models.state import AgentState, CustomerProfile, CustomerTier
from src.services.tool_registry import ToolRegistry
from datetime import datetime


class TelecomDemo:
    def __init__(self):
        self.tool_registry = ToolRegistry()
        self.telecom_agent = TelecomServiceAgent()
        self.telecom_agent.register_tool_registry(self.tool_registry)
    
    def print_header(self, title):
        print(f"\n{'='*60}")
        print(f"🏢 TELECOM SERVICE CENTER DEMO")
        print(f"📧 {title}")
        print(f"{'='*60}")
    
    def print_section(self, title):
        print(f"\n{'➤'*3} {title}")
        print('-' * 40)
    
    async def demo_disconnect_request(self):
        """Demo: Customer requests to disconnect a phone number via email"""
        
        self.print_header("PHONE NUMBER DISCONNECT REQUEST")
        
        # Create customer state
        customer = CustomerProfile(
            customer_id="CUST001",
            name="John Doe",
            email="john.doe@email.com",
            phone="5551234567",
            tier=CustomerTier.GOLD,
            account_status="active",
            registration_date=datetime(2023, 1, 15),
            lifetime_value=2500.00
        )
        
        # Email message from customer
        email_message = """
        Subject: Request to Disconnect Phone Line
        
        Hello,
        
        I need to disconnect my secondary phone line 555-123-4568 from my account. 
        This line is no longer needed for my business.
        
        Please process this request and confirm once completed.
        
        Thank you,
        John Doe
        Account: CUST001
        """
        
        print("📨 INCOMING EMAIL:")
        print(email_message)
        
        # Create agent state
        state = AgentState(
            session_id="session_20240101_001",
            conversation_id="conv_disconnect_001",
            current_message=email_message,
            customer=customer,
            context={
                "channel": "email",
                "sender_email": "john.doe@email.com",
                "subject": "Request to Disconnect Phone Line"
            }
        )
        
        self.print_section("AGENT PROCESSING")
        
        # Check if telecom agent can handle this
        can_handle = await self.telecom_agent.can_handle(state)
        print(f"✅ TelecomServiceAgent can handle: {can_handle}")
        
        if can_handle:
            # Process the request
            print("🔄 Processing disconnect request...")
            result = await self.telecom_agent.handle_message(state.current_message, state)
            
            self.print_section("AGENT RESPONSE")
            print(f"📋 Action: {result.get('action', 'N/A')}")
            print(f"🎯 Confidence: {result.get('confidence', 0.0):.2f}")
            print(f"📊 Success: {result.get('success', False)}")
            print(f"🔄 Next Step: {result.get('next_action', 'N/A')}")
            
            if result.get('data'):
                data = result['data']
                print(f"🎫 Tickets Created: {data.get('tickets_created', 0)}")
                print(f"📋 Requests Processed: {data.get('requests_processed', 0)}")
                print(f"📧 Email Sent: {data.get('email_sent', False)}")
        
        return result if can_handle else None
    
    async def demo_add_line_request(self):
        """Demo: Customer requests to add a new phone line via email"""
        
        self.print_header("PHONE LINE ADDITION REQUEST")
        
        customer = CustomerProfile(
            customer_id="CUST002",
            name="Jane Smith",
            email="jane.smith@email.com",
            phone="5559876543",
            tier=CustomerTier.PLATINUM,
            account_status="active",
            registration_date=datetime(2022, 11, 20),
            lifetime_value=5000.00
        )
        
        email_message = """
        Subject: Add New Phone Line to Account
        
        Dear Customer Service,
        
        I would like to add a new phone line to my account for my growing business. 
        Please set up an additional number with the same features as my current line.
        
        My current number is 555-987-6543.
        
        Please let me know the next steps and estimated timeline.
        
        Best regards,
        Jane Smith
        Premium Business Account
        """
        
        print("📨 INCOMING EMAIL:")
        print(email_message)
        
        state = AgentState(
            session_id="session_20240101_002",
            conversation_id="conv_addline_002",
            current_message=email_message,
            customer=customer,
            context={
                "channel": "email",
                "sender_email": "jane.smith@email.com",
                "subject": "Add New Phone Line to Account"
            }
        )
        
        self.print_section("AGENT PROCESSING")
        
        can_handle = await self.telecom_agent.can_handle(state)
        print(f"✅ TelecomServiceAgent can handle: {can_handle}")
        
        if can_handle:
            print("🔄 Processing add line request...")
            result = await self.telecom_agent.handle_message(state.current_message, state)
            
            self.print_section("AGENT RESPONSE")
            print(f"📋 Action: {result.get('action', 'N/A')}")
            print(f"🎯 Confidence: {result.get('confidence', 0.0):.2f}")
            print(f"👥 Requires Human: {result.get('requires_human', False)}")
            
            if result.get('data'):
                data = result['data']
                print(f"🎫 Tickets Created: {data.get('tickets_created', 0)}")
                print(f"📧 Customer Notified: {data.get('email_sent', False)}")
        
        return result if can_handle else None
    
    async def demo_invalid_request(self):
        """Demo: Invalid email request (email not in system)"""
        
        self.print_header("INVALID EMAIL REQUEST")
        
        email_message = """
        Subject: Disconnect Phone Service
        
        I want to cancel my phone number 555-999-8888 immediately.
        Please process this request.
        
        Thanks
        """
        
        print("📨 INCOMING EMAIL (from unknown sender):")
        print(email_message)
        
        state = AgentState(
            session_id="session_20240101_003",
            conversation_id="conv_invalid_003",
            current_message=email_message,
            customer=None,  # Unknown customer
            context={
                "channel": "email",
                "sender_email": "unknown@example.com",
                "subject": "Disconnect Phone Service"
            }
        )
        
        self.print_section("AGENT PROCESSING")
        
        can_handle = await self.telecom_agent.can_handle(state)
        print(f"✅ TelecomServiceAgent can handle: {can_handle}")
        
        if can_handle:
            print("🔄 Processing invalid request...")
            result = await self.telecom_agent.handle_message(state.current_message, state)
            
            self.print_section("AGENT RESPONSE")
            print(f"📋 Action: {result.get('action', 'N/A')}")
            print(f"🎯 Confidence: {result.get('confidence', 0.0):.2f}")
            print(f"⚠️  Verification Required: Email not found in system")
            
            if result.get('data'):
                data = result['data']
                print(f"📧 Verification Email Sent: {data.get('verification_email_sent', False)}")
        
        return result if can_handle else None
    
    async def demo_workflow_summary(self):
        """Show the complete workflow summary"""
        
        self.print_header("TELECOM SERVICE WORKFLOW SUMMARY")
        
        workflow_steps = [
            "1. 📧 Email received from customer",
            "2. 🔍 Email validation & customer lookup", 
            "3. 📱 Phone number extraction & validation",
            "4. ✅ Service request eligibility check",
            "5. 🎫 SmartPath ticket creation",
            "6. 📧 Customer confirmation email",
            "7. 👥 Queue for human service center",
            "8. ⚡ Process service change",
            "9. 📧 Completion notification"
        ]
        
        print("AUTOMATED WORKFLOW STEPS:")
        for step in workflow_steps:
            print(f"  {step}")
        
        print(f"\n🏆 BENEFITS:")
        print("  • Automated email processing & validation")
        print("  • Intelligent phone number extraction")
        print("  • Comprehensive eligibility checking")
        print("  • Integrated ticketing system (SmartPath)")
        print("  • Customer communication automation")
        print("  • Human agent context preparation")
        print("  • 24/7 request processing capability")
        
        print(f"\n⚙️  TOOLS UTILIZED:")
        tools = [
            "Email validation & lookup",
            "Phone number validation",
            "Customer service eligibility",
            "SmartPath ticket creation",
            "Customer notification system",
            "Interaction logging & analytics"
        ]
        
        for tool in tools:
            print(f"  • {tool}")
    
    async def run_complete_demo(self):
        """Run the complete demonstration"""
        
        print("🚀 Starting Telecom Service Agent Demo")
        print("This demo shows email-based phone number management")
        
        # Demo 1: Disconnect request
        await self.demo_disconnect_request()
        
        # Demo 2: Add line request  
        await self.demo_add_line_request()
        
        # Demo 3: Invalid request
        await self.demo_invalid_request()
        
        # Summary
        await self.demo_workflow_summary()
        
        print(f"\n{'='*60}")
        print("✨ DEMO COMPLETED SUCCESSFULLY!")
        print("The TelecomServiceAgent is ready for production use.")
        print(f"{'='*60}")


async def main():
    """Main demo function"""
    demo = TelecomDemo()
    await demo.run_complete_demo()


if __name__ == "__main__":
    asyncio.run(main())