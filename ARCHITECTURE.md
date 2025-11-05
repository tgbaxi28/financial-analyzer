# Architecture & Design Document

## System Overview

The Financial Report Analysis System is a containerized, **multi-agent AI platform** powered by **LlamaIndex** for intelligent analysis of financial documents. The system implements a **collaborative multi-agent architecture** where specialized AI agents work together using the **Retrieval-Augmented Generation (RAG)** pattern with runtime credential management.

**Version**: 2.0 (Multi-Agent Architecture)  
**Last Updated**: November 2025

## Core Design Principles

### 🔒 Security First
- **Zero Credential Storage**: No passwords/keys ever persisted
- **Runtime-Only Credentials**: Stored in memory, discarded after session
- **Audit Everything**: Every query logged with provider, timestamp, and agent
- **No External Data**: All context from uploaded files only
- **Agent Isolation**: Each agent operates in controlled context with defined tools

### 📈 Scalability
- **Horizontal Scaling**: Multiple app instances behind load balancer
- **Agent Statelessness**: Agents are stateless and can be parallelized
- **Vector Database**: pgvector with HNSW indexing for fast search
- **Connection Pooling**: Reuse database connections efficiently
- **Async Operations**: Batch processing for large document sets

### 🛡️ Reliability
- **Multi-Provider Fallback**: Switch providers if one fails
- **Agent Fault Tolerance**: Failed agents don't crash the system
- **Error Handling**: Graceful degradation with informative messages
- **Health Checks**: Container health endpoints for monitoring
- **Data Persistence**: PostgreSQL with backup strategy
- **Conversation Recovery**: Persist agent conversations for resilience

### 🤖 Multi-Agent Intelligence
- **Specialization**: Each agent has domain expertise
- **Collaboration**: Agents can be orchestrated for complex queries
- **Transparency**: All agent decisions are logged and traceable
- **Extensibility**: Easy to add new agents without modifying core system

## Architecture Layers

### 1. Presentation Layer (Gradio UI)
- **Single-Page Application**: Gradio Blocks
- **Four Main Tabs**:
  - Credentials: Input AI provider keys (not stored)
  - Reports: Upload and manage documents (supports password-protected files)
  - Chat: Natural language queries with multi-agent routing
  - BI Bot: Pre-built financial analyses (legacy mode)
- **Real-time Feedback**: Agent attribution, status updates, progress indicators
- **Responsive Design**: Works on desktop/tablet
- **Multi-Agent Controls**: Toggle for enabling/disabling agent routing

### 2. Multi-Agent Layer (LlamaIndex Framework)

#### Agent Architecture Pattern
The system uses **ReAct (Reasoning + Acting)** agents from LlamaIndex, allowing agents to:
1. **Reason**: Think about the query and plan approach
2. **Act**: Use tools to gather information
3. **Observe**: Process tool results
4. **Iterate**: Repeat until satisfied or max iterations reached

```
┌─────────────────────────────────────────────────────────┐
│            Agent Orchestrator (Coordinator)              │
│  • Manages conversation state                            │
│  • Routes queries to appropriate agents                  │
│  • Combines results from multiple agents                 │
│  • Maintains conversation history                        │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
┌───────▼──────┐ ┌──▼───────┐ ┌─▼──────────┐
│ Document     │ │ Metrics  │ │ Trend      │
│ Agent        │ │ Agent    │ │ Agent      │
├──────────────┤ ├──────────┤ ├────────────┤
│Tools:        │ │Tools:    │ │Tools:      │
│• search_docs │ │• calc_   │ │• analyze_  │
│• extract_    │ │  ratio   │ │  growth    │
│  section     │ │• calc_   │ │• compare_  │
│• list_       │ │  liquidity│ │  periods   │
│  reports     │ │• calc_   │ │• identify_ │
│              │ │  profit  │ │  variance  │
│              │ │• calc_   │ │• seasonal  │
│              │ │  leverage│ │            │
└──────────────┘ └──────────┘ └────────────┘
        │            │            │
        └────────────┼────────────┘
                     │
        ┌────────────▼────────────┐
        │   Query Router Agent    │
        │  (Intent Classification)│
        │  • Keywords matching    │
        │  • Context analysis     │
        │  • Agent selection      │
        └─────────────────────────┘
```

#### BaseFinancialAgent Abstract Class
```python
class BaseFinancialAgent:
    """
    Abstract base for all financial agents.
    Provides common functionality:
    - LlamaIndex ReActAgent initialization
    - System prompt management
    - Tool registration
    - Context formatting
    - Error handling
    """
    
    def __init__(self, name, description, llm, tools):
        self.name = name
        self.description = description
        self.tools = tools
        self.agent = self._create_agent(llm)
    
    def _create_agent(self, llm) -> ReActAgent:
        """Creates LlamaIndex ReAct agent with tools"""
        return ReActAgent.from_tools(
            tools=self.tools,
            llm=llm,
            verbose=True,
            max_iterations=self.max_iterations
        )
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Each agent defines its own expertise"""
        pass
    
    @abstractmethod
    def _create_tools(self) -> List[FunctionTool]:
        """Each agent defines its own tools"""
        pass
```

#### Agent Specializations

**1. DocumentAnalysisAgent**
- **Purpose**: Search and extraction from financial documents
- **Tools Implementation**:
  - `search_documents()`: Uses embedding service for semantic search
  - `extract_section()`: Regex-based section extraction
  - `list_available_reports()`: Database query for indexed reports
- **System Prompt**: Emphasizes document structure understanding
- **Max Iterations**: 10 (allows thorough search)
- **Temperature**: 0.7 (balanced creativity for interpretation)

**2. FinancialMetricsAgent**
- **Purpose**: Calculate financial ratios and metrics
- **Tools Implementation**:
  - `calculate_liquidity_ratios()`: Current, quick, cash ratios
  - `calculate_profitability_ratios()`: ROA, ROE, profit margins
  - `calculate_leverage_ratios()`: D/E, interest coverage
  - `calculate_ratio()`: Generic ratio calculator
- **System Prompt**: Emphasizes accounting precision
- **Max Iterations**: 8 (calculations are deterministic)
- **Temperature**: 0.5 (lower for accuracy)

**3. TrendAnalysisAgent**
- **Purpose**: Identify patterns and trends over time
- **Tools Implementation**:
  - `analyze_growth_trend()`: Regression analysis on time series
  - `compare_periods()`: YoY, QoQ, MoM comparisons
  - `identify_variance()`: Actual vs budget/forecast
  - `seasonal_analysis()`: Quarterly pattern detection
- **System Prompt**: Emphasizes statistical analysis
- **Max Iterations**: 8
- **Temperature**: 0.6 (balanced for insights)

**4. QueryRouterAgent**
- **Purpose**: Classify intent and route to specialists
- **Implementation**: Keyword-based routing with context
- **Routing Logic**:
  ```python
  keywords_map = {
      'document_analysis': ['show', 'find', 'extract', 'what', 'where'],
      'financial_metrics': ['calculate', 'ratio', 'roe', 'roa', 'margin'],
      'trend_analysis': ['trend', 'growth', 'compare', 'yoy', 'qoq']
  }
  ```
- **Fallback**: Routes to DocumentAnalysisAgent by default

**5. AgentOrchestrator**
- **Purpose**: Coordinate all agents and manage state
- **Capabilities**:
  - Single-agent execution for simple queries
  - Multi-agent collaboration for complex queries
  - Conversation history management
  - Performance tracking and logging
- **State Management**:
  ```python
  {
      'conversation_history': List[Dict],
      'agent_responses': Dict[str, str],
      'performance_metrics': Dict[str, float],
      'session_id': str
  }
  ```

### 3. Application Layer (Python Services)

#### LLM Provider Abstraction (Enhanced for Multi-Agent)

```
┌─────────────────────────────────────────┐
│       LLM Adapter (Multi-Agent)         │
├─────────────────────────────────────────┤
│ • Creates LlamaIndex LLM instances      │
│ • Manages provider-specific configs     │
│ • Handles embedding models              │
│ • Provides unified interface            │
└────────────────┬────────────────────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
┌───▼──────┐ ┌──▼──────┐ ┌──▼──────┐
│ Azure    │ │ Google  │ │ AWS     │
│ OpenAI   │ │ Gemini  │ │ Bedrock │
│ LLM      │ │ LLM     │ │ LLM     │
└──────────┘ └─────────┘ └─────────┘
```

**LLMAdapter Class**:
```python
class LLMAdapter:
    """
    Bridge between provider credentials and LlamaIndex LLMs.
    Supports: Azure OpenAI, Google Gemini, AWS Bedrock
    """
    
    @staticmethod
    def create_llm(credentials: ProviderCredentials):
        """Create LlamaIndex LLM instance"""
        if credentials.provider == "azure":
            return AzureOpenAI(
                model=credentials.model,
                api_key=credentials.credentials['api_key'],
                azure_endpoint=credentials.credentials['endpoint'],
                api_version="2024-02-15-preview"
            )
        elif credentials.provider == "google":
            return Gemini(
                model=credentials.model,
                api_key=credentials.credentials['api_key']
            )
        elif credentials.provider == "aws":
            return Bedrock(
                model=credentials.model,
                aws_access_key_id=credentials.credentials['access_key'],
                aws_secret_access_key=credentials.credentials['secret_key'],
                region_name=credentials.credentials['region']
            )
    
    @staticmethod
    def get_embedding_model(credentials):
        """Create embedding model for vector generation"""
        # Similar pattern for embedding models
```

**Features**:
- Unified interface for all providers
- Automatic credential validation
- Provider-specific error handling
- Embedding generation (1536 dimensions)
- Chat response generation
- Multi-agent compatible

#### Document Processing Pipeline (IBM Docling)
```
Upload → Validate → Extract → Chunk → Embed → Store
  ↓        ↓         ↓        ↓       ↓      ↓
 File    Format    Text     1000    Vector  DB
        Check     Tables     char
        Password  (Docling)
```

**IBM Docling Integration**:
- **Unified Processor**: All formats use IBM Granite-Docling
- **Supported Formats**: PDF, Excel (XLSX), CSV, JSON, DOCX
- **Password Support**: Handles encrypted PDFs and protected files
- **Table Extraction**: Advanced table structure recognition
- **Layout Analysis**: Preserves document structure and sections

**Processing Flow**:
```python
class DocumentProcessor:
    def __init__(self, file_path, file_type, password=None):
        self.file_path = file_path
        self.file_type = file_type
        self.password = password
    
    def process(self):
        # Use IBM Docling for all formats
        from docling.document_converter import DocumentConverter
        
        converter = DocumentConverter()
        result = converter.convert(
            self.file_path,
            password=self.password
        )
        
        full_text = result.document.export_to_markdown()
        chunks = self._create_chunks(full_text)
        
        return full_text, chunks
    
    def _create_chunks(self, text, chunk_size=1000, overlap=200):
        # Semantic chunking with overlap
        chunks = []
        for i in range(0, len(text), chunk_size - overlap):
            chunk = text[i:i + chunk_size]
            chunks.append({
                'text': chunk,
                'chunk_index': len(chunks),
                'section_type': self._detect_section(chunk)
            })
        return chunks
```

#### Embedding Service
```
┌──────────────────────────┐
│  Semantic Search Engine  │
├──────────────────────────┤
│ • Vector similarity      │
│ • Hybrid search          │
│ • Top-K retrieval        │
│ • Chunking strategy      │
└──────────────────────────┘
```

**Capabilities**:
- Stores 1536-dimensional embeddings
- Cosine similarity search
- Keyword filtering support
- Provider re-indexing
- Batch embedding generation

#### Audit Service (Enhanced for Multi-Agent)
```
┌──────────────────────────────────────┐
│   Compliance & Multi-Agent Logging   │
├──────────────────────────────────────┤
│ • Query tracking with agent info     │
│ • Provider usage stats               │
│ • Agent performance metrics          │
│ • Conversation history               │
│ • Retention policies                 │
│ • Agent decision logging             │
└──────────────────────────────────────┘
```

**Logging Enhancements**:
- Every query: text, provider, model, agent, latency, success
- Agent execution: which agents used, tools invoked, iterations
- Multi-agent queries: agent collaboration patterns
- Performance: response time per agent
- Errors: agent-specific error tracking
- Session tracking: conversation correlation across agents

**Structured Logging System**:
```python
# utils/logger.py provides:
- JSONFormatter: Machine-readable logs
- ColoredFormatter: Human-readable console
- LogContext: Contextual information (session_id, user_id)
- @log_performance: Decorator for timing functions
- Log rotation: 10MB files, 5 backups
- Three log files: app.log, error.log, agents.log
```

### 4. Data Layer (PostgreSQL + pgvector)

#### Database Schema
```sql
reports
├── id (UUID, PK)
├── filename
├── file_path
├── file_size_bytes
├── file_type
├── upload_date
├── processing_status
├── embedding_provider
├── chunks_created
└── [FK to audit_logs]

chunks
├── id (UUID, PK)
├── report_id (FK)
├── chunk_text
├── chunk_index
├── page_number
├── section_type
├── embedding (Vector 1536) ⭐
├── embedding_model
└── created_at

audit_logs
├── id (UUID, PK)
├── query_text
├── query_type
├── provider_name
├── provider_model
├── agent_name (NEW: which agent handled query)
├── agent_tools_used (NEW: JSON array of tools)
├── processing_time_ms
├── chunks_used
├── success
├── error_message
├── session_id
└── created_at

conversation_messages
├── id (UUID, PK)
├── session_id
├── message_index
├── role
├── content
├── provider_used
├── model_used
├── agent_used (NEW: which agent generated response)
├── chunks_referenced (JSON)
└── created_at
```

#### Indexing Strategy
```sql
-- Fast vector search (approximate)
CREATE INDEX chunks_embedding_idx 
ON chunks USING hnsw (embedding vector_cosine_ops);

-- Supporting indexes
CREATE INDEX chunks_report_idx ON chunks(report_id);
CREATE INDEX chunks_created_idx ON chunks(created_at);
CREATE INDEX audit_created_idx ON audit_logs(created_at);
CREATE INDEX audit_provider_idx ON audit_logs(provider_name);
```

### 5. Infrastructure Layer (Docker & Networking)

#### Container Architecture
```
┌─────────────────────────────┐
│     Docker Host Network     │
├─────────────────────────────┤
│  ┌─────────┐ ┌────────┐    │
│  │ Gradio  │ │ Nginx  │    │
│  │ App:7860│ │:80/:443│    │
│  │(Multi-  │ │        │    │
│  │ Agent)  │ │        │    │
│  └────┬────┘ └────┬───┘    │
│       │            │        │
│  ┌────▼────────────▼───┐    │
│  │  PostgreSQL + pgv   │    │
│  │  vector:5432        │    │
│  └─────────────────────┘    │
└─────────────────────────────┘
```

#### Docker Compose Services
1. **app**: Gradio application (Python 3.11)
2. **postgres**: PostgreSQL 16 + pgvector extension
3. **nginx**: Reverse proxy (SSL termination, rate limiting)

#### Network Communication
- Gradio ↔ PostgreSQL: Direct TCP (5432)
- External ↔ Nginx: HTTPS (443) / HTTP (80)
- Nginx ↔ Gradio: HTTP (7860)
- All services: Internal docker network

## Data Flow

### Multi-Agent Chat Query Flow
```
1. User enters question
   ↓
2. Question → AgentOrchestrator receives query
   ↓
3. If routing enabled → QueryRouterAgent analyzes intent
   ↓
4. Router → Selects appropriate specialist agent(s)
   ↓
5. Specialist Agent → Receives query + context
   ↓
6. Agent → Reasons about approach (ReAct)
   ↓
7. Agent → Selects and executes tool
   ↓
8. Tool → May generate embedding → Search pgvector
   ↓
9. Tool → May calculate metric → Return result
   ↓
10. Agent → Observes tool result
   ↓
11. Agent → Decides: iterate or finish
   ↓
12. Agent → Generates final response
   ↓
13. Orchestrator → Logs agent execution (audit trail)
   ↓
14. Orchestrator → Returns response with agent attribution
   ↓
15. UI → Displays response with agent name
```

### Multi-Agent Collaboration Flow (Complex Queries)
```
1. User: "Analyze revenue trend and calculate ROE"
   ↓
2. Orchestrator → Detects need for multiple agents
   ↓
3. Execute in parallel:
   ├── TrendAnalysisAgent → analyze_growth_trend(revenue)
   └── FinancialMetricsAgent → calculate_profitability_ratios()
   ↓
4. Orchestrator → Combines results
   ↓
5. Orchestrator → Generates unified response
   ↓
6. Response: "Revenue grew 15% YoY. ROE is 18.5%"
```

### Report Upload Flow
```
1. User selects file (optionally provides password)
   ↓
2. Validate file type and size
   ↓
3. Extract text and tables using IBM Docling
   ↓
4. Split into semantic chunks (1000 char, 200 overlap)
   ↓
5. Generate embeddings for each chunk (using LLM adapter)
   ↓
6. Store embeddings + metadata in PostgreSQL
   ↓
7. Update report status to "ready"
   ↓
8. Log embedding generation to audit trail
   ↓
9. Agent tools can now access this report
```

## Credential Management Strategy

### Current Architecture (No Storage)
```
┌─────────────────────────┐
│  User Credentials       │
│  (Entered in UI)        │
└────────────┬────────────┘
             │ (HTTP POST)
             ↓
        ┌────────────┐
        │ Validation │ → Test with provider
        └────────────┘
             │ (Success)
             ↓
┌─────────────────────────┐
│ Session Memory Object   │
│ (current_session dict)  │
│ - credentials dict      │
│ - provider name         │
│ - model name            │
│ - llm instance          │
│ - embedding model       │
└────────────┬────────────┘
             │ (In-memory only)
             ↓
         ┌────────────┐
         │ LLM Adapter│ → Create LlamaIndex LLM
         │            │ → Initialize agents
         └────────────┘
             │
         ┌────────────┐
         │ Agent Calls│ → Generate embeddings
         │            │ → Chat responses
         │            │ → Tool execution
         └────────────┘
             │ (Session ends)
             ↓
        Credentials & agents discarded
```

**Security Benefits**:
- No database storage means no data breach risk
- Credentials never written to disk or logs
- Each session is isolated
- Agents are recreated per session
- No persistent attack surface

### Alternative: Secure Storage (Future)
If credential storage is needed:
```python
# Encryption at rest
from cryptography.fernet import Fernet
cipher = Fernet(encryption_key)
encrypted_creds = cipher.encrypt(credentials.encode())

# Store encrypted, retrieve on login
credential = CredentialModel(
    user_id=user.id,
    provider="azure",
    encrypted_value=encrypted_creds,
    created_at=datetime.utcnow()
)

# Decrypt only in memory when needed
decrypted = cipher.decrypt(stored_encrypted).decode()
```

## Performance Optimization

### Agent-Level Optimization

**Agent Configuration Tuning**:
```json
{
  "document_analysis": {
    "max_iterations": 10,  // Higher for thorough search
    "temperature": 0.7,    // Balanced creativity
    "timeout_seconds": 30
  },
  "financial_metrics": {
    "max_iterations": 8,   // Lower for deterministic calculations
    "temperature": 0.5,    // Lower for accuracy
    "timeout_seconds": 20
  },
  "trend_analysis": {
    "max_iterations": 8,
    "temperature": 0.6,
    "timeout_seconds": 25
  }
}
```

**Agent Caching**:
- Cache agent tool results for identical queries (5 min TTL)
- Cache embedding searches (10 min TTL)
- LRU cache for frequent calculations
- Session-level conversation caching

**Parallel Agent Execution**:
```python
# For multi-agent queries
import asyncio

async def execute_agents_parallel(agents, query):
    tasks = [agent.execute(query) for agent in agents]
    results = await asyncio.gather(*tasks)
    return combine_results(results)
```

### Vector Search Optimization
```
Index Type       | Recall | Speed   | Memory |
─────────────────┼────────┼─────────┼────────┤
Linear scan      | 100%   | Slow    | Low    │
IVFFlat (100)    | 90%    | Medium  | Medium │
HNSW (m=16)      | 95%    | Fast    | High   │
```

### Recommended for Production
```sql
-- Create HNSW index after initial data loading
CREATE INDEX chunks_embedding_hnsw 
ON chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Tune search parameters
SET hnsw.ef_search = 100;  -- Higher = more accurate but slower
```

### Batch Processing Strategy
```
1. Collect queries (queue)
2. Batch similar queries
3. Generate embeddings in parallel
4. Cache results for 5 minutes
5. Reduce API calls by 60%
```

## Scaling Strategy

### Vertical Scaling (Add Resources)
```
Single Server:
├── CPU: 4 cores → 8+ cores
├── RAM: 4GB → 16GB+
├── Storage: 50GB → 500GB+
└── Network: 1Gbps → 10Gbps
```

### Horizontal Scaling (Add Instances)
```
Load Balancer (Nginx)
    ├── App Instance 1 (port 7860) [5 agents initialized]
    ├── App Instance 2 (port 7861) [5 agents initialized]
    ├── App Instance 3 (port 7862) [5 agents initialized]
    └── App Instance N (port 786N) [5 agents initialized]

All instances → Same PostgreSQL (connection pooling)

Session Affinity: Required for agent conversation state
```

**Agent Scaling Considerations**:
- Each app instance has its own agent instances
- Agents are stateless (conversation in DB)
- Load balancer needs session affinity for conversations
- Agents can be instantiated on-demand per user session

### Database Optimization
```
Primary Database (Writes)
└── Read Replicas (Audit logs, Reports listing)

Connection Pool: 25-50 connections per app instance
Max Connections: number_of_app_instances × pool_size
```

## Security Architecture

### Authentication & Authorization
```
Future Implementation:
├── User Registration/Login
├── API Key generation per user
├── Role-based access (Admin/User)
├── Audit logs per user
└── Rate limiting per user
```

### Encryption Strategy
```
Current (Runtime Only):
├── Credentials never written to disk
├── No database storage of secrets
├── HTTPS only for external communication
└── Connection pooling over local network

Future (Secure Storage):
├── Encrypt credentials at rest (AES-256)
├── Key management with AWS KMS / Azure Key Vault
├── Rotate keys annually
└── Audit key access
```

### Data Privacy
```
GDPR Compliance:
├── Audit logs retention: 1 year max
├── Right to deletion: Remove report + chunks + logs
├── Data portability: Export conversations as JSON
└── Transparency: Show all logged data

CCPA Compliance:
├── Opt-out mechanisms
├── Data sale prohibition
├── Sensitive personal info handling
└── Consumer notice requirements
```

## Deployment Topology

### Development
```
Developer Laptop
├── Docker Desktop
├── All services in one Compose stack
├── Shared network bridge
├── SQLite or local PostgreSQL
└── Multi-agent system: 5 agents per session
```

**Agent Considerations**:
- Agents initialized per user session
- Fast iteration for agent development
- Debug logging enabled for agent decisions
- All agents run in single process

### Staging
```
Cloud VM (e.g., EC2, GCP VM)
├── Docker Swarm or Kubernetes (2-3 replicas)
├── Managed PostgreSQL (AWS RDS, Azure Database)
├── SSL with Let's Encrypt
├── Monitoring + logging stack (agent metrics)
└── Session affinity for multi-agent conversations
```

**Agent Considerations**:
- Load balancer with session affinity
- Agent logs forwarded to centralized logging
- Test agent routing accuracy
- Monitor agent performance metrics

### Production
```
Kubernetes Cluster (EKS/AKS/GKE)
├── Multiple Gradio pods (auto-scaling 5-20 pods)
│   └── Each pod: 5 agents per user session
├── Managed database (RDS, Azure, Cloud SQL)
├── Managed Redis (agent result caching)
├── Load balancer (ALB, Azure LB, GCP LB)
│   └── Session affinity enabled
├── CDN (CloudFront, Azure CDN, Cloud CDN)
├── Monitoring (Prometheus, Datadog)
│   └── Custom metrics: agent latency, routing accuracy
├── Logging (ELK, Splunk, CloudWatch)
│   └── Structured logs: agents.log, app.log, error.log
└── Backup & DR strategy
```

**Agent Considerations**:
- Each pod initializes agents on-demand
- Session state stored in database
- Agent metrics: response time, accuracy, tool usage
- Alert on agent failures or timeouts
- A/B test different agent configurations

## Technology Stack Justification

| Component | Choice | Why |
|-----------|--------|-----|
| Frontend | Gradio | Easy UI, no JS needed, perfect for ML apps |
| Multi-Agent Framework | LlamaIndex | Production-ready agents, ReAct pattern, extensive tool support |
| Backend | Python | Simple, LLM SDKs available, rapid dev |
| Database | PostgreSQL | Mature, pgvector support, reliable |
| Vector Store | pgvector | Integrated with PostgreSQL, easy deployment |
| LLM Providers | Multiple | Avoid vendor lock-in, cost optimization |
| Document Processing | IBM Docling | Unified extraction, password support, high quality |
| Logging | Python logging | Standard library, customizable, structured |
| Container | Docker | Standard, reproducible builds |
| Orchestration | Docker Compose | Simple for dev/test, Kubernetes for production |
| Reverse Proxy | Nginx | Lightweight, battle-tested, good rate limiting |

## Cost Breakdown (Monthly Estimate)

### Infrastructure (AWS Example)
```
EC2 (app server, t3.large):        $100
RDS (PostgreSQL, 1TB storage):     $200
Load Balancer:                     $25
NAT Gateway:                       $30
Backup storage:                    $20
─────────────────────────────────
Total Infrastructure:              $375
```

### AI Provider Costs (1000 queries/day with Multi-Agent)
```
Scenario: 1000 queries/day
- 40% DocumentAgent (search): 400 queries
- 30% MetricsAgent (calculation): 300 queries  
- 30% TrendAgent (analysis): 300 queries

Embeddings (1000 docs, 1000 tokens avg):    $2 (Azure)
Chat responses (avg 500 tokens):            $5 (Azure)
Agent overhead (ReAct iterations):          +20% = $1.4

Total AI cost per day: $8.40 (Azure)

Alternative with Google Gemini:             $4/day
Alternative with AWS Bedrock:               $15/day
```

### Total Monthly Estimate
```
Infrastructure + AI:  $375 + $252 = $627/month (Azure with agents)
                      $375 + $120 = $495/month (Google with agents)
                      $375 + $450 = $825/month (AWS with agents)

Note: Multi-agent system adds ~20% to AI costs due to:
- Agent reasoning iterations (ReAct)
- Tool execution overhead
- Multi-agent collaboration for complex queries
```

## Future Enhancements

1. **Enhanced Multi-Agent System**:
   - Add specialized agents (Risk Analysis, Compliance, Forecasting)
   - Agent-to-agent communication without orchestrator
   - Hierarchical agent structures (supervisor → specialist)
   - Learning from user feedback to improve routing

2. **Multi-User Support**: User authentication, separate audit trails per user

3. **Custom Agent Training**: Fine-tune agent system prompts on org data

4. **Real-time Collaboration**: Multiple users querying with shared agent context

5. **Advanced Visualizations**: Agent-generated charts, dashboards, trend visualizations

6. **Mobile App**: React Native/Flutter client with agent support

7. **Compliance Automation**: GDPR/HIPAA/SOC2 audit reports with agent attribution

8. **API Gateway**: REST/GraphQL API for third-party agent integration

9. **Autonomous Analysis**: Agents proactively identify issues in new reports

10. **Knowledge Base**: Persistent agent memory across users/organizations

11. **Agent Marketplace**: Community-contributed specialized agents

12. **Predictive Analytics**: Forecasting agents based on historical data

---

**Document Version**: 2.0 (Multi-Agent Architecture)  
**Last Updated**: November 2025  
**Architecture Owner**: Platform Engineering Team