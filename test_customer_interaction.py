"""
Customer Interaction Testing Script

This script allows you to test the Contact Center AI system as a customer
interacting with the support agents.
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Optional, Dict, Any


class CustomerTestClient:
    """Test client for simulating customer interactions"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.conversation_id: Optional[str] = None
        
    async def authenticate(self, username: str = "johndoe", password: str = "secret") -> bool:
        """Authenticate and get access token"""
        print(f"🔐 Authenticating as {username}...")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/token",
                    data={"username": username, "password": password},
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    self.token = token_data["access_token"]
                    print("✅ Authentication successful!")
                    return True
                else:
                    print(f"❌ Authentication failed: {response.status_code} - {response.text}")
                    return False
                    
            except Exception as e:
                print(f"❌ Authentication error: {str(e)}")
                return False
    
    async def start_conversation(self, 
                               customer_id: str = "CUST_001",
                               channel: str = "web",
                               initial_message: str = "Hello, I need help with my account",
                               priority: str = "medium") -> bool:
        """Start a new conversation with the support system"""
        
        if not self.token:
            print("❌ Please authenticate first!")
            return False
            
        print(f"💬 Starting conversation: '{initial_message}'")
        
        async with httpx.AsyncClient() as client:
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                payload = {
                    "customer_id": customer_id,
                    "channel": channel,
                    "initial_message": initial_message,
                    "priority": priority
                }
                
                response = await client.post(
                    f"{self.base_url}/api/v1/conversations",
                    json=payload,
                    headers=headers
                )
                
                if response.status_code in [200, 201]:
                    conversation_data = response.json()
                    self.conversation_id = conversation_data.get("conversation_id")
                    agent_type = conversation_data.get("agent_type", "unknown")
                    agent_response = conversation_data.get("response", "No response")
                    
                    print(f"✅ Conversation started!")
                    print(f"📋 Conversation ID: {self.conversation_id}")
                    print(f"🤖 Assigned Agent: {agent_type}")
                    print(f"💭 Agent Response: {agent_response}")
                    print("-" * 50)
                    
                    return True
                else:
                    print(f"❌ Failed to start conversation: {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                    
            except Exception as e:
                print(f"❌ Error starting conversation: {str(e)}")
                return False
    
    async def send_message(self, message: str) -> bool:
        """Send a message to the current conversation"""
        
        if not self.token or not self.conversation_id:
            print("❌ No active conversation. Please start a conversation first!")
            return False
            
        print(f"📤 You: {message}")
        
        async with httpx.AsyncClient() as client:
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                payload = {"content": message}
                
                response = await client.post(
                    f"{self.base_url}/api/v1/conversations/{self.conversation_id}/messages",
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    message_data = response.json()
                    agent_type = message_data.get("agent_type", "Agent")
                    content = message_data.get("content", "No response")
                    confidence = message_data.get("confidence_score", 0.0)
                    
                    print(f"📥 {agent_type}: {content}")
                    print(f"🎯 Confidence: {confidence:.2f}")
                    print("-" * 50)
                    
                    return True
                else:
                    print(f"❌ Failed to send message: {response.status_code}")
                    print(f"Response: {response.text}")
                    return False
                    
            except Exception as e:
                print(f"❌ Error sending message: {str(e)}")
                return False
    
    async def get_conversation_status(self) -> Dict[str, Any]:
        """Get the current conversation status"""
        
        if not self.token or not self.conversation_id:
            print("❌ No active conversation!")
            return {}
            
        async with httpx.AsyncClient() as client:
            try:
                headers = {"Authorization": f"Bearer {self.token}"}
                
                response = await client.get(
                    f"{self.base_url}/api/v1/conversations/{self.conversation_id}/state",
                    headers=headers
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"❌ Failed to get status: {response.status_code}")
                    return {}
                    
            except Exception as e:
                print(f"❌ Error getting status: {str(e)}")
                return {}
    
    async def check_health(self) -> bool:
        """Check if the service is healthy"""
        print("🏥 Checking service health...")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/health")
                
                if response.status_code == 200:
                    health_data = response.json()
                    print(f"✅ Service is healthy: {health_data.get('status')}")
                    return True
                else:
                    print(f"❌ Service health check failed: {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"❌ Health check error: {str(e)}")
                return False


async def interactive_test_session():
    """Run an interactive test session"""
    
    print("=" * 60)
    print("🤖 CONTACT CENTER AI - Customer Test Interface")
    print("=" * 60)
    
    client = CustomerTestClient()
    
    # Check service health
    if not await client.check_health():
        print("❌ Service is not available. Make sure the application is running.")
        return
    
    # Authenticate
    if not await client.authenticate():
        print("❌ Authentication failed. Cannot proceed.")
        return
    
    print("\n📋 Test Scenarios Available:")
    print("1. General Support Query")
    print("2. Technical Issue")
    print("3. Billing Question") 
    print("4. Sales Inquiry")
    print("5. Custom Message")
    
    while True:
        try:
            choice = input("\nSelect a scenario (1-5) or 'q' to quit: ").strip()
            
            if choice.lower() == 'q':
                break
            
            scenarios = {
                "1": "I'm having trouble accessing my account dashboard",
                "2": "My internet connection keeps dropping every few minutes",
                "3": "I was charged twice for the same service this month",
                "4": "I'm interested in upgrading to your premium plan",
                "5": None  # Custom message
            }
            
            if choice in scenarios:
                if choice == "5":
                    message = input("Enter your custom message: ").strip()
                else:
                    message = scenarios[choice]
                
                if message:
                    # Start conversation if this is the first message
                    if not client.conversation_id:
                        success = await client.start_conversation(
                            initial_message=message,
                            customer_id=f"TEST_CUSTOMER_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        )
                        if not success:
                            continue
                    else:
                        # Send as follow-up message
                        await client.send_message(message)
                    
                    # Allow follow-up messages
                    while True:
                        follow_up = input("\nEnter follow-up message (or press Enter to return to menu): ").strip()
                        if not follow_up:
                            break
                        await client.send_message(follow_up)
            else:
                print("❌ Invalid choice. Please select 1-5 or 'q'.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")


async def automated_test_scenarios():
    """Run automated test scenarios"""
    
    print("=" * 60)
    print("🤖 AUTOMATED TEST SCENARIOS")
    print("=" * 60)
    
    client = CustomerTestClient()
    
    # Health check
    if not await client.check_health():
        return False
    
    # Authentication test
    print("\n1. Testing Authentication...")
    if not await client.authenticate():
        return False
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Basic FAQ Query",
            "initial_message": "What are your business hours?",
            "follow_ups": ["Do you have weekend support?"]
        },
        {
            "name": "Technical Support",
            "initial_message": "My internet connection is very slow",
            "follow_ups": [
                "It's been happening for the past 3 days",
                "I've already restarted my router"
            ]
        },
        {
            "name": "Billing Inquiry",
            "initial_message": "I need help understanding my bill",
            "follow_ups": ["There's a charge I don't recognize"]
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{i+1}. Testing: {scenario['name']}")
        
        # Start new conversation for each scenario
        client.conversation_id = None
        
        success = await client.start_conversation(
            initial_message=scenario["initial_message"],
            customer_id=f"AUTO_TEST_{i}"
        )
        
        if success:
            # Send follow-up messages
            for follow_up in scenario["follow_ups"]:
                await asyncio.sleep(2)  # Brief pause between messages
                await client.send_message(follow_up)
    
    print("\n✅ All automated tests completed!")
    return True


async def main():
    """Main function to choose test mode"""
    
    print("Contact Center AI - Customer Testing Tool")
    print("1. Interactive Test Session")
    print("2. Automated Test Scenarios")
    
    choice = input("Select mode (1 or 2): ").strip()
    
    if choice == "1":
        await interactive_test_session()
    elif choice == "2":
        await automated_test_scenarios()
    else:
        print("Invalid choice. Exiting.")


if __name__ == "__main__":
    asyncio.run(main())