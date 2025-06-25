"""
Quick Test Script - Verify Contact Center AI is working
"""

import asyncio
import httpx
import json
from datetime import datetime


async def quick_test():
    """Run a quick test to verify the system is working"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Contact Center AI - Quick Test")
    print("=" * 40)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            
            # 1. Health Check
            print("1. Testing health endpoint...")
            health_response = await client.get(f"{base_url}/health")
            
            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"   ✅ Health: {health_data.get('status')}")
            else:
                print(f"   ❌ Health check failed: {health_response.status_code}")
                return False
            
            # 2. Authentication
            print("2. Testing authentication...")
            auth_response = await client.post(
                f"{base_url}/token",
                data={"username": "johndoe", "password": "secret"},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if auth_response.status_code == 200:
                token_data = auth_response.json()
                token = token_data["access_token"]
                print(f"   ✅ Authentication successful")
            else:
                print(f"   ❌ Authentication failed: {auth_response.status_code}")
                print(f"   Response: {auth_response.text}")
                return False
            
            # 3. Start Conversation
            print("3. Testing conversation start...")
            headers = {"Authorization": f"Bearer {token}"}
            conversation_data = {
                "customer_id": "QUICK_TEST_001",
                "channel": "web",
                "initial_message": "Hello, I need help with my account",
                "priority": "medium"
            }
            
            conv_response = await client.post(
                f"{base_url}/api/v1/conversations",
                json=conversation_data,
                headers=headers
            )
            
            if conv_response.status_code in [200, 201]:
                conversation = conv_response.json()
                conversation_id = conversation["conversation_id"]
                agent_type = conversation["agent_type"]
                response_text = conversation["response"]
                
                print(f"   ✅ Conversation started")
                print(f"   📋 ID: {conversation_id}")
                print(f"   🤖 Agent: {agent_type}")
                print(f"   💬 Response: {response_text[:100]}...")
            else:
                print(f"   ❌ Conversation start failed: {conv_response.status_code}")
                print(f"   Response: {conv_response.text}")
                return False
            
            # 4. Send Follow-up Message
            print("4. Testing follow-up message...")
            message_data = {"content": "I can't access my billing information"}
            
            msg_response = await client.post(
                f"{base_url}/api/v1/conversations/{conversation_id}/messages",
                json=message_data,
                headers=headers
            )
            
            if msg_response.status_code == 200:
                message = msg_response.json()
                agent_response = message["content"]
                confidence = message["confidence_score"]
                
                print(f"   ✅ Follow-up message sent")
                print(f"   💬 Agent Response: {agent_response[:100]}...")
                print(f"   🎯 Confidence: {confidence:.2f}")
            else:
                print(f"   ❌ Follow-up message failed: {msg_response.status_code}")
                print(f"   Response: {msg_response.text}")
                return False
            
            # 5. Get Conversation State
            print("5. Testing conversation state...")
            state_response = await client.get(
                f"{base_url}/api/v1/conversations/{conversation_id}/state",
                headers=headers
            )
            
            if state_response.status_code == 200:
                state = state_response.json()
                status = state.get("status", "unknown")
                message_count = len(state.get("conversation_history", []))
                
                print(f"   ✅ State retrieved")
                print(f"   📊 Status: {status}")
                print(f"   📝 Messages: {message_count}")
            else:
                print(f"   ❌ State retrieval failed: {state_response.status_code}")
                print(f"   Response: {state_response.text}")
            
            print("\n🎉 All tests passed! The Contact Center AI is working correctly.")
            print("\nNext steps:")
            print("- Run: python test_customer_interaction.py")
            print("- Try different conversation scenarios")
            print("- Check the API documentation at http://localhost:8000/docs")
            
            return True
            
    except httpx.ConnectError:
        print("❌ Cannot connect to the application.")
        print("Make sure the application is running on http://localhost:8000")
        print("Run: python -m src.main")
        return False
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False


if __name__ == "__main__":
    success = asyncio.run(quick_test())
    if not success:
        print("\n💡 Troubleshooting:")
        print("1. Make sure the application is running: python -m src.main")
        print("2. Check if port 8000 is available")
        print("3. Verify dependencies are installed: pip install -r requirements.txt")
        print("4. Check application logs for errors")
        exit(1)
    else:
        print("\n✅ System is ready for customer interactions!")