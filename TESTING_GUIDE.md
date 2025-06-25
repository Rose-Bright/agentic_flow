# 🧪 Contact Center AI - Testing Guide

This guide provides comprehensive instructions for testing the Contact Center Agentic Flow System as a customer interacting with AI support agents.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Running Contact Center AI application (on port 8000)
- Dependencies installed (`pip install -r requirements.txt`)

### 1. Start the Application
```bash
# Make sure the application is running
python -m src.main
```
The application should be listening on `http://localhost:8000`

### 2. Run Customer Test Interface
```bash
# Interactive testing
python test_customer_interaction.py

# Or run automated scenarios
python test_customer_interaction.py
# Select option 2 when prompted
```

## 📋 Available Testing Methods

### Method 1: Interactive Test Client (Recommended)
The easiest way to test customer interactions:

```bash
python test_customer_interaction.py
```

**Features:**
- ✅ Automatic authentication
- ✅ Pre-built test scenarios
- ✅ Interactive conversation flow
- ✅ Real-time agent responses
- ✅ Follow-up message support

### Method 2: Direct API Testing with cURL

#### Step 1: Get Authentication Token
```bash
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=johndoe&password=secret"
```

Example response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Step 2: Start a Conversation
```bash
curl -X POST "http://localhost:8000/api/v1/conversations" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST_001",
    "channel": "web",
    "initial_message": "I need help with my account",
    "priority": "medium"
  }'
```

#### Step 3: Send Follow-up Messages
```bash
curl -X POST "http://localhost:8000/api/v1/conversations/CONVERSATION_ID/messages" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "I cant access my billing information"
  }'
```

### Method 3: Python Script Testing
```python
import asyncio
import httpx

async def test_conversation():
    base_url = "http://localhost:8000"
    
    # 1. Authenticate
    async with httpx.AsyncClient() as client:
        auth_response = await client.post(
            f"{base_url}/token",
            data={"username": "johndoe", "password": "secret"}
        )
        token = auth_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Start conversation
        conversation_data = {
            "customer_id": "TEST_001",
            "channel": "web", 
            "initial_message": "Hello, I need technical support",
            "priority": "high"
        }
        
        conv_response = await client.post(
            f"{base_url}/api/v1/conversations",
            json=conversation_data,
            headers=headers
        )
        
        conversation = conv_response.json()
        print(f"Agent Response: {conversation['response']}")
        
        # 3. Send follow-up
        message_data = {"content": "My internet keeps disconnecting"}
        
        msg_response = await client.post(
            f"{base_url}/api/v1/conversations/{conversation['conversation_id']}/messages",
            json=message_data,
            headers=headers
        )
        
        message = msg_response.json()
        print(f"Agent Response: {message['content']}")

# Run the test
asyncio.run(test_conversation())
```

## 🎯 Test Scenarios

### Scenario 1: General Support (Tier 1)
**Initial Message:** "What are your business hours?"
**Expected:** 
- Routed to Tier 1 Support Agent
- Quick FAQ-style response
- High confidence score (>0.8)

### Scenario 2: Technical Issue (Tier 2)
**Initial Message:** "My internet connection keeps dropping every few minutes"
**Expected:**
- Routed to Technical Support Agent
- Request for diagnostic information
- Offer troubleshooting steps

**Follow-up:** "I've already restarted my router twice"
**Expected:**
- Advanced diagnostic suggestions
- Possible escalation triggers

### Scenario 3: Billing Question (Billing Agent)
**Initial Message:** "I was charged twice for the same service this month"
**Expected:**
- Routed to Billing Agent
- Request for account verification
- Investigation of duplicate charges

### Scenario 4: Sales Inquiry (Sales Agent)
**Initial Message:** "I'm interested in upgrading to your premium plan"
**Expected:**
- Routed to Sales Agent
- Product information and pricing
- Upselling opportunities

### Scenario 5: Complex Issue (Escalation)
**Initial Message:** "I need to cancel my service immediately due to poor performance"
**Follow-up:** "This is unacceptable, I want to speak to a manager"
**Expected:**
- Escalation to Supervisor Agent
- Higher priority handling
- Retention-focused response

## 🔍 Testing Checklist

### Basic Functionality
- [ ] ✅ Application starts successfully
- [ ] ✅ Health check endpoint responds
- [ ] ✅ Authentication works with test credentials
- [ ] ✅ Can start new conversations
- [ ] ✅ Can send follow-up messages
- [ ] ✅ Receives agent responses

### Agent Routing
- [ ] ✅ Intent classification accuracy
- [ ] ✅ Appropriate agent assignment
- [ ] ✅ Escalation triggers work
- [ ] ✅ Agent handoffs function properly

### Response Quality
- [ ] ✅ Responses are relevant to queries
- [ ] ✅ Response time under 5 seconds
- [ ] ✅ Confidence scores are reasonable
- [ ] ✅ Follow-up suggestions provided

### Error Handling
- [ ] ✅ Invalid authentication handled gracefully
- [ ] ✅ Malformed requests return proper errors
- [ ] ✅ System recovers from agent failures
- [ ] ✅ Timeout scenarios handled

## 🐛 Troubleshooting

### Common Issues

#### 1. "Service is not available"
**Problem:** Cannot connect to the application
**Solution:**
```bash
# Check if application is running
curl http://localhost:8000/health

# Start the application if not running
python -m src.main
```

#### 2. "Authentication failed"
**Problem:** Cannot get access token
**Solution:**
- Verify username/password: `johndoe` / `secret`
- Check token endpoint: `POST /token`
- Ensure Content-Type header is correct

#### 3. "Conversation not found"
**Problem:** Cannot send messages to conversation
**Solution:**
- Verify conversation_id from start_conversation response
- Check if conversation expired
- Ensure proper Authorization header

#### 4. "Agent timeout" or slow responses
**Problem:** Agent takes too long to respond
**Solution:**
- Check application logs for errors
- Verify LangGraph integration status
- Check database connectivity

### Debug Mode
Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python -m src.main
```

## 📊 Performance Testing

### Load Testing with Multiple Conversations
```python
import asyncio
import aiohttp

async def load_test():
    """Test with 10 concurrent conversations"""
    
    async def single_conversation(session, i):
        # Authentication
        auth_data = {"username": "johndoe", "password": "secret"}
        async with session.post("/token", data=auth_data) as resp:
            token = (await resp.json())["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
        
        # Start conversation
        conv_data = {
            "customer_id": f"LOAD_TEST_{i}",
            "channel": "web",
            "initial_message": f"Test message {i}",
            "priority": "medium"
        }
        
        async with session.post("/api/v1/conversations", 
                               json=conv_data, 
                               headers=headers) as resp:
            result = await resp.json()
            print(f"Conversation {i}: {result.get('response', 'No response')}")
    
    async with aiohttp.ClientSession() as session:
        tasks = [single_conversation(session, i) for i in range(10)]
        await asyncio.gather(*tasks)

# Run load test
asyncio.run(load_test())
```

## 📈 Monitoring Test Results

### Key Metrics to Monitor
- **Response Time:** Should be < 5 seconds
- **Accuracy:** Intent classification > 85%
- **Escalation Rate:** < 20% for simple queries
- **Error Rate:** < 1% of requests

### View Application Metrics
```bash
# Check metrics endpoint
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/metrics
```

## 🎯 Advanced Testing

### Custom Test Scenarios
Create your own test scenarios by modifying `test_customer_interaction.py`:

```python
custom_scenarios = [
    {
        "name": "Complex Technical Issue",
        "initial_message": "My VPN connection fails when connecting from certain locations",
        "follow_ups": [
            "It works fine from home but not from my office",
            "I'm using Windows 11 with the latest updates",
            "The error code is 800-something"
        ]
    }
]
```

### A/B Testing Different Prompts
Test different ways of asking the same question:
- "I need help with billing" vs "I have a question about my invoice"
- "My internet is slow" vs "Network performance issues"

## 📝 Reporting Issues

When reporting issues, please include:
1. **Test scenario** being executed
2. **Expected behavior** vs **actual behavior**
3. **Error messages** or logs
4. **Steps to reproduce**
5. **Environment details** (OS, Python version, etc.)

## 🚀 Next Steps

After basic testing works:
1. **Test WebSocket connections** for real-time updates
2. **Test file attachments** in conversations
3. **Test conversation history** retrieval
4. **Test multi-channel** scenarios
5. **Test production deployment** with Docker

---

**Happy Testing! 🎉**

For additional support, check the application logs or create an issue in the project repository.