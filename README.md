# Contact Center Agentic Flow System

An intelligent, multi-agent contact center system built with LangGraph and Vertex AI that provides automated customer support through specialized AI agents.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python -m src.database.init_db

# Run the application
python -m src.main
```

## 🧪 Testing the Application

### Method 1: Interactive Test Client (Recommended)

The easiest way to test customer interactions:
```bash
python test_customer_interaction.py
```

This provides:
- ✅ Automatic authentication
- ✅ Pre-built test scenarios
- ✅ Interactive conversation flow
- ✅ Real-time agent responses

### Method 2: Manual API Testing

#### 1. Start the Application
```bash
python -m src.main
# Application will run on http://localhost:8000
```

#### 2. Get Authentication Token
```bash
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=johndoe&password=secret"
```

#### 3. Start a Conversation
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

#### 4. Send Follow-up Messages
```bash
curl -X POST "http://localhost:8000/api/v1/conversations/CONVERSATION_ID/messages" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "I cant access my billing information"
  }'
```

### Test Credentials
- **Username:** `johndoe`
- **Password:** `secret`

### Test Scenarios

Try these conversation starters to test different agent types:

1. **General Support:** "What are your business hours?"
2. **Technical Issues:** "My internet connection is very slow"
3. **Billing Questions:** "I was charged twice for the same service"
4. **Sales Inquiries:** "I'm interested in upgrading to premium"

## 🏗️ Architecture

- **LangGraph Orchestration**: Multi-agent workflow management
- **Vertex AI Integration**: Gemini Pro, Claude 3, and custom models
- **FastAPI Backend**: RESTful API with WebSocket support
- **PostgreSQL**: State management and analytics
- **Redis**: Caching and session management

## 📋 Features

- ⚡ Sub-30 second response times
- 🤖 6 specialized AI agents (Tier 1-3, Sales, Billing, Supervisor)
- 🔄 Intelligent routing and escalation
- 📊 Real-time monitoring and analytics
- 🛡️ Enterprise security and compliance
- 🌐 Multi-channel support (Web, Voice, Email, Mobile, Social)

## 🧪 Available Test Endpoints

- `GET /health` - Application health check
- `POST /token` - Get authentication token
- `POST /api/v1/conversations` - Start new conversation
- `POST /api/v1/conversations/{id}/messages` - Send message
- `GET /api/v1/conversations/{id}/state` - Get conversation state

## 📊 Monitoring

Check application status:
```bash
curl http://localhost:8000/health
```

Check system metrics (requires authentication):
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/metrics
```

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use**: The application runs on port 8000 by default. You mentioned it's listening on port 6379 - this might be a Redis instance.

2. **Authentication errors**: Make sure to use the correct credentials (`johndoe`/`secret`)

3. **Database connection**: Run `python test_startup.py` to verify all components are working

### Debug Mode
```bash
export LOG_LEVEL=DEBUG
python -m src.main
```

## 📚 Documentation

For detailed testing instructions, see [TESTING_GUIDE.md](TESTING_GUIDE.md)

## 🚀 Production Deployment

See [deployment guide](docs/deployment.md) for production setup instructions.

---

**Ready to test!** 🎉 Run `python test_customer_interaction.py` to start your first conversation with the AI agents.
