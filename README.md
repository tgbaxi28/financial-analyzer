# Financial Report Analysis System - Complete Documentation

## Overview

The Financial Report Analysis System is an AI-powered platform for analyzing consolidated financial reports using a multi-provider LLM architecture. Users can upload reports, query them using natural language, and run pre-built financial analyses - all with **no credential storage** (credentials are entered at runtime).

## Key Features

### ✨ Core Capabilities

- **Multi-Provider LLM Support**: Azure AI, Google Gemini, AWS Bedrock
- **Unified Document Processing**: IBM Granite-Docling for consistent extraction across all formats
- **Password-Protected Files**: Support for encrypted PDFs and other password-protected documents
- **Semantic Search**: pgvector-based vector database for intelligent document retrieval
- **File-in-Context Only**: All responses based solely on uploaded documents
- **Runtime Credentials**: No storage of sensitive credentials
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
        │  Document Processing       │
        │  & Embedding Service       │
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

1. Go to **Credentials Tab**
2. Select your AI provider:
   - **Azure AI**: Provide API Key, Endpoint, Model name
   - **Google Gemini**: Provide API Key, Model name
   - **AWS Bedrock**: Provide Access Key, Secret Key, Region, Model
3. Click **Validate & Save Credentials**
4. Credentials are stored in memory for the current session only

### 2️⃣ Upload Financial Reports

1. Go to **Reports Tab**
2. Upload PDF, Excel, CSV, JSON, or DOCX files
3. System automatically:
   - Extracts text and tables
   - Chunks document into semantic segments
   - Generates embeddings using selected provider
   - Stores in pgvector database
4. Monitor progress in status indicator

### 3️⃣ Query Reports via Chat

1. Go to **Chat Tab**
2. Ask natural language questions about your reports
3. System automatically:
   - Generates query embedding
   - Searches for relevant document sections
   - Generates response using LLM with context
   - Displays source citations
4. Maintain conversation history across queries

### 4️⃣ Run BI Analytics

1. Go to **BI Bot Tab**
2. Select analysis type:
   - **Variance Analysis**: Identify deviations from expectations
   - **Trend Analysis**: Track metrics over time
   - **Ratio Analysis**: Calculate financial ratios
3. System generates analysis based on uploaded reports

## API Reference

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

## Troubleshooting

### Common Issues

#### 1. Connection to Database Failed
```bash
# Check PostgreSQL container is running
docker-compose ps

# Check connection string
echo $DATABASE_URL

# Test connection manually
psql postgresql://finuser:pass@localhost:5432/financial_reports
```

#### 2. Embedding Generation Fails
- Verify credentials are entered correctly
- Check API quotas/limits for provider
- Ensure text is not empty
- Check network connectivity to API endpoint

#### 3. Semantic Search Returns No Results
- Lower `SIMILARITY_THRESHOLD` in .env
- Ensure reports are indexed (`processing_status = ready`)
- Check that embeddings were generated successfully
- Verify query is related to document content

#### 4. Out of Memory
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

## Production Checklist

- [ ] SSL certificates configured for nginx
- [ ] Database backups automated (daily)
- [ ] Monitoring setup (Prometheus, Grafana)
- [ ] Log aggregation (ELK, Datadog)
- [ ] Alerting for errors and performance degradation
- [ ] Load testing completed (at least 10 concurrent users)
- [ ] Disaster recovery plan documented
- [ ] Credentials rotation policy implemented
- [ ] Audit logs retention policy set (e.g., 1 year)
- [ ] Rate limiting tuned for expected load
- [ ] Database indexes verified for production
- [ ] Connection pooling configured
- [ ] Graceful shutdown procedures tested

## Support & Contribution

For issues, feature requests, or contributions:

1. Check existing documentation
2. Review audit logs for errors
3. Check provider API quotas
4. Verify environment configuration
5. Contact system administrator

---

**Last Updated**: October 2025
**Version**: 1.0
**License**: Proprietary