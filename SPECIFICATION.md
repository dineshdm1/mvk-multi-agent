# MVK SDK Assistant - Technical Specification

## Document Information

- **Version**: 1.0
- **Last Updated**: 2025-11-18
- **Status**: Production
- **Authors**: MVK SDK Team

---

## 1. Executive Summary

### 1.1 Purpose
The MVK SDK Assistant is an AI-powered documentation and code generation system designed to accelerate MVK SDK integration across multiple AI frameworks. It reduces integration time from 30+ minutes to ~2 minutes through intelligent query routing, RAG-based documentation retrieval, and automated code generation.

### 1.2 Key Features
- **Multi-Agent Architecture**: 4 specialized agents working collaboratively
- **Comprehensive Observability**: Full MVK SDK instrumentation for cost tracking and performance monitoring
- **Framework Support**: LangChain, LlamaIndex, CrewAI, AutoGen, Haystack, and generic frameworks
- **RAG-Powered**: ChromaDB vector store with 55 documentation chunks
- **Code Generation**: Context-aware code examples with explanations and cost estimates
- **Real-time Web Search**: Tavily integration for up-to-date framework information

### 1.3 Success Metrics
- **Latency**: 95th percentile < 30 seconds end-to-end
- **Accuracy**: >90% helpful feedback rate
- **Cost**: <$0.001 per query average
- **Availability**: 99.9% uptime target

---

## 2. System Requirements

### 2.1 Runtime Environment
```yaml
Platform: Docker Container
Base Image: python:3.11-slim
Memory: 2GB minimum, 4GB recommended
CPU: 2 cores minimum
Storage: 10GB minimum (for ChromaDB persistence)
Network: Outbound HTTPS (OpenAI, Tavily, MVK endpoints)
```

### 2.2 External Dependencies
```yaml
OpenAI API:
  - Endpoint: api.openai.com
  - Models: gpt-4o-mini-2024-07-18, text-embedding-3-small
  - Rate Limits: Tier-based (check OpenAI dashboard)

Tavily API:
  - Endpoint: api.tavily.com
  - Rate Limits: Plan-dependent

MVK Ingest Service:
  - Endpoint: ingest.mavvrik.ai/v1/traces
  - Protocol: HTTPS
  - Batching: 60-second intervals
```

### 2.3 Environment Variables
```bash
# Required
OPENAI_API_KEY=<your-key>           # OpenAI API key
TAVILY_API_KEY=<your-key>           # Tavily API key
MVK_API_KEY=<your-key>              # MVK SDK API key
MVK_AGENT_ID=<uuid>                 # Unique agent identifier
MVK_AGENT_NAME=mvk-sdk-agent        # Agent display name
MVK_TENANT_ID=<tenant-id>           # Tenant identifier

# Optional
AUTH_PASSWORD=mavvrik@123           # Chainlit auth password
LLM_MODEL=gpt-4o-mini               # LLM model name
CHROMA_COLLECTION=mvk_sdk_docs      # ChromaDB collection name
CHROMA_PERSIST_DIR=/app/chroma/data # ChromaDB storage path
CHAINLIT_PORT=8000                  # Server port
```

---

## 3. Agent Specifications

### 3.1 Chat Orchestrator

#### 3.1.1 Overview
```yaml
File: src/agents/orchestrator.py
Class: ChatOrchestrator
Pattern: Singleton
Initialization: On module import
```

#### 3.1.2 Responsibilities
- Initialize MVK SDK instrumentation
- Classify user intent using LLM
- Route queries to specialist agents
- Synthesize multi-agent responses
- Manage execution flow

#### 3.1.3 Interface
```python
@mvk.signal(step_type="RETRIEVER", operation="orchestrate")
def process_query(
    self, 
    query: str, 
    conversation_history: Optional[str] = None
) -> Dict[str, any]:
    """
    Process user query through multi-agent system.
    
    Args:
        query: User's question/request
        conversation_history: Optional previous conversation context
        
    Returns:
        {
            "answer": str,              # Formatted response
            "sources": List[str],       # Documentation sources
            "intent": Dict,             # Classified intent
            "agents_used": List[str]    # Which agents responded
        }
    """
```

#### 3.1.4 Stages
```yaml
Stage 1 - Intent Classification:
  Context: stage.intent_classification
  Duration: ~1.5s
  LLM: GPT-4o-mini
  Input: User query + prompt
  Output: Intent classification (needs_sdk, needs_framework, needs_code)

Stage 2 - Agent Routing:
  Context: stage.agent_routing
  Duration: Variable (depends on agents)
  Logic: Parallel execution of selected agents
  Agents: sdk_agent, framework_router, code_generator

Stage 3 - Response Synthesis:
  Context: stage.response_synthesis
  Duration: <100ms
  Logic: Combine agent responses with formatting
  Output: Final formatted answer
```

#### 3.1.5 Configuration
```python
LLM_MODEL: str = "gpt-4o-mini"
LLM_TEMPERATURE_INTENT: float = 0.1  # Low temp for consistent intent classification
LLM_TEMPERATURE_SYNTHESIS: float = 0.3
```

---

### 3.2 SDK Agent

#### 3.2.1 Overview
```yaml
File: src/agents/sdk_agent.py
Class: SDKAgent
Pattern: Singleton
Purpose: RAG-based MVK SDK documentation retrieval
```

#### 3.2.2 Responsibilities
- Semantic search in ChromaDB vector store
- Retrieve top-k relevant documentation chunks
- Synthesize answers using LLM with retrieved context
- Track retrieval metrics

#### 3.2.3 Interface
```python
@mvk.signal(step_type="RETRIEVER", operation="rag_search")
def query(self, question: str) -> Dict[str, any]:
    """
    Perform RAG search for SDK documentation.
    
    Args:
        question: User's SDK-related question
        
    Returns:
        {
            "answer": str,          # Synthesized answer
            "sources": List[str],   # Source document pages
            "confidence": float     # 0-1 confidence score
        }
    """
```

#### 3.2.4 Stages
```yaml
Stage 1 - Retrieval:
  Context: stage.retrieval
  Operations:
    1. chromadb.count - Check collection size
    2. openai.embeddings.create - Generate query embedding
    3. chromadb.query - Similarity search (top-5)
  Duration: ~1.0s
  
Stage 2 - Synthesis:
  Context: stage.synthesis
  Operation: openai.chat.completion
  Model: GPT-4o-mini
  Context Window: Retrieved docs + system prompt + user query
  Duration: ~5.0s
  Max Tokens: 500
```

#### 3.2.5 Configuration
```python
CHROMA_COLLECTION: str = "mvk_sdk_docs"
CHROMA_PERSIST_DIR: str = "/app/chroma/data"
EMBEDDING_MODEL: str = "text-embedding-3-small"
EMBEDDING_DIMENSIONS: int = 1536
RETRIEVAL_TOP_K: int = 5
SIMILARITY_THRESHOLD: float = 0.7
LLM_MAX_TOKENS: int = 500
```

#### 3.2.6 Data Model
```python
ChromaDB Document:
  - id: str (unique identifier)
  - content: str (documentation chunk)
  - metadata:
      - source: str (file path)
      - page: int (page number)
      - chunk_index: int (chunk position)
```

---

### 3.3 Framework Router

#### 3.3.1 Overview
```yaml
File: src/agents/framework_router.py
Class: FrameworkRouter
Pattern: Factory (creates framework-specific specialists)
Purpose: Route to framework-specific documentation and examples
```

#### 3.3.2 Supported Frameworks
```yaml
LangChain:
  Pattern: "langchain|lcel|runnable|chain"
  Search Domain: python.langchain.com
  
LlamaIndex:
  Pattern: "llamaindex|llama.index"
  Search Domain: docs.llamaindex.ai
  
CrewAI:
  Pattern: "crewai|crew.ai"
  Search Domain: docs.crewai.com
  
AutoGen:
  Pattern: "autogen"
  Search Domain: microsoft.github.io/autogen
  
Haystack:
  Pattern: "haystack"
  Search Domain: docs.haystack.deepset.ai
  
Generic:
  Pattern: Default (no specific framework)
  Search Domain: General web search
```

#### 3.3.3 Interface
```python
@mvk.signal(step_type="RETRIEVER", operation="framework_search")
def query(self, question: str, framework: str = None) -> Dict[str, any]:
    """
    Search framework-specific documentation.
    
    Args:
        question: User's framework question
        framework: Optional framework name (auto-detected if None)
        
    Returns:
        {
            "answer": str,              # Framework-specific answer
            "sources": List[str],       # Web sources
            "framework": str,           # Detected/used framework
            "search_results_count": int # Number of results found
        }
    """
```

#### 3.3.4 Stages
```yaml
Stage 1 - Web Search:
  Context: stage.web_search
  Tool: tool.tavily_search
  Operation: Tavily API call
  Query Construction: f"{framework} {question} integration with MVK SDK"
  Max Results: 3
  Include Domains: Framework-specific docs
  Duration: ~7.0s
  
Stage 2 - Synthesis:
  Context: stage.synthesis
  Operation: openai.chat.completion
  Model: GPT-4o-mini
  Context: Search results + system prompt + user query
  Duration: ~1.0s
  Max Tokens: 500
```

#### 3.3.5 Configuration
```python
TAVILY_MAX_RESULTS: int = 3
TAVILY_SEARCH_DEPTH: str = "advanced"
LLM_MAX_TOKENS: int = 500
LLM_TEMPERATURE: float = 0.3
```

---

### 3.4 Code Generator

#### 3.4.1 Overview
```yaml
File: src/agents/code_generator.py
Class: CodeGenerator
Pattern: Singleton
Purpose: Generate working code examples with explanations
```

#### 3.4.2 Responsibilities
- Generate complete, executable code examples
- Provide detailed explanations
- Estimate costs
- Identify gotchas and warnings
- Format output with syntax highlighting

#### 3.4.3 Interface
```python
@mvk.signal(step_type="LLM", operation="code_generation")
def generate(self, context: Dict[str, any]) -> Dict[str, any]:
    """
    Generate code example with documentation.
    
    Args:
        context: {
            "query": str,              # User query
            "sdk_info": str,           # SDK agent response
            "framework_info": str,     # Framework specialist response
            "framework": str           # Target framework
        }
        
    Returns:
        {
            "code": str,              # Python code
            "explanation": str,       # What the code does
            "cost_estimate": str,     # Estimated cost per execution
            "gotchas": str,           # Warnings and tips
            "sources": List[str]      # Documentation references
        }
    """
```

#### 3.4.4 Stages
```yaml
Stage 1 - Generation:
  Context: stage.generation
  Operation: openai.chat.completion
  Model: GPT-4o-mini
  Input: SDK context + Framework context + User query
  Duration: ~11.0s
  Max Tokens: 1000
  Temperature: 0.4
  
Stage 2 - Parsing:
  Context: stage.parsing
  Logic: Extract structured sections from LLM response
  Sections: code, explanation, cost_estimate, gotchas
  Duration: <100ms
```

#### 3.4.5 Configuration
```python
LLM_MAX_TOKENS: int = 1000
LLM_TEMPERATURE: float = 0.4
CODE_LANGUAGE: str = "python"
INCLUDE_IMPORTS: bool = True
INCLUDE_COMMENTS: bool = True
```

#### 3.4.6 Output Format
```python
Code Section:
  - Language: Python
  - Style: PEP 8 compliant
  - Imports: Explicit and complete
  - Comments: Inline explanations
  
Explanation Section:
  - Format: Plain text
  - Length: 2-4 sentences
  - Focus: What the code does, not how
  
Cost Estimate Section:
  - Format: "Approximately $X.XX per [query|execution|request]"
  - Based on: Model pricing + estimated token usage
  
Gotchas Section:
  - Format: Bullet points with ⚠️ prefix
  - Content: Common errors, limitations, best practices
```

---

## 4. Tool Specifications

### 4.1 ChromaDB Manager

#### 4.1.1 Overview
```yaml
File: src/tools/chromadb_manager.py
Class: ChromaDBManager
Pattern: Singleton
Purpose: Vector database operations
```

#### 4.1.2 Interface
```python
class ChromaDBManager:
    def search(
        self, 
        query: str, 
        k: int = 5
    ) -> List[Document]:
        """
        Semantic search in vector store.
        
        Args:
            query: Search query text
            k: Number of results to return
            
        Returns:
            List of Document objects with content and metadata
        """
    
    def get_collection_stats(self) -> Dict[str, any]:
        """Get collection statistics."""
        return {
            "count": int,
            "collection_name": str,
            "persist_directory": str
        }
```

#### 4.1.3 Configuration
```python
Collection Name: mvk_sdk_docs
Persist Directory: /app/chroma/data
Embedding Function: OpenAI text-embedding-3-small
Distance Metric: Cosine similarity
```

#### 4.1.4 Data Schema
```python
Document:
  - page_content: str
  - metadata:
      - source: str (file path)
      - page: int (page number)
```

---

### 4.2 Tavily Search

#### 4.2.1 Overview
```yaml
File: src/tools/tavily_search.py
Class: TavilySearch
Pattern: Singleton
Purpose: Web search for framework documentation
```

#### 4.2.2 Interface
```python
class TavilySearch:
    def search_framework(
        self,
        query: str,
        framework: str,
        max_results: int = 3
    ) -> List[Dict[str, str]]:
        """
        Search framework-specific documentation.
        
        Args:
            query: Search query
            framework: Framework name
            max_results: Max results to return
            
        Returns:
            [
                {
                    "title": str,
                    "url": str,
                    "content": str,
                    "score": float
                }
            ]
        """
```

#### 4.2.3 Configuration
```python
Max Results: 3
Search Depth: advanced
Include Domains: Framework-specific (e.g., python.langchain.com)
Timeout: 10 seconds
```

---

## 5. Data Specifications

### 5.1 Request Flow Data

#### 5.1.1 User Session
```python
UserSession:
  - user_id: str (username)
  - session_id: str (format: "session_{uuid4().hex[:16]}")
  - authenticated: bool
  - created_at: datetime
  - conversations: List[Conversation]
```

#### 5.1.2 Conversation
```python
Conversation:
  - conversation_id: str (format: "conv-{timestamp_ms}")
  - user_message: str
  - assistant_message: str
  - feedback: Optional[str] ("helpful" | "not_helpful")
  - created_at: datetime
  - duration_ms: float
  - cost_usd: float
```

#### 5.1.3 Intent Classification
```python
Intent:
  - needs_sdk_help: bool
  - needs_framework_help: bool
  - needs_code_generation: bool
  - framework_detected: Optional[str]
  - confidence: float (0-1)
```

---

### 5.2 MVK SDK Telemetry Data

#### 5.2.1 Span Structure
```python
Span:
  - traceId: str (UUID)
  - spanId: str (hex)
  - parentSpanId: Optional[str]
  - name: str (operation name)
  - kind: int (SPAN_KIND)
  - startTimeUnixNano: str
  - endTimeUnixNano: str
  - status: Dict
  - attributes: List[Attribute]
  - events: List[Event]
  - links: List[Link]
```

#### 5.2.2 Context Attributes
```python
Business Context:
  - mvk.user_id: str
  - mvk.session_id: str
  - mvk.tenant_id: str
  - mvk.name: str (stage name)

Agent Attributes:
  - mvk.agent_id: str
  - mvk.agent_name: str
  - mvk.signal: str (function name)
  - mvk.step_type: str (AGENT|LLM|RETRIEVER|TOOL|EMBEDDING)
  - mvk.operation: str

LLM Attributes:
  - mvk.model_name: str
  - mvk.model_provider: str
  - mvk.prompt_tokens: int
  - mvk.completion_tokens: int
  - mvk.total_tokens: int
  - mvk.duration_ms: float

VectorDB Attributes:
  - mvk.collection_name: str
  - mvk.query_limit: int
  - mvk.results_count: int
  - mvk.duration_ms: float
```

#### 5.2.3 Metrics
```python
Metric:
  - metric_kind: str
  - quantity: int
  - uom: str (unit of measure)
  - metadata: Dict

Common Metrics:
  - token.prompt: {quantity: int, uom: "token"}
  - token.completion: {quantity: int, uom: "token"}
  - token.total: {quantity: int, uom: "token"}
  - embedding.tokens: {quantity: int, uom: "token"}
  - embedding.vectors: {quantity: int, uom: "vector"}
  - vector.retrieved: {quantity: int, uom: "vector"}
  - tavily.search: {quantity: 1, uom: "search"}
  - user.feedback: {quantity: 1|0, uom: "feedback"}
```

---

## 6. API Specifications

### 6.1 Chainlit Callbacks

#### 6.1.1 Authentication
```python
@cl.password_auth_callback
async def auth_callback(username: str, password: str) -> Optional[cl.User]:
    """
    Authenticate user with username/password.
    
    Args:
        username: User identifier
        password: Password (checked against AUTH_PASSWORD env var)
        
    Returns:
        cl.User if authenticated, None otherwise
    """
```

#### 6.1.2 Chat Start
```python
@cl.on_chat_start
async def start():
    """
    Initialize chat session.
    
    Actions:
        - Display welcome message
        - Initialize session variables
    """
```

#### 6.1.3 Message Handler
```python
@cl.on_message
async def main(message: cl.Message):
    """
    Handle user message.
    
    Args:
        message: User's message object
        
    Actions:
        - Extract message content
        - Call handle_query()
        - Display response
        - Provide feedback actions
    """
```

#### 6.1.4 Action Handlers
```python
@cl.action_callback("feedback_helpful")
async def on_feedback_helpful(action: cl.Action):
    """Handle thumbs up feedback."""

@cl.action_callback("feedback_not_helpful")
async def on_feedback_not_helpful(action: cl.Action):
    """Handle thumbs down feedback."""
```

---

### 6.2 Internal APIs

#### 6.2.1 Session Manager
```python
class SessionManager:
    def create_session(self, user_id: str) -> UserSession:
        """Create new user session."""
    
    def get_session(self, session_id: str) -> Optional[UserSession]:
        """Get existing session."""
    
    def add_conversation(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
        conversation_id: str
    ) -> None:
        """Add conversation to session."""
    
    def add_feedback(
        self,
        conversation_id: str,
        feedback_type: str
    ) -> None:
        """Add user feedback to conversation."""
```

---

## 7. Performance Specifications

### 7.1 Latency Targets
```yaml
Intent Classification:
  - P50: < 1.5s
  - P95: < 2.5s
  - P99: < 3.5s

SDK Agent Query:
  - P50: < 10.0s
  - P95: < 12.0s
  - P99: < 15.0s

Framework Router Query:
  - P50: < 7.0s
  - P95: < 9.0s
  - P99: < 12.0s

Code Generator:
  - P50: < 11.0s
  - P95: < 14.0s
  - P99: < 18.0s

End-to-End:
  - P50: < 23.0s
  - P95: < 28.0s
  - P99: < 35.0s
```

### 7.2 Throughput Targets
```yaml
Concurrent Users: 10-50
Queries per Minute: 5-10
ChromaDB Queries per Second: 100+
LLM Tokens per Second: Variable (provider-dependent)
```

### 7.3 Resource Limits
```yaml
Memory:
  - Baseline: 500MB
  - Per User Session: ~10MB
  - ChromaDB: ~200MB
  - Max: 2GB

CPU:
  - Idle: < 5%
  - Per Query: ~50% (1 core)
  - Max: 200% (2 cores)

Disk:
  - ChromaDB: ~100MB
  - Logs: ~50MB/day
  - Total: < 1GB
```

---

## 8. Cost Specifications

### 8.1 Per-Query Costs
```yaml
LLM Costs (GPT-4o-mini):
  - Input: $0.150 / 1M tokens
  - Output: $0.600 / 1M tokens
  
Embedding Costs (text-embedding-3-small):
  - Input: $0.020 / 1M tokens

Tavily Search:
  - $0.001 per search (estimated)

Typical Query Breakdown:
  - Intent Classification: $0.00006
  - SDK Agent: $0.00021
  - Framework Router: $0.00013 (including Tavily)
  - Code Generator: $0.00035
  - Total Average: $0.00075 per query
```

### 8.2 Monthly Cost Estimates
```yaml
100 queries/day (3,000/month):
  - LLM Costs: ~$2.25
  - Tavily Costs: ~$3.00
  - Total: ~$5.25/month

500 queries/day (15,000/month):
  - LLM Costs: ~$11.25
  - Tavily Costs: ~$15.00
  - Total: ~$26.25/month

1,000 queries/day (30,000/month):
  - LLM Costs: ~$22.50
  - Tavily Costs: ~$30.00
  - Total: ~$52.50/month
```

---

## 9. Security Specifications

### 9.1 Authentication
```yaml
Method: Password-based
Storage: Environment variable (AUTH_PASSWORD)
Session Duration: Until browser close
Password Requirements: None (configurable)
```

### 9.2 Authorization
```yaml
Model: Single-tenant (all authenticated users have full access)
```

### 9.3 Data Protection
```yaml
In Transit:
  - External APIs: HTTPS
  - MVK Ingest: HTTPS
  
At Rest:
  - ChromaDB: Unencrypted (local filesystem)
  - Session Data: In-memory only
  - No PII storage
```

### 9.4 Secrets Management
```yaml
API Keys:
  - Storage: Environment variables
  - Access: Read-only at startup
  - Logging: Never logged
  - Exposure: Not exposed in responses
```

---

## 10. Observability Specifications

### 10.1 Logging
```yaml
Format: Structured (timestamp, level, message)
Levels: DEBUG, INFO, WARNING, ERROR
Destinations: stdout (captured by Docker)
Retention: Managed by Docker log driver

Key Events:
  - Application startup
  - MVK SDK initialization
  - User authentication
  - Query processing start/end
  - Agent execution
  - Errors and exceptions
```

### 10.2 Metrics
```yaml
MVK SDK Metrics (automatic):
  - Span duration
  - Token usage
  - Cost attribution
  - Error rates
  - Throughput

Custom Metrics:
  - User feedback scores
  - Tool usage (Tavily, ChromaDB)
  - Agent selection frequency
```

### 10.3 Tracing
```yaml
Provider: MVK SDK
Format: OpenTelemetry-compatible
Sampling: 100% (all requests traced)
Batching: 60-second intervals
Endpoint: ingest.mavvrik.ai/v1/traces

Trace Attributes:
  - traceId: UUID per conversation
  - spanId: Unique per operation
  - parentSpanId: Span hierarchy
  - Business context (user, session, tenant)
  - Technical context (agent, stage, operation)
```

---

## 11. Error Handling Specifications

### 11.1 Error Categories
```yaml
User Errors:
  - Invalid credentials
  - Empty query
  - Unsupported request
  - Response: User-friendly message

System Errors:
  - LLM API failure
  - ChromaDB unavailable
  - Tavily API failure
  - Response: Generic error message + logging

Configuration Errors:
  - Missing API keys
  - Invalid environment variables
  - Response: Startup failure
```

### 11.2 Retry Logic
```yaml
LLM API Calls:
  - Max Retries: 3
  - Backoff: Exponential (1s, 2s, 4s)
  - Timeout: 30s per attempt

ChromaDB Queries:
  - Max Retries: 2
  - Backoff: Linear (1s, 2s)
  - Timeout: 5s per attempt

Tavily Searches:
  - Max Retries: 2
  - Backoff: Linear (2s, 4s)
  - Timeout: 10s per attempt
```

### 11.3 Fallback Behavior
```yaml
SDK Agent Failure:
  - Return: "I don't have that information in the documentation."
  - Continue: Yes (other agents may still respond)

Framework Router Failure:
  - Return: "⚠️ Couldn't find information about {framework}."
  - Continue: Yes

Code Generator Failure:
  - Return: None (omit code section)
  - Continue: Yes

All Agents Fail:
  - Return: Generic error message
  - Log: Full error details
```

---

## 12. Testing Specifications

### 12.1 Unit Tests
```yaml
Coverage Target: >80%
Framework: pytest
Location: tests/unit/

Test Categories:
  - Agent logic (intent classification, routing, synthesis)
  - Tool functionality (ChromaDB, Tavily)
  - Session management
  - Configuration validation
```

### 12.2 Integration Tests
```yaml
Coverage Target: Critical paths
Framework: pytest
Location: tests/integration/

Test Scenarios:
  - End-to-end query processing
  - Multi-agent coordination
  - External API integration (mocked)
  - Error handling and recovery
```

### 12.3 Performance Tests
```yaml
Tool: locust or pytest-benchmark
Metrics: Latency, throughput, resource usage

Scenarios:
  - Single user, simple query
  - Single user, complex query
  - 10 concurrent users
  - Sustained load (100 queries/hour)
```

---

## 13. Deployment Specifications

### 13.1 Build Process
```bash
# Build Docker image
docker build -t mvk-sdk-agent:latest .

# Tag for registry
docker tag mvk-sdk-agent:latest registry.example.com/mvk-sdk-agent:1.0

# Push to registry
docker push registry.example.com/mvk-sdk-agent:1.0
```

### 13.2 Deployment Process
```bash
# Deploy with Docker Compose
docker-compose up -d

# Health check
curl http://localhost:8000/health

# View logs
docker-compose logs -f
```

### 13.3 Environment Configuration
```yaml
Development:
  - PORT: 8000
  - LOG_LEVEL: DEBUG
  - AUTH_PASSWORD: dev-password

Staging:
  - PORT: 8000
  - LOG_LEVEL: INFO
  - AUTH_PASSWORD: staging-password
  - MVK_TENANT_ID: staging-tenant

Production:
  - PORT: 8000
  - LOG_LEVEL: WARNING
  - AUTH_PASSWORD: <secure-password>
  - MVK_TENANT_ID: production-tenant
  - Resource limits: 4GB RAM, 2 CPU
```

---

## 14. Maintenance Specifications

### 14.1 Backup & Restore
```yaml
ChromaDB Data:
  - Frequency: Daily
  - Method: Volume snapshot
  - Retention: 7 days
  - Location: /app/chroma/data

Configuration:
  - Frequency: On change
  - Method: Git version control
  - Retention: Indefinite
```

### 14.2 Updates
```yaml
Dependency Updates:
  - Frequency: Monthly
  - Process: 
      1. Review release notes
      2. Update requirements.txt
      3. Test in staging
      4. Deploy to production

Model Updates:
  - Frequency: As needed
  - Process:
      1. Update LLM_MODEL env var
      2. Test query quality
      3. Monitor costs
      4. Rollback if needed

Documentation Updates:
  - Frequency: As needed
  - Process:
      1. Re-ingest PDFs into ChromaDB
      2. Verify search quality
      3. Update collection stats
```

### 14.3 Monitoring
```yaml
Health Checks:
  - Endpoint: /health (if implemented)
  - Frequency: Every 60s
  - Alerts: On failure

Performance Monitoring:
  - Dashboard: MVK Dashboard
  - Metrics: Latency, cost, errors
  - Alerts: P95 latency > 35s, error rate > 5%

Cost Monitoring:
  - Dashboard: MVK Dashboard + OpenAI dashboard
  - Alerts: Daily cost > $5, monthly projection > $100
```

---

## 15. Compliance & Governance

### 15.1 Data Retention
```yaml
Session Data:
  - Duration: In-memory only (cleared on restart)
  - PII: Usernames (not persisted)

Conversation History:
  - Duration: In-memory only
  - PII: User queries (not persisted)

Telemetry Data:
  - Duration: Per MVK retention policy
  - PII: user_id (username - pseudonymized if needed)
```

### 15.2 Privacy
```yaml
User Consent:
  - Required for: Telemetry tracking
  - Method: Login implies consent (document in ToS)

Data Sharing:
  - External Services: OpenAI, Tavily, MVK
  - Purpose: Service provision and observability
  - User Control: None (required for operation)
```

---

## 16. Version History

### 16.1 Current Version
```yaml
Version: 1.0.0
Release Date: 2025-11-18
Status: Production
```

### 16.2 Change Log
```yaml
1.0.0 (2025-11-18):
  - Initial production release
  - 4 agent architecture
  - Full MVK SDK instrumentation
  - ChromaDB integration (55 docs)
  - Tavily web search
  - Code generation
  - Feedback tracking
```

---

## 17. Glossary

```yaml
RAG: Retrieval Augmented Generation - LLM technique using external knowledge
LLM: Large Language Model (e.g., GPT-4o-mini)
Embedding: Vector representation of text
Vector Store: Database for similarity search (ChromaDB)
Span: Unit of work in distributed tracing
Trace: Collection of spans representing a request
Context: Metadata attached to spans (user, session, etc.)
Signal: MVK SDK decorator for automatic tracking
Wrapper: Auto-instrumentation for external libraries
Metric: Quantifiable measurement (tokens, cost, etc.)
Agent: Specialized component for specific tasks
Orchestrator: Coordinator of multiple agents
Specialist: Framework-specific sub-agent
Tool: Utility function (ChromaDB, Tavily)
```

---

## 18. References

### 18.1 Internal Documentation
- ARCHITECTURE.md - System architecture diagrams and flow
- README.md - Setup and usage instructions
- Code comments - Inline documentation

### 18.2 External Documentation
- MVK SDK Documentation: Internal docs (in ChromaDB)
- OpenAI API: https://platform.openai.com/docs
- Chainlit: https://docs.chainlit.io
- LangChain: https://python.langchain.com
- ChromaDB: https://docs.trychroma.com
- Tavily: https://tavily.com/docs

---

## 19. Appendix

### 19.1 Sample Queries
```yaml
SDK Question:
  - "What does mvk.signal() do?"
  - "How do I track LLM costs?"
  - "Explain mvk.context()"

Framework Question:
  - "How do I integrate MVK SDK with LangChain?"
  - "Show me MVK instrumentation for LlamaIndex"

Code Request:
  - "Generate code for tracking a LangChain RetrievalQA chain"
  - "Example of MVK SDK with CrewAI agents"
```

### 19.2 Sample Responses
```yaml
SDK Response:
  - Brief explanation from documentation
  - Source references (Page X)
  - Code examples if available

Framework Response:
  - Framework-specific guidance
  - Integration steps
  - Web sources

Code Response:
  - Complete Python code
  - Detailed explanation
  - Cost estimate
  - Gotchas/warnings
```

---

**Document End**
