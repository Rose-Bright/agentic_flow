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

## 🧪 Testing

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests  
pytest tests/integration/

# Run load tests
pytest tests/load/
```

## 📚 Documentation

- [API Documentation](docs/api.md)
- [Agent Architecture](docs/agents.md)
- [Deployment Guide](docs/deployment.md)
- [Configuration Reference](docs/configuration.md)

## 🚀 Deployment

See [deployment guide](docs/deployment.md) for production setup instructions.