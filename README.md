# Mavvrik SDK Assistant

**AI-powered multi-agent system to help Mavvrik development teams instrument AI agents using various frameworks and MVK SDK**

---

## 🎯 Quick Overview

**Problem:** Developers spend 30+ minutes searching scattered documentation (MVK SDK + 9+ framework docs) to integrate agents.

**Solution:** Intelligent multi-agent assistant that:
- ✅ Answers MVK SDK questions instantly (ChromaDB RAG)
- ✅ Provides framework-specific guidance (Tavily web search)
- ✅ Generates working code examples
- ✅ Tracks all interactions via MVK SDK (dogfooding)
- ✅ Learns from feedback (👍 / 👎)

**Time Saved:** 30 min → 2 min per integration question

---

## 🚀 Quick Start

### Prerequisites
- Docker + Docker Compose
- OpenAI API key ([get here](https://platform.openai.com/api-keys))
- Tavily API key ([get here](https://app.tavily.com))
- MVK SDK documentation PDF

### Setup (2 minutes)

```bash
# 1. Clone repository
git clone https://github.com/dineshdm1/mavvrik-sdk-assistant.git
cd mavvrik-sdk-assistant

# 2. Create .env file
cp .env.example .env
# Edit .env and add your API keys

# 3. Place PDF documentation
cp /path/to/mvk_sdk_docs.pdf docs/mvk_sdk_documentation.pdf

# 4. Start
docker-compose up

# ✅ Access at: http://localhost:8000
```

That's it! The system will:
- ✅ Auto-index your PDF (~2-3 minutes first time)
- ✅ Start Chainlit UI on port 8000
- ✅ Be ready for questions

---

## 🔐 Authentication

When you first access the application:

1. **Enter username**: This becomes your `user_id`
2. **Enter password**: `mavvrik@123` (common for everyone)
3. **Start asking questions!**

---

## 🤖 System Architecture

```
User (Browser) → http://localhost:8000
    ↓
Chainlit UI (Authentication + Chat)
    ↓
Chat Orchestrator Agent (Routes based on intent)
    ↓
├─→ SDK Agent (ChromaDB + PDF RAG)
├─→ Framework Router
│   ├─→ LangChain Specialist (Tavily)
│   ├─→ LlamaIndex Specialist (Tavily)
│   └─→ Generic Framework (Tavily)
└─→ Code Generator (Synthesizes SDK + Framework)
    ↓
Response with code examples + explanations
    ↓
User provides feedback (👍 / 👎)
    ↓
MVK Dashboard (all interactions tracked)
```

**Key Technologies:**
- **UI:** Chainlit
- **LLM:** OpenAI GPT-4o-mini
- **Vector DB:** ChromaDB (self-hosted)
- **Web Search:** Tavily API
- **Framework:** LangChain
- **Tracking:** MVK SDK (dogfooding)
- **Deployment:** Docker + Docker Compose

---

## 💡 Example Interactions

### Example 1: Simple SDK Question
```
You: "What does mvk.signal() do?"

Assistant (SDK Agent):
📚 Searching MVK SDK documentation...

The @mvk.signal() decorator wraps an entire function to track its total cost,
including retries and failures. Perfect for business-level cost tracking.

Example:
```python
import mvk_sdk as mvk

@mvk.signal(step_type="AGENT", operation="customer_support")
def handle_query(query: str):
    # All operations tracked as one cost boundary
    return process_query(query)
```

Cost tracking: Single span captures entire function execution.
See also: mvk.create_signal() for granular tracking.

👍 Helpful  👎 Not Helpful
```

### Example 2: Framework Integration
```
You: "How do I instrument a LangChain agent with MVK?"

Assistant (Multi-Agent):
🔄 Collaborating with SDK Agent + LangChain Specialist + Code Generator...

Here's a complete working example:

```python
import mvk_sdk as mvk
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain_openai import ChatOpenAI

# 1. Initialize MVK BEFORE imports
mvk.instrument(wrappers={"include": ["genai"]})

# 2. Create agent
llm = ChatOpenAI(model="gpt-4o-mini")
agent = create_openai_functions_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools)

# 3. Execute with context
with mvk.context(user_id="user-123", session_id="session-xyz"):
    result = executor.invoke({"input": "Search for orders"})
```

What's tracked:
✅ LLM calls (auto-tracked)
✅ Business context (user_id, session_id)
✅ Full execution cost

Gotchas:
⚠️ mvk.instrument() MUST be called before OpenAI imports

👍 Helpful  👎 Not Helpful
```

---

## ✨ Features

### Core Capabilities
- **Instant SDK Answers**: ChromaDB RAG searches 10,000+ documentation chunks in <2 seconds
- **Framework Guidance**: Tavily-powered web search for LangChain, LlamaIndex, CrewAI, and more
- **Working Code Examples**: Code Generator synthesizes SDK + framework patterns
- **Session Management**: Tracks user_id, session_id (entire journey), conversation_id (individual queries)
- **Feedback Learning**: Thumbs up/down mechanism to improve response quality

### MVK SDK Tracking Hierarchy

All interactions tracked in Mavvrik Dashboard:
```
User Journey (session_id: "session_abc123")
├─ Query 1 (conversation_id: "conv_001")
│  ├─ agent.chat_orchestrator
│  ├─ agent.sdk_agent
│  │  ├─ tool.chromadb_search
│  │  └─ tool.llm_generation
│  └─ feedback.helpful (metric)
├─ Query 2 (conversation_id: "conv_002")
│  ├─ agent.chat_orchestrator
│  ├─ agent.framework_specialist.langchain
│  │  ├─ tool.tavily_search
│  │  └─ tool.llm_synthesis
│  └─ feedback.not_helpful (metric)
```

**Important:**
- `session_id`: One per user login → tracks entire session until logout
- `conversation_id`: One per question/query → tracks individual Q&A

---

## 🔧 Configuration

### Required Environment Variables
```bash
# OpenAI API (required)
OPENAI_API_KEY=sk-...

# Tavily API (required)
TAVILY_API_KEY=tvly-...

# MVK SDK (required for tracking)
MVK_API_KEY=mvk_...
MVK_AGENT_ID=mavvrik-sdk-assistant
MVK_TENANT_ID=mavvrik-internal
```

### Optional Configuration
```bash
# LLM Model
LLM_MODEL=gpt-4o-mini  # Default

# ChromaDB Settings
CHROMA_COLLECTION=mvk_sdk_docs
CHROMA_PERSIST_DIR=./chroma/data

# Chainlit
CHAINLIT_PORT=8000
CHAINLIT_SESSION_TIMEOUT=120  # Session timeout in seconds (default: 120)
CHAINLIT_WEBSOCKET_TIMEOUT=90  # WebSocket timeout in seconds (default: 90)

# Authentication
AUTH_PASSWORD=mavvrik@123  # Default password
```

### Performance Tuning
```bash
# For queries taking longer than 2 minutes, increase these timeouts:
CHAINLIT_SESSION_TIMEOUT=180   # 3 minutes
CHAINLIT_WEBSOCKET_TIMEOUT=150 # 2.5 minutes
```

---

## 📊 Performance

- **Simple SDK Questions**: <10 seconds
- **Code Generation**: <30 seconds
- **ChromaDB Query**: <2 seconds
- **Tavily Search**: <5 seconds
- **Concurrent Users**: 5-6 supported
- **PDF Indexing**: ~2-3 minutes (first time only)

---

## 🐛 Troubleshooting

### Common Issues

**Container won't start**
```bash
# Check API keys are set
docker-compose config

# View logs
docker-compose logs -f
```

**PDF not indexed**
```bash
# Verify PDF exists
ls -lh docs/mvk_sdk_documentation.pdf

# Trigger re-indexing
docker-compose down -v  # Delete ChromaDB volume
docker-compose up
```

**ChromaDB errors**
```bash
# Reset ChromaDB
docker-compose down -v
docker-compose up --build
```

**Authentication issues**
- Default password is `mavvrik@123`
- Set custom password in `.env` with `AUTH_PASSWORD=your-password`

**Session timeout / Re-authentication prompt during long queries**
```bash
# If you see "Please authenticate" after asking complex questions:
# Increase timeout values in .env file

CHAINLIT_SESSION_TIMEOUT=180      # Increase to 3 minutes
CHAINLIT_WEBSOCKET_TIMEOUT=150    # Increase to 2.5 minutes

# Then restart:
docker-compose restart
```

**Why does this happen?**
- Complex queries (e.g., LlamaIndex with embeddings) can take 45-60 seconds
- Default session timeout is 120 seconds (2 minutes)
- If query processing exceeds timeout, UI disconnects
- Backend still completes the work (visible in MVK telemetry)
- Solution: Increase timeout or optimize query complexity

---

## 📈 Success Metrics

### Tracked in MVK Dashboard
- Daily active users (unique user_ids)
- Queries per day
- Agent routing distribution
- Average response time
- Cost per query
- Feedback score (% positive)

### Expected Impact
- **Time Saved**: 30 min → 2 min per integration question (93% reduction)
- **Team Adoption**: 80%+ weekly usage within first month
- **Slack Questions**: 50% reduction in repetitive SDK questions

---

## 🏗️ Project Structure

```
mavvrik-sdk-assistant/
├── docker-compose.yml          # Docker Compose configuration
├── Dockerfile                  # Docker image definition
├── entrypoint.sh              # Startup script
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── docs/                     # Documentation folder
│   └── mvk_sdk_documentation.pdf  # Place your PDF here
├── src/                      # Source code
│   ├── app.py               # Main Chainlit application
│   ├── init.py              # Initialization script
│   ├── agents/              # Agent implementations
│   │   ├── orchestrator.py      # Chat orchestrator
│   │   ├── sdk_agent.py         # SDK RAG agent
│   │   ├── framework_router.py  # Framework specialists
│   │   └── code_generator.py    # Code generation
│   ├── tools/               # Tool implementations
│   │   ├── chromadb_manager.py  # Vector DB management
│   │   ├── tavily_search.py     # Web search
│   │   └── pdf_ingestion.py     # PDF processing
│   ├── utils/               # Utilities
│   │   ├── config.py            # Configuration
│   │   ├── mvk_tracker.py       # MVK SDK wrapper
│   │   └── session_manager.py   # Session management
│   └── prompts/             # LLM prompts
│       └── prompts.py
└── chroma/                  # ChromaDB data (Docker volume)
```

---

## 📝 License

Internal Mavvrik project - not licensed for external use.

---

## 👥 Team

**Target Users**: 5-6 Mavvrik internal developers
**Repository**: https://github.com/dineshdm1/mavvrik-sdk-assistant
**Contact**: [Your Slack Channel]

---

## 🎉 Getting Started

1. Clone the repository
2. Add API keys to `.env`
3. Place PDF documentation in `docs/`
4. Run `docker-compose up`
5. Visit http://localhost:8000
6. Login with username and password `mavvrik@123`
7. Start asking questions!

**Happy integrating!** 🚀
