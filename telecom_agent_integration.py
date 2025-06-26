#!/usr/bin/env python3
"""
Integration script to add TelecomServiceAgent to the existing system
"""

import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.agents.telecom_service_agent import TelecomServiceAgent
from src.models.state import AgentState, CustomerProfile, CustomerTier
from src.services.tool_registry import ToolRegistry
from datetime import datetime


async def test_telecom_agent():
    """Test the TelecomServiceAgent functionality"""
    
    print("🔧 Testing TelecomServiceAgent Integration")
    print("=" * 50)
    
    # Initialize tool registry
    tool_registry = ToolRegistry()
    
    # Initialize telecom service agent
    telecom_agent = TelecomServiceAgent()
    telecom_agent.register_tool_registry(tool_registry)
    
    print("✅ TelecomServiceAgent initialized successfully")
    
    # Test case 1: Email-based phone disconnect request
    print("\n📧 Test Case 1: Phone Disconnect Request")
    print("-" * 30)
    
    state = AgentState(
        session_id="test_session_001",
        conversation_id="test_conv_001",
        current_message="I need to disconnect my phone number 555-123-4567. Please cancel this line from my account.",
        customer=CustomerProfile(
            customer_id="CUST001",
            name="John Doe",
            email="john.doe@email.com",
            phone="5551234567",
            tier=CustomerTier.GOLD,
            account_status="active",
            registration_date=datetime.now(),
            lifetime_value=2500.00
        ),
        context={"channel": "email", "sender_email": "john.doe@email.com"}
    )
    
    # Test can_handle
    can_handle = await telecom_agent.can_handle(state)
    print(f"Can handle request: {can_handle}")
    
    if can_handle:
        # Process the request
        result = await telecom_agent.handle_message(state.current_message, state)
        print(f"Agent response: {result.get('message', 'No message')}")
        print(f"Action taken: {result.get('action', 'No action')}")
        print(f"Confidence: {result.get('confidence', 0.0)}")
        print(f"Success: {result.get('success', False)}")
    
    # Test case 2: Email-based phone add request
    print("\n📧 Test Case 2: Phone Add Request")
    print("-" * 30)
    
    state2 = AgentState(
        session_id="test_session_002",
        conversation_id="test_conv_002", 
        current_message="I would like to add a new phone line to my account. Please set up an additional number for my business.",
        customer=CustomerProfile(
            customer_id="CUST002",
            name="Jane Smith",
            email="jane.smith@email.com",
            phone="5559876543",
            tier=CustomerTier.PLATINUM,
            account_status="active",
            registration_date=datetime.now(),
            lifetime_value=5000.00
        ),
        context={"channel": "email", "sender_email": "jane.smith@email.com"}
    )
    
    can_handle2 = await telecom_agent.can_handle(state2)
    print(f"Can handle request: {can_handle2}")
    
    if can_handle2:
        result2 = await telecom_agent.handle_message(state2.current_message, state2)
        print(f"Agent response: {result2.get('message', 'No message')}")
        print(f"Action taken: {result2.get('action', 'No action')}")
        print(f"Confidence: {result2.get('confidence', 0.0)}")
    
    # Test case 3: Invalid email request
    print("\n📧 Test Case 3: Invalid Email Request")
    print("-" * 30)
    
    state3 = AgentState(
        session_id="test_session_003",
        conversation_id="test_conv_003",
        current_message="I want to disconnect 555-999-8888 from my account",
        customer=None,  # No customer profile
        context={"channel": "email", "sender_email": "unknown@invalid.com"}
    )
    
    can_handle3 = await telecom_agent.can_handle(state3)
    print(f"Can handle request: {can_handle3}")
    
    if can_handle3:
        result3 = await telecom_agent.handle_message(state3.current_message, state3)
        print(f"Agent response: {result3.get('message', 'No message')}")
        print(f"Action taken: {result3.get('action', 'No action')}")
    
    print("\n🎉 TelecomServiceAgent testing completed!")
    print("=" * 50)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_telecom_agent())