# Financial Report Analysis System - Multi-Agent AI Platform

## 🤖 Overview

The Financial Report Analysis System is a **Multi-Agent AI platform** powered by **LlamaIndex**, providing intelligent, specialized analysis of financial documents through collaborative AI agents. The system uses a multi-provider LLM architecture with **no credential storage** (credentials are entered at runtime).

### 🌟 What's New in v2.0

**Multi-Agent AI System** - Intelligent query routing and specialized analysis through:
- 📄 **Document Analysis Agent** - Expert in searching and extracting information
- 📊 **Financial Metrics Agent** - Specialized in calculating ratios and metrics
- 📈 **Trend Analysis Agent** - Identifies patterns and trends over time
- 🧭 **Query Router Agent** - Routes queries to the best specialist
- 🎯 **Agent Orchestrator** - Coordinates all agents seamlessly

**Enhanced Logging System** - Production-ready observability:
- Structured logging (JSON & text formats)
- Automatic log rotation (10MB files, 5 backups)
- Colored console output for easy debugging
- Separate logs for app, errors, and agents
- Performance tracking and metrics

## Key Features

### ✨ Core Capabilities

- **🤖 Multi-Agent AI System**: LlamaIndex-powered intelligent agents with specialized expertise
- **Multi-Provider LLM Support**: Azure OpenAI, Google Gemini, AWS Bedrock
- **Intelligent Query Routing**: Automatic routing to the most appropriate specialist agent
- **Unified Document Processing**: IBM Granite-Docling for consistent extraction across all formats
- **Password-Protected Files**: Support for encrypted PDFs and other password-protected documents
- **Semantic Search**: pgvector-based vector database for intelligent document retrieval
- **File-in-Context Only**: All responses based solely on uploaded documents
- **Runtime Credentials**: No storage of sensitive credentials
- **Comprehensive Logging**: Multi-level logging with rotation and performance tracking
- **Conversation Management**: Maintains chat history with audit logging
- **Pre-built Analytics**: Variance, trend, and ratio analysis templates
- **Comprehensive Audit Trail**: Track all queries and provider usage

### 📋 File Format Support

- PDF (including password-protected) - using IBM Granite-Docling
- Excel (XLSX) - using IBM Granite-Docling
- CSV - using IBM Granite-Docling
- JSON - using IBM Granite-Docling
- DOCX - using IBM Granite-Docling

**Note**: All document processing now uses IBM Granite-Docling for consistent, high-quality extraction across all formats.

## 🏗️ Multi-Agent Architecture

### Agent System

The system uses specialized AI agents that collaborate to provide comprehensive financial analysis:

```
User Query
    ↓
Query Router Agent (Analyzes intent)
    ↓
┌─────────────────┬──────────────────┬────────────────────┐
│  Document Agent │  Metrics Agent   │   Trend Agent      │
│  (Search docs)  │  (Calculate)     │   (Analyze trends) │
└─────────────────┴──────────────────┴────────────────────┘
    ↓
Agent Orchestrator (Coordinates & combines results)
    ↓
Unified Response with Agent Attribution
```

### Specialized Agents

#### 1. 📄 Document Analysis Agent
- **Purpose**: Searches and extracts information from financial documents
- **Expertise**: Understanding document structure (balance sheets, income statements, cash flow)
- **Tools**:
  - `search_documents`: Semantic search across uploaded reports
  - `extract_section`: Extract specific sections from documents
  - `list_available_reports`: Show all indexed reports
- **Use Cases**: "What was the revenue in Q3?", "Show me the balance sheet"

#### 2. 📊 Financial Metrics Agent
- **Purpose**: Calculates financial ratios and metrics
- **Expertise**: Liquidity, profitability, leverage, efficiency ratios
- **Tools**:
  - `calculate_ratio`: Generic ratio calculation
  - `calculate_liquidity_ratios`: Current ratio, quick ratio, cash ratio
  - `calculate_profitability_ratios`: ROA, ROE, profit margins
  - `calculate_leverage_ratios`: Debt-to-equity, interest coverage
- **Use Cases**: "Calculate the current ratio", "What's the ROE?"

#### 3. 📈 Trend Analysis Agent
- **Purpose**: Identifies trends and patterns in financial data
- **Expertise**: Growth trends, variance analysis, seasonal patterns
- **Tools**:
  - `analyze_growth_trend`: Track metrics over time
  - `compare_periods`: YoY, QoQ, MoM comparisons
  - `identify_variance`: Actual vs budget analysis
  - `seasonal_analysis`: Detect quarterly patterns
- **Use Cases**: "Show revenue trend over 4 quarters", "Compare YoY growth"

#### 4. 🧭 Query Router Agent
- **Purpose**: Routes queries to the most appropriate specialist
- **Expertise**: Intent classification and agent selection
- **Logic**: Keyword matching and context analysis
- **Use Cases**: Automatically determines which agent handles each query

#### 5. 🎯 Agent Orchestrator
- **Purpose**: Coordinates all agents and maintains conversation context
- **Features**:
  - Single-agent execution for simple queries
  - Multi-agent collaboration for complex queries
  - Conversation history management
  - Performance tracking

### Enhanced Logging System

#### Log Files (in `logs/` directory)

- **app.log**: Complete application log with all events
- **error.log**: Errors and critical issues only
- **agents.log**: Agent-specific operations and decisions

#### Logging Features

- **Structured Logging**: JSON and text formats
- **Log Rotation**: Automatic rotation (10MB files, 5 backups)
- **Colored Console Output**: Easy-to-read colored logs (DEBUG=cyan, INFO=green, WARNING=yellow, ERROR=red, CRITICAL=magenta)
- **Performance Tracking**: Built-in timing decorators
- **Context Logging**: Session, user, and query metadata
- **Third-party Suppression**: Quiets verbose libraries

#### Log Levels

Configure via environment variable:
```bash
export LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

#### Viewing Logs

```bash
# Real-time monitoring
tail -f logs/app.log

# View errors only
tail -f logs/error.log

# View agent operations
tail -f logs/agents.log

# Search for specific patterns
grep "ERROR" logs/app.log
grep "agent.document" logs/agents.log
```

## Architecture

### System Components

```
```
┌─────────────────────────────────────────────────────┐
│              Gradio Web Interface                    │
│  ┌──────────────┬──────────────┬──────────────┐    │
│  │   Chat Tab   │  BI Bot Tab  │ Reports Tab  │    │
│  │              │              │  (Password)  │    │
│  └──────────────┴──────────────┴──────────────┘    │
│  ┌───────────────────────────────────────────┐    │
│  │      Credentials Tab (Runtime Only)       │    │
│  └───────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
    ┌───▼──┐   ┌─────▼─────┐   ┌──▼────┐
    │ Azure │   │  Google   │   │  AWS  │
    │  AI   │   │  Gemini   │   │ Bedrock
    └───┬──┘   └─────┬─────┘   └──┬────┘
        │             │             │
        └─────────────┼─────────────┘
                      │
        ┌─────────────▼──────────────┐
        │   Multi-Provider LLM       │
        │   Abstraction Layer        │
        └─────────────┬──────────────┘
                      │
        ┌─────────────▼──────────────┐
        │   LlamaIndex Multi-Agent   │
        │   System (5 Agents)        │
        └─────────────┬──────────────┘
                      │
        ┌─────────────▼──────────────┐
        │ IBM Granite-Docling        │
        │ Document Processor         │
        │ (All formats unified)      │
        └─────────────┬──────────────┘
                      │
        ┌─────────────▼──────────────┐
        │  Embedding Service         │
        │  with pgvector             │
        └─────────────┬──────────────┘
                      │
        ┌─────────────▼──────────────┐
        │   pgvector Database        │
        │  (PostgreSQL + Vector)     │
        └────────────────────────────┘
```

### Database Schema

#### Reports Table
```sql
- id (UUID)
- filename
- file_path
- file_size_bytes
- file_type (pdf, xlsx, csv, json, docx)
- upload_date
- processing_status (processing, indexed, ready, failed)
- embedding_provider (azure, google, aws)
- embedding_model
- chunks_created
```

#### Chunks Table (with Vector Embeddings)
```sql
- id (UUID)
- report_id (FK)
- chunk_text
- chunk_index
- page_number
- section_type
- embedding (Vector 1536)
- embedding_model
- created_at
```

#### Audit Logs Table
```sql
- id (UUID)
- query_text
- query_type (chat, bi_bot, embedding)
- provider_name (azure, google, aws)
- provider_model
- response_length
- processing_time_ms
- success
- error_message
- chunks_used
- session_id
- created_at
```

#### Conversation Messages Table
```sql
- id (UUID)
- session_id
- message_index
- role (user, assistant)
- content
- provider_used
- model_used
- chunks_referenced (JSON array)
- created_at
```

## Deployment

### Quick Start with Docker Compose

```bash
# 1. Clone repository and navigate to directory
cd /path/to/financial-report-analyzer

# 2. Configure environment
cp .env .env.local
# Edit .env.local with your settings

# 3. Start services
docker-compose up -d

# 4. Access application
# - Gradio UI: http://localhost:7860
# - PostgreSQL: localhost:5432
# - Nginx Proxy: http://localhost (or https://localhost with SSL)
```

### Environment Configuration

Edit `.env` file with:

```env
# Database
DATABASE_URL=postgresql://finuser:your_password@postgres:5432/financial_reports
DB_PASSWORD=your_password

# Application
APP_PORT=7860
DEBUG=False
LOG_LEVEL=INFO

# File Upload
MAX_FILE_SIZE_MB=50
ALLOWED_EXTENSIONS=pdf,xlsx,csv,json,docx

# Vector Database
EMBEDDING_DIMENSION=1536
SIMILARITY_THRESHOLD=0.7
MAX_CHUNKS_PER_QUERY=10
```

### Manual Installation

```bash
# 1. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup database (if using external PostgreSQL)
export DATABASE_URL=postgresql://user:pass@host:5432/db
python -c "from models import init_db; init_db(os.getenv('DATABASE_URL'))"

# 4. Run application
python main.py

# 5. Open browser to http://localhost:7860
```

## Usage Guide

### 1️⃣ Configure Credentials

1. Go to **🔐 Credentials Tab**
2. Select your AI provider:
   - **Azure OpenAI**: Provide API Key, Endpoint, Model name (gpt-4, gpt-35-turbo, gpt-4-turbo)
   - **Google Gemini**: Provide API Key, Model name (gemini-pro, gemini-pro-vision)
   - **AWS Bedrock**: Provide Access Key, Secret Key, Region, Model (Claude 3 models)
3. Click **"Validate & Initialize Multi-Agent System"**
4. Wait for confirmation: "✅ Multi-Agent System: Initialized"
5. Credentials are stored in memory for the current session only (never persisted)

### 2️⃣ Upload Financial Reports

1. Go to **📄 Reports Tab**
2. Upload PDF, Excel, CSV, JSON, or DOCX files
3. **For password-protected files**: Enter password in the password field
4. Click **"📤 Upload Report"**
5. System automatically:
   - Extracts text and tables using IBM Docling
   - Chunks document into semantic segments (1000 chars, 200 overlap)
   - Generates embeddings using selected provider
   - Stores in pgvector database with metadata
6. Monitor progress: You'll see "✅ Report uploaded successfully!" with details

### 3️⃣ Query Reports via Chat (Multi-Agent)

1. Go to **💬 Chat (Multi-Agent) Tab**
2. **Ensure "Use Multi-Agent System" is checked** (recommended)
3. Ask natural language questions about your reports
4. System automatically:
   - Analyzes your query intent
   - Routes to the appropriate specialist agent
   - Executes agent tools to gather information
   - Generates intelligent response with context
   - Displays response with agent attribution
5. Conversation history is maintained across queries
6. Each response shows which agent handled it

**Example Queries:**
- *"What was the revenue in Q3 2024?"* → Routed to Document Agent
- *"Calculate the current ratio"* → Routed to Metrics Agent
- *"Show me the revenue trend over the last 4 quarters"* → Routed to Trend Agent
- *"Compare profit margins year-over-year"* → May use multiple agents

### 4️⃣ Configure Agents (Optional)

Agents can be configured via `config/agents.json`:

```json
{
  "document_analysis": {
    "enabled": true,
    "max_iterations": 10,
    "temperature": 0.7
  },
  "financial_metrics": {
    "enabled": true,
    "max_iterations": 8,
    "temperature": 0.5
  },
  "trend_analysis": {
    "enabled": true,
    "max_iterations": 8,
    "temperature": 0.6
  }
}
```

## 🔧 Configuration

### Environment Variables

Key environment variables in `.env`:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/financial_reports

# Application
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
MAX_FILE_SIZE_MB=50
UPLOAD_DIR=uploads
APP_PORT=7860

# Vector Search
EMBEDDING_DIMENSION=1536
SIMILARITY_THRESHOLD=0.7
MAX_CHUNKS_PER_QUERY=10
```

### Agent Configuration

Create `config/agents.json` to customize agent behavior:

```json
{
  "document_analysis": {
    "name": "document_analysis",
    "description": "Analyzes financial documents",
    "enabled": true,
    "max_iterations": 10,
    "temperature": 0.7
  },
  "financial_metrics": {
    "enabled": true,
    "max_iterations": 8,
    "temperature": 0.5
  },
  "trend_analysis": {
    "enabled": true,
    "max_iterations": 8,
    "temperature": 0.6
  }
}
```

## API Reference

### Multi-Agent System

#### `AgentOrchestrator`
```python
from agents import AgentOrchestrator

# Initialize orchestrator
orchestrator = AgentOrchestrator(
    llm=llm,
    embedding_service=embedding_service,
    session_maker=session_maker
)

# Execute query with automatic routing
result = orchestrator.execute_query(
    query="What was the revenue in Q3?",
    context={},
    use_routing=True
)

# Execute with multiple agents
result = orchestrator.execute_multi_agent_query(
    query="Analyze revenue and calculate metrics",
    agent_names=["document_analysis", "financial_metrics"]
)

# Get conversation history
history = orchestrator.get_conversation_history()

# Reset conversation
orchestrator.reset_conversation()
```

#### `BaseFinancialAgent`
```python
from agents.base_agent import BaseFinancialAgent

# All agents inherit from this base class
class CustomAgent(BaseFinancialAgent):
    def get_system_prompt(self) -> str:
        return "Your custom system prompt"
    
    def _create_tools(self) -> List[FunctionTool]:
        # Define agent-specific tools
        pass
```

### Multi-Provider LLM Classes

#### `ProviderCredentials`
```python
@dataclass
class ProviderCredentials:
    provider: str  # "azure", "google", "aws"
    credentials: Dict[str, str]
    model: str
```

#### `BaseLLMProvider`
```python
# Validate credentials
provider.validate_credentials() -> bool

# Generate embedding
provider.generate_embedding(text: str) -> List[float]

# Chat response
provider.generate_chat_response(
    query: str,
    context: str,
    system_prompt: Optional[str] = None,
    conversation_history: Optional[List[Dict]] = None
) -> LLMResponse

# BI Analysis
provider.generate_bi_analysis(
    analysis_type: str,
    data_context: str,
    parameters: Dict[str, Any]
) -> LLMResponse
```

#### `LLMProviderFactory`
```python
# Create provider from credentials
provider = LLMProviderFactory.create_provider(credentials)

# Get supported providers
providers = LLMProviderFactory.get_supported_providers()
# Returns: ["azure", "google", "aws"]
```

### Document Processing

#### `DocumentProcessor`
```python
processor = DocumentProcessor(file_path, file_type)
full_text, chunks = processor.process()

# Returns:
# - full_text: Complete extracted text
# - chunks: List[Dict] with keys: text, chunk_index, section_type
```

### Embedding Service

#### `EmbeddingService`
```python
service = EmbeddingService(session)

# Store embeddings
stored = service.store_embeddings(
    report_id, chunks, embeddings, provider, model
)

# Semantic search
results = service.semantic_search(
    query_embedding,
    top_k=10,
    similarity_threshold=0.7
)

# Hybrid search
results = service.hybrid_search(
    query_embedding,
    keyword_filters={"report_ids": [...]}
)

# Re-index with different provider
service.reindex_report(
    report_id, chunks, embeddings, new_provider, new_model
)
```

### Audit Service

#### `AuditService`
```python
service = AuditService(session)

# Log query
log_id = service.log_query(
    query_text, query_type, provider_name, provider_model,
    report_id=None, chunks_used=0, processing_time_ms=None,
    response_length=None, success=True, error_message=None
)

# Get conversation history
history = service.get_conversation_history(session_id)

# Get audit logs
logs = service.get_audit_logs(
    limit=100,
    query_type=None,
    provider_name=None,
    report_id=None
)

# Get provider usage stats
stats = service.get_provider_usage_stats()

# Delete old logs (compliance)
deleted = service.delete_old_logs(days_to_keep=90)
```

## Security & Compliance

### 🔒 Credential Security

- **No Storage**: Credentials are NEVER stored in database
- **Runtime Only**: Entered via UI, used in memory, discarded after session
- **No Logs**: Credentials never written to logs
- **In-Memory Only**: Stored in Python session object

### 📝 Audit Trail

Every query logs:
- Query text (not sensitive credentials)
- Provider used
- Model used
- Processing time
- Success/failure status
- Number of chunks used
- Session ID for correlation

### 🔐 Database Security

```bash
# Enable SSL for PostgreSQL connection
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require

# Use pgvector indexes for security (proper query planning)
CREATE INDEX ON chunks USING hnsw (embedding vector_cosine_ops);

# Column-level encryption available (application-side for sensitive data)
```

### 🌐 Network Security

- Nginx reverse proxy with:
  - SSL/TLS termination
  - Rate limiting (10 req/s general, 100 req/s API)
  - Security headers (HSTS, CSP, X-Frame-Options)
  - Client IP logging
  - Request/response compression

## Performance Optimization

### Vector Search Performance

```sql
-- Create HNSW index for fast approximate search
CREATE INDEX ON chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- For exact search (slower but accurate)
CREATE INDEX ON chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

### Database Optimization

```python
# Connection pooling
from sqlalchemy.pool import QueuePool
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
)

# Query optimization
from sqlalchemy import and_
query = session.query(Chunk).filter(
    and_(
        Chunk.report_id.in_(report_ids),
        Chunk.embedding != None,
    )
).all()
```

## 🐛 Troubleshooting

### Multi-Agent System Issues

#### 1. "Multi-Agent System: Not initialized"
**Symptom**: Chat returns this error message
**Solution**: 
- Go to Credentials tab
- Validate credentials again
- Click "Validate & Initialize Multi-Agent System"
- Check logs/app.log for detailed errors

#### 2. "Import llama_index errors"
**Symptom**: Application fails to start with import errors
**Solution**:
```bash
pip install -r requirements.txt --upgrade
pip install llama-index llama-index-core --upgrade
```

#### 3. Agents not responding or timing out
**Symptom**: Queries hang or timeout
**Solution**:
- Check `logs/agents.log` for detailed error messages
- Reduce `max_iterations` in `config/agents.json`
- Check API rate limits for your provider
- Verify network connectivity to LLM provider

#### 4. Wrong agent handling query
**Symptom**: Query routed to incorrect agent
**Solution**:
- Query router uses keyword matching
- Use more specific keywords in your query
- Check `logs/agents.log` to see routing decisions
- You can disable routing by unchecking "Use Multi-Agent System"

### Common Issues

#### 5. Connection to Database Failed
```bash
# Check PostgreSQL container is running
docker-compose ps

# Check connection string
echo $DATABASE_URL

# Test connection manually
psql postgresql://finuser:pass@localhost:5432/financial_reports
```

#### 6. Embedding Generation Fails
- Verify credentials are entered correctly
- Check API quotas/limits for provider
- Ensure text is not empty
- Check network connectivity to API endpoint

#### 7. Semantic Search Returns No Results
- Lower `SIMILARITY_THRESHOLD` in .env
- Ensure reports are indexed (`processing_status = ready`)
- Check that embeddings were generated successfully
- Verify query is related to document content

#### 8. Out of Memory
- Reduce `MAX_CHUNKS_PER_QUERY`
- Reduce `EMBEDDING_DIMENSION` (though this reduces accuracy)
- Use smaller batch sizes for embedding generation
- Consider horizontal scaling with load balancer

## Scaling Recommendations

### Horizontal Scaling

```yaml
# docker-compose.yml with load balancing
services:
  app1:
    image: financial-analyzer:latest
    environment:
      - APP_INSTANCE=1
  
  app2:
    image: financial-analyzer:latest
    environment:
      - APP_INSTANCE=2
  
  loadbalancer:
    image: nginx:latest
    volumes:
      - ./nginx-lb.conf:/etc/nginx/nginx.conf
    ports:
      - "80:80"
    depends_on:
      - app1
      - app2
```

### Database Scaling

```bash
# Connection pooling
pgBouncer:
  pool_mode: transaction
  max_client_conn: 1000
  default_pool_size: 25

# Read replicas for reporting
PostgreSQL replication:
  primary:
    - Handles writes
  replicas:
    - Handle read queries from audit logs
    - Report generation
```

## Cost Optimization

### Provider Comparison

| Provider | Embedding Model | Cost/1M tokens | Latency |
|----------|-----------------|----------------|---------|
| Azure AI | text-embedding-3-small | $0.02 | ~100ms |
| Google Gemini | embedding-001 | $0.0001 | ~200ms |
| AWS Bedrock | Titan Embed | $0.10/1M | ~150ms |

### Cost-Saving Tips

1. **Batch Embeddings**: Process multiple documents at once
2. **Cache Results**: Reuse embeddings for identical queries
3. **Provider Fallback**: Use cheaper provider as primary, expensive as backup
4. **Selective Indexing**: Only index relevant documents
5. **Compression**: Compress embeddings before storage

## 📝 Logging & Monitoring

### Log Files

All logs are in the `logs/` directory:

- **app.log**: Complete application log (all levels)
- **error.log**: Errors and critical issues only
- **agents.log**: Agent-specific operations and decisions

### Monitoring Commands

```bash
# Real-time app monitoring
tail -f logs/app.log

# Monitor errors only
tail -f logs/error.log

# Monitor agent decisions
tail -f logs/agents.log

# Search for specific patterns
grep "ERROR" logs/app.log
grep "agent.document" logs/agents.log | tail -20
grep "processing_time" logs/app.log

# Count errors in last hour
grep "ERROR" logs/app.log | grep "$(date +%Y-%m-%d\ %H)" | wc -l
```

### Debug Mode

Enable verbose logging:

```bash
export LOG_LEVEL=DEBUG
python main.py
```

## 🤝 Contributing

### Adding New Agents

1. Create new agent file in `agents/` directory
2. Inherit from `BaseFinancialAgent`
3. Implement required methods:

```python
from agents.base_agent import BaseFinancialAgent
from llama_index.core.tools import FunctionTool

class MyCustomAgent(BaseFinancialAgent):
    def __init__(self, llm):
        tools = self._create_tools()
        super().__init__(
            name="my_custom_agent",
            description="Does custom analysis",
            llm=llm,
            tools=tools
        )
    
    def _create_tools(self):
        def my_tool(param: str) -> str:
            """Tool description."""
            return f"Result: {param}"
        
        return [FunctionTool.from_defaults(fn=my_tool)]
    
    def get_system_prompt(self) -> str:
        return "You are a custom agent..."
```

4. Register agent in `AgentOrchestrator`
5. Add to agent configuration file
6. Update query router keywords

## Production Checklist

### Infrastructure
- [ ] SSL certificates configured for nginx
- [ ] Database backups automated (daily)
- [ ] Monitoring setup (Prometheus, Grafana)
- [ ] Log aggregation (ELK, Datadog, CloudWatch)
- [ ] Alerting for errors and performance degradation
- [ ] Load testing completed (at least 10 concurrent users)
- [ ] Disaster recovery plan documented

### Security
- [ ] Credentials rotation policy implemented
- [ ] Audit logs retention policy set (e.g., 1 year)
- [ ] Rate limiting tuned for expected load
- [ ] Database indexes verified for production
- [ ] Connection pooling configured
- [ ] Graceful shutdown procedures tested

### Multi-Agent System
- [ ] Agent configurations reviewed and optimized
- [ ] Agent performance benchmarked
- [ ] Query routing accuracy tested
- [ ] Agent-specific monitoring configured
- [ ] Agent error handling tested
- [ ] Agent iteration limits tuned

## 📚 Additional Documentation

- **[MIGRATION_SUMMARY.md](MIGRATION_SUMMARY.md)**: Detailed migration guide to v2.0
- **[ARCHITECTURE.md](ARCHITECTURE.md)**: System architecture deep dive
- **[INDEX.md](INDEX.md)**: Code navigation and file structure
- **Agent Source Code**: See `agents/` directory for individual agents

## 🙏 Acknowledgments

- **LlamaIndex**: Multi-agent framework and orchestration
- **IBM Docling**: Advanced document processing
- **pgvector**: High-performance vector similarity search
- **Gradio**: Interactive web interface
- **OpenAI, Google, AWS**: LLM provider APIs

## Support & Contribution

For issues, feature requests, or contributions:

1. Check existing documentation
2. Review logs in `logs/` directory
3. Check `logs/agents.log` for agent-specific issues
4. Review audit logs for errors
5. Check provider API quotas
6. Verify environment configuration
7. Test with DEBUG logging enabled
8. Contact system administrator

## Technology Stack

- **Frontend**: Gradio 4.44
- **AI Framework**: LlamaIndex 0.10
- **Backend**: Python 3.10+
- **Database**: PostgreSQL 16 + pgvector
- **LLM Providers**: Azure OpenAI, Google Gemini, AWS Bedrock
- **Document Processing**: IBM Docling (Granite)
- **Logging**: Python logging with custom formatters
- **Orchestration**: Docker Compose

---

**Version**: 2.0.0 (Multi-Agent)  
**Last Updated**: November 2025  
**License**: Proprietary