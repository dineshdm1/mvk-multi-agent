# MVK SDK Assistant - Architecture Documentation

## Overview

The MVK SDK Assistant is a multi-agent AI system designed to help developers integrate the MVK SDK into their applications across various AI frameworks (LangChain, LlamaIndex, CrewAI, etc.). The system uses a hierarchical agent architecture with comprehensive observability through MVK SDK instrumentation.

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           MVK SDK Assistant                                      │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────┐    │
│  │                        Chainlit Web Interface                           │    │
│  │                    (Authentication + Chat UI)                           │    │
│  └────────────────────────────────────────────────────────────────────────┘    │
│                                    │                                            │
│                                    ▼                                            │
│  ┌────────────────────────────────────────────────────────────────────────┐    │
│  │                         app.py (Request Handler)                        │    │
│  │  • Session Management                                                   │    │
│  │  • Authentication                                                       │    │
│  │  • MVK Context Setting (user_id, session_id, tenant_id)               │    │
│  │  • Conversation ID Generation                                          │    │
│  └────────────────────────────────────────────────────────────────────────┘    │
│                                    │                                            │
│                                    ▼                                            │
│  ┌────────────────────────────────────────────────────────────────────────┐    │
│  │                    Chat Orchestrator (Main Agent)                       │    │
│  │                                                                         │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │    │
│  │  │ Stage 1: Intent Classification                                  │  │    │
│  │  │  • Analyze user query                                           │  │    │
│  │  │  • Determine needed agents (SDK, Framework, Code Gen)          │  │    │
│  │  │  • LLM: GPT-4o-mini                                            │  │    │
│  │  └─────────────────────────────────────────────────────────────────┘  │    │
│  │                               │                                         │    │
│  │                               ▼                                         │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │    │
│  │  │ Stage 2: Agent Routing                                          │  │    │
│  │  │  • Route to appropriate specialist agents                       │  │    │
│  │  │  • Execute agents in parallel/sequence                          │  │    │
│  │  │  • Collect responses                                            │  │    │
│  │  └─────────────────────────────────────────────────────────────────┘  │    │
│  │                               │                                         │    │
│  │                               ▼                                         │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │    │
│  │  │ Stage 3: Response Synthesis                                     │  │    │
│  │  │  • Combine multi-agent responses                                │  │    │
│  │  │  • Format final answer                                          │  │    │
│  │  │  • Return to user                                               │  │    │
│  │  └─────────────────────────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────────────────────────┘    │
│                                    │                                            │
│              ┌─────────────────────┼─────────────────────┐                     │
│              ▼                     ▼                     ▼                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐            │
│  │   SDK Agent      │  │ Framework Router │  │ Code Generator   │            │
│  │                  │  │                  │  │                  │            │
│  │ • RAG Search     │  │ • Route by FW    │  │ • Generate Code  │            │
│  │ • ChromaDB       │  │ • 6 Specialists  │  │ • Explain        │            │
│  │ • Embeddings     │  │ • Web Search     │  │ • Cost Estimate  │            │
│  │ • Synthesis      │  │ • Synthesis      │  │ • Gotchas        │            │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘            │
│          │                      │                      │                       │
│          ▼                      ▼                      ▼                       │
│  ┌──────────────────────────────────────────────────────────────┐             │
│  │                    External Services                          │             │
│  │  • OpenAI (GPT-4o-mini, text-embedding-3-small)             │             │
│  │  • ChromaDB (Vector Store - mvk_sdk_docs)                   │             │
│  │  • Tavily (Web Search API)                                   │             │
│  └──────────────────────────────────────────────────────────────┘             │
│                                    │                                            │
│                                    ▼                                            │
│  ┌────────────────────────────────────────────────────────────────────────┐    │
│  │                    MVK SDK Observability Layer                          │    │
│  │  • Auto-tracking (LLM, VectorDB, Embeddings)                           │    │
│  │  • Manual tracking (Tavily, Custom Metrics)                            │    │
│  │  • Context propagation (user, session, tenant, conversation)           │    │
│  │  • Span hierarchy (agents → stages → operations)                       │    │
│  └────────────────────────────────────────────────────────────────────────┘    │
│                                    │                                            │
│                                    ▼                                            │
│  ┌────────────────────────────────────────────────────────────────────────┐    │
│  │                      MVK Dashboard (External)                           │    │
│  │  • Cost Analytics                                                       │    │
│  │  • Performance Monitoring                                               │    │
│  │  • User Attribution                                                     │    │
│  │  • Trace Visualization                                                  │    │
│  └────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Agent Architecture Diagram

```
                         ┌─────────────────────────────────────┐
                         │   Chat Orchestrator (Main Agent)   │
                         │                                     │
                         │  @mvk.signal(operation="orchestrate")│
                         │  step_type="RETRIEVER"              │
                         └─────────────────────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    ▼                   ▼                   ▼
        ┌────────────────────┐ ┌────────────────┐ ┌────────────────────┐
        │    SDK Agent       │ │ Framework      │ │  Code Generator    │
        │                    │ │ Router         │ │                    │
        │ @mvk.signal(       │ │                │ │ @mvk.signal(       │
        │  operation=        │ │ @mvk.signal(   │ │  operation=        │
        │  "rag_search")     │ │  operation=    │ │  "code_generation")│
        │                    │ │  "framework    │ │                    │
        │ step_type=         │ │  _search")     │ │ step_type="LLM"    │
        │  "RETRIEVER"       │ │                │ │                    │
        └────────────────────┘ │ step_type=     │ └────────────────────┘
                │              │  "RETRIEVER"   │          │
                │              └────────────────┘          │
                │                      │                   │
                ▼                      ▼                   ▼
        ┌──────────────┐      ┌──────────────┐    ┌──────────────┐
        │              │      │              │    │              │
        │  Stages:     │      │  Stages:     │    │  Stages:     │
        │              │      │              │    │              │
        │  1. Retrieval│      │  1. Web      │    │  1. Generation│
        │     ├─ChromaDB│     │     Search   │    │     └─LLM     │
        │     │  Count  │     │     └─Tavily │    │              │
        │     ├─Embedding│     │              │    │  2. Parsing  │
        │     └─Query   │     │  2. Synthesis│    │     └─Format  │
        │              │      │     └─LLM    │    │              │
        │  2. Synthesis│      │              │    │              │
        │     └─LLM    │      │              │    │              │
        │              │      │              │    │              │
        └──────────────┘      └──────────────┘    └──────────────┘
                │                      │                   │
                └──────────────────────┴───────────────────┘
                                       │
                                       ▼
                         ┌─────────────────────────┐
                         │  Framework Specialists │
                         │                         │
                         │  • LangChain Specialist│
                         │  • LlamaIndex Specialist│
                         │  • CrewAI Specialist   │
                         │  • AutoGen Specialist  │
                         │  • Haystack Specialist │
                         │  • Generic Specialist  │
                         └─────────────────────────┘
```

---

## Instrumentation Architecture

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                        MVK SDK Instrumentation Layers                         │
└───────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│ Layer 1: Global Instrumentation Setup (orchestrator.__init__)                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  mvk.instrument(                                                                │
│      wrappers={"include": ["genai", "vectordb"]},  # Auto-track LLM + VectorDB │
│      batching={"max_interval_ms": 60000}           # Batch every 60 seconds    │
│  )                                                                              │
│                                                                                  │
│  ✅ Enables automatic tracking of:                                             │
│     • All OpenAI LLM calls                                                      │
│     • All OpenAI embedding calls                                                │
│     • All ChromaDB vector operations                                            │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Layer 2: Business Context Setting (app.py - per request)                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  with mvk.context(                                                              │
│      user_id="dinesh",                    # Who made the request                │
│      session_id="session_abc123",         # Which login session                 │
│      tenant_id="p6v6yenh2o_ii7tv"        # Which organization                  │
│  ):                                                                             │
│      with mvk.context(conversation_id="conv_001"):  # Which Q&A pair           │
│          # All nested operations inherit this context                           │
│          result = chat_orchestrator.process_query(query)                       │
│                                                                                  │
│  ✅ Sets business context for attribution:                                     │
│     • User-level cost tracking                                                  │
│     • Session-level analytics                                                   │
│     • Tenant-level billing                                                      │
│     • Conversation-level debugging                                              │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Layer 3: Agent-Level Tracking (agents - @mvk.signal decorator)                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  @mvk.signal(step_type="AGENT", operation="orchestrate")                       │
│  def process_query(self, query: str):                                          │
│      # Agent span created automatically                                         │
│      # Inherits all parent context (user, session, tenant, conversation)       │
│                                                                                  │
│  @mvk.signal(step_type="AGENT", operation="rag_search")                        │
│  def query(self, question: str):                                               │
│      # SDK Agent span created                                                   │
│                                                                                  │
│  @mvk.signal(step_type="AGENT", operation="code_generation")                   │
│  def generate(self, context: dict):                                            │
│      # Code Generator span created                                              │
│                                                                                  │
│  ✅ Creates agent-level spans with:                                            │
│     • Agent identification (via function name)                                  │
│     • Step type classification                                                  │
│     • Operation categorization                                                  │
│     • Automatic parent-child relationships                                      │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Layer 4: Stage-Level Tracking (agents - mvk.context for stages)                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  # In orchestrator.py                                                           │
│  with mvk.context(name="stage.intent_classification"):                         │
│      intent = self._classify_intent(query)  # LLM call auto-tracked           │
│                                                                                  │
│  with mvk.context(name="stage.agent_routing"):                                 │
│      responses = self._route_to_agents(query, intent)                          │
│                                                                                  │
│  # In sdk_agent.py                                                              │
│  with mvk.context(name="stage.retrieval"):                                     │
│      docs = chromadb_manager.search(question, k=5)  # VectorDB auto-tracked   │
│                                                                                  │
│  with mvk.context(name="stage.synthesis"):                                     │
│      answer = llm.invoke(prompt)  # LLM call auto-tracked                     │
│                                                                                  │
│  ✅ Creates stage-level context for:                                           │
│     • Granular performance analysis                                             │
│     • Stage-specific cost attribution                                           │
│     • Detailed trace visualization                                              │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Layer 5: Tool-Level Tracking (manual for non-wrapped tools)                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  # In framework_router.py for Tavily search                                     │
│  with mvk.context(name="stage.web_search"):                                    │
│      with mvk.create_signal(                                                    │
│          name="tool.tavily_search",                                             │
│          step_type="TOOL",                                                      │
│          operation="web_search"                                                 │
│      ):                                                                         │
│          # Call pure utility tool                                               │
│          results = tavily_search.search_framework(...)                          │
│                                                                                  │
│          # Add custom metrics                                                   │
│          mvk.add_metered_usage([                                                │
│              Metric(                                                            │
│                  metric_kind="tavily.search",                                   │
│                  quantity=1,                                                    │
│                  uom="search"                                                   │
│              ).to_dict() | {                                                    │
│                  "metadata": {                                                  │
│                      "estimated_cost": 0.001,                                   │
│                      "currency": "USD",                                         │
│                      "provider": "tavily",                                      │
│                      "framework": self.framework_name,                          │
│                      "results_returned": len(results)                           │
│                  }                                                              │
│              }                                                                  │
│          ])                                                                     │
│                                                                                  │
│  ✅ Manually tracks tools not covered by auto-wrappers:                        │
│     • Third-party API calls (Tavily)                                            │
│     • Custom tools                                                              │
│     • Business metrics                                                          │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ Layer 6: Automatic Operation Tracking (via wrappers)                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Auto-tracked operations (no code needed):                                      │
│                                                                                  │
│  📊 LLM Calls (genai wrapper):                                                 │
│     • openai.chat.completion                                                    │
│       ├─ model: gpt-4o-mini-2024-07-18                                         │
│       ├─ prompt_tokens: 257                                                     │
│       ├─ completion_tokens: 30                                                  │
│       ├─ total_tokens: 287                                                      │
│       └─ cost: $0.00006                                                         │
│                                                                                  │
│  📊 Embedding Calls (genai wrapper):                                           │
│     • openai.embeddings.create                                                  │
│       ├─ model: text-embedding-3-small                                         │
│       ├─ tokens: 14                                                             │
│       ├─ dimensions: 1536                                                       │
│       └─ cost: $0.00                                                            │
│                                                                                  │
│  📊 VectorDB Operations (vectordb wrapper):                                    │
│     • chromadb.count                                                            │
│       └─ results: 55 vectors                                                    │
│     • chromadb.query                                                            │
│       ├─ query_limit: 5                                                         │
│       ├─ results: 5 vectors                                                     │
│       └─ duration: 9ms                                                          │
│                                                                                  │
│  ✅ All inherit context from parent spans:                                     │
│     • user_id, session_id, tenant_id, conversation_id                          │
│     • agent_name, stage name                                                    │
│     • Proper parent-child relationships                                         │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Context Propagation Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        Context Inheritance Hierarchy                             │
└─────────────────────────────────────────────────────────────────────────────────┘

app.py (Request Layer)
│
├─ mvk.context(user_id="dinesh", session_id="session_abc", tenant_id="...")
│  │
│  └─ mvk.context(conversation_id="conv_001")
│     │
│     └─ orchestrator.process_query()  ← @mvk.signal()
│        │
│        │ INHERITS: user_id, session_id, tenant_id, conversation_id ✅
│        │
│        ├─ mvk.context(name="stage.intent_classification")
│        │  │
│        │  └─ llm.invoke()  ← auto-tracked
│        │     INHERITS: ALL above + name="stage.intent_classification" ✅
│        │
│        └─ mvk.context(name="stage.agent_routing")
│           │
│           ├─ sdk_agent.query()  ← @mvk.signal()
│           │  │
│           │  │ INHERITS: ALL from parent ✅
│           │  │
│           │  ├─ mvk.context(name="stage.retrieval")
│           │  │  │
│           │  │  ├─ chromadb.count()  ← auto-tracked
│           │  │  │  INHERITS: ALL + name="stage.retrieval" ✅
│           │  │  │
│           │  │  ├─ openai.embeddings.create()  ← auto-tracked
│           │  │  │  INHERITS: ALL + name="stage.retrieval" ✅
│           │  │  │
│           │  │  └─ chromadb.query()  ← auto-tracked
│           │  │     INHERITS: ALL + name="stage.retrieval" ✅
│           │  │
│           │  └─ mvk.context(name="stage.synthesis")
│           │     │
│           │     └─ llm.invoke()  ← auto-tracked
│           │        INHERITS: ALL + name="stage.synthesis" ✅
│           │
│           ├─ framework_router.query()  ← @mvk.signal()
│           │  │
│           │  │ INHERITS: ALL from parent ✅
│           │  │
│           │  ├─ mvk.context(name="stage.web_search")
│           │  │  │
│           │  │  └─ mvk.create_signal("tool.tavily_search")  ← manual
│           │  │     INHERITS: ALL + name="stage.web_search" ✅
│           │  │
│           │  └─ mvk.context(name="stage.synthesis")
│           │     │
│           │     └─ llm.invoke()  ← auto-tracked
│           │        INHERITS: ALL + name="stage.synthesis" ✅
│           │
│           └─ code_generator.generate()  ← @mvk.signal()
│              │
│              │ INHERITS: ALL from parent ✅
│              │
│              └─ mvk.context(name="stage.generation")
│                 │
│                 └─ llm.invoke()  ← auto-tracked
│                    INHERITS: ALL + name="stage.generation" ✅

KEY:
✅ = Context automatically inherited via MVK SDK thread-local storage
← = Tracking method (auto-tracked via wrappers or manual via @mvk.signal)
```

---

## Component Details

### 1. **Chat Orchestrator**
- **File**: `src/agents/orchestrator.py`
- **Purpose**: Main routing and coordination agent
- **Responsibilities**:
  - Initialize MVK SDK instrumentation
  - Classify user intent
  - Route to specialist agents
  - Synthesize multi-agent responses
- **Instrumentation**: `@mvk.signal(step_type="AGENT", operation="orchestrate")`

### 2. **SDK Agent**
- **File**: `src/agents/sdk_agent.py`
- **Purpose**: RAG-based MVK SDK documentation specialist
- **Responsibilities**:
  - Semantic search in ChromaDB
  - Retrieve relevant documentation
  - Synthesize answers using LLM
- **Instrumentation**: `@mvk.signal(step_type="AGENT", operation="rag_search")`
- **Tools**: ChromaDB, OpenAI Embeddings, OpenAI Chat

### 3. **Framework Router**
- **File**: `src/agents/framework_router.py`
- **Purpose**: Route queries to framework-specific specialists
- **Supported Frameworks**:
  - LangChain
  - LlamaIndex
  - CrewAI
  - AutoGen
  - Haystack
  - Generic (fallback)
- **Instrumentation**: `@mvk.signal(step_type="AGENT", operation="framework_search")`
- **Tools**: Tavily Web Search, OpenAI Chat

### 4. **Code Generator**
- **File**: `src/agents/code_generator.py`
- **Purpose**: Generate working code examples
- **Responsibilities**:
  - Generate integration code
  - Provide explanations
  - Estimate costs
  - Identify gotchas
- **Instrumentation**: `@mvk.signal(step_type="AGENT", operation="code_generation")`
- **Tools**: OpenAI Chat

---

## Data Flow

### Request Flow
```
1. User Authentication
   └─ Username/Password → Session Created → session_id generated

2. User Query
   └─ Query Text → app.py → conversation_id generated

3. Context Setup
   └─ mvk.context(user_id, session_id, tenant_id, conversation_id)

4. Orchestrator Processing
   ├─ Stage 1: Intent Classification (LLM)
   ├─ Stage 2: Agent Routing
   │  ├─ SDK Agent (if SDK question)
   │  ├─ Framework Router (if framework question)
   │  └─ Code Generator (if code needed)
   └─ Stage 3: Response Synthesis

5. Response Delivery
   └─ Formatted Answer → User

6. Feedback Collection
   └─ 👍/👎 → Tracked with conversation_id
```

### Data Storage
```
ChromaDB (Vector Store):
├─ Collection: mvk_sdk_docs
├─ Documents: 55 chunks
├─ Embeddings: text-embedding-3-small (1536 dims)
└─ Persistence: /app/chroma/data

Session Manager (In-Memory):
├─ User Sessions
├─ Conversation History
└─ Feedback Records

MVK Dashboard (External):
├─ Traces (by traceId)
├─ Spans (nested hierarchy)
├─ Metrics (tokens, costs, durations)
└─ Context (user, session, tenant, conversation)
```

---

## Technology Stack

### Core Technologies
- **Language**: Python 3.11
- **UI Framework**: Chainlit
- **LLM Provider**: OpenAI (GPT-4o-mini)
- **Embeddings**: OpenAI (text-embedding-3-small)
- **Vector Database**: ChromaDB
- **Web Search**: Tavily API
- **Observability**: MVK SDK (v1.2.0)
- **Deployment**: Docker + Docker Compose

### Key Dependencies
```
chainlit==1.0.0
openai==2.8.1
langchain-openai==0.0.5
langchain-community==0.0.13
langchain-core==0.1.16
chromadb==0.4.22
tavily-python==0.3.0
mvk-sdk-py==1.2.0
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────┐
│              Docker Container                        │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │  Chainlit App (Port 8000)                  │    │
│  │  ├─ app.py                                 │    │
│  │  ├─ agents/                                │    │
│  │  ├─ tools/                                 │    │
│  │  └─ utils/                                 │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │  ChromaDB (Persistent Volume)              │    │
│  │  └─ /app/chroma/data                       │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │  Environment Variables                      │    │
│  │  ├─ OPENAI_API_KEY                         │    │
│  │  ├─ TAVILY_API_KEY                         │    │
│  │  ├─ MVK_API_KEY                            │    │
│  │  ├─ MVK_AGENT_ID                           │    │
│  │  ├─ MVK_AGENT_NAME                         │    │
│  │  └─ MVK_TENANT_ID                          │    │
│  └────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
                       │
                       ▼
        ┌─────────────────────────────┐
        │   External Services          │
        │                             │
        │  • OpenAI API               │
        │  • Tavily API               │
        │  • MVK Ingest Service       │
        │    (ingest.mavvrik.ai)      │
        └─────────────────────────────┘
```

---

## Performance Characteristics

### Typical Request Latencies
```
Intent Classification:    1.5-2.0 seconds (LLM)
SDK Agent Query:         10.0-12.0 seconds (RAG + LLM)
Framework Router Query:   7.0-8.0 seconds (Web Search + LLM)
Code Generator:          11.0-14.0 seconds (LLM)
Total End-to-End:        23.0-28.0 seconds
```

### Token Usage (per query)
```
Intent Classification:    287 tokens  (~$0.00006)
SDK Agent:               786 tokens  (~$0.00020)
Framework Specialist:    774 tokens  (~$0.00012)
Code Generator:          923 tokens  (~$0.00035)
Embeddings:               14 tokens  (~$0.00)
Total per Query:      ~1,900 tokens  (~$0.00073)
```

### Resource Usage
```
ChromaDB Collection:     55 documents
Average Query Latency:   5-10ms (vector search)
Embedding Dimensions:    1536
Memory Footprint:        ~500MB (app + ChromaDB)
```

---

## Security Considerations

### Authentication
- Password-based authentication
- Session management via Chainlit
- No persistent storage of credentials

### API Keys
- Stored in environment variables
- Never logged or exposed
- Validated on startup

### Data Privacy
- No user data stored persistently (except ChromaDB docs)
- Session data in-memory only
- Conversation history not persisted

### Network Security
- Container isolation
- Environment-based configuration
- HTTPS recommended for production

---

## Monitoring & Observability

### MVK SDK Tracking
```
Tracked Automatically:
├─ All LLM calls (tokens, costs, latencies)
├─ All embedding calls (tokens, dimensions)
├─ All VectorDB operations (queries, results)
└─ All spans with full context

Tracked Manually:
├─ Tavily web searches (costs, results)
└─ User feedback (helpful/not helpful)

Business Context:
├─ user_id (who made the request)
├─ session_id (which login session)
├─ tenant_id (which organization)
└─ conversation_id (which Q&A pair)
```

### Metrics Available
- Cost per user
- Cost per session
- Cost per conversation
- Latency per agent
- Latency per stage
- Token usage per model
- Error rates
- Feedback scores

---

## Extension Points

### Adding New Agents
1. Create agent file in `src/agents/`
2. Add `@mvk.signal()` decorator
3. Implement stage-level `mvk.context()` calls
4. Register in orchestrator routing logic

### Adding New Framework Specialists
1. Add framework to `FRAMEWORK_PATTERNS` in `framework_router.py`
2. Create specialist class inheriting from base
3. Implement framework-specific search logic
4. No changes needed to instrumentation (auto-inherited)

### Adding New Tools
1. Create pure utility function (no MVK code)
2. Wrap calls in agent with `mvk.create_signal()`
3. Add custom metrics with `mvk.add_metered_usage()`

---

## Troubleshooting

### Common Issues

**Issue**: Missing spans in MVK Dashboard
- **Cause**: `mvk.instrument()` not called
- **Fix**: Check `orchestrator.__init__()` executes

**Issue**: Missing context (user_id, session_id)
- **Cause**: `mvk.context()` not set in app.py
- **Fix**: Verify context setting in `handle_query()`

**Issue**: Spans not nested correctly
- **Cause**: Missing `@mvk.signal()` decorator
- **Fix**: Add decorator to agent functions

**Issue**: ChromaDB not persisting
- **Cause**: Volume mount issue
- **Fix**: Check `docker-compose.yml` volume configuration

---

## Future Enhancements

### Planned Features
1. **Streaming Responses**: Real-time token streaming
2. **Multi-Language Support**: Beyond Python examples
3. **Advanced RAG**: Hybrid search, reranking
4. **Caching**: Response caching for common queries
5. **A/B Testing**: Model/prompt experimentation
6. **Advanced Analytics**: Custom dashboards, reports
7. **Batch Processing**: Multi-query handling
8. **Feedback Loop**: Auto-improvement from user feedback

---

## References

- **MVK SDK Documentation**: Internal docs (55 chunks in ChromaDB)
- **MVK SDK Python**: v1.2.0
- **OpenAI Models**: GPT-4o-mini, text-embedding-3-small
- **Chainlit**: v1.0.0
- **LangChain**: v0.1.x ecosystem

---

**Last Updated**: 2025-11-18  
**Version**: 1.0  
**Authors**: MVK SDK Team
