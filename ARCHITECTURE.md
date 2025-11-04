# Architecture & Design Document

## System Overview

The Financial Report Analysis System is a containerized, multi-provider AI application for semantic analysis of financial documents. It follows a **Retrieval-Augmented Generation (RAG)** pattern with runtime credential management.

## Core Design Principles

### 🔒 Security First
- **Zero Credential Storage**: No passwords/keys ever persisted
- **Runtime-Only Credentials**: Stored in memory, discarded after session
- **Audit Everything**: Every query logged with provider and timestamp
- **No External Data**: All context from uploaded files only

### 📈 Scalability
- **Horizontal Scaling**: Multiple app instances behind load balancer
- **Vector Database**: pgvector with HNSW indexing for fast search
- **Connection Pooling**: Reuse database connections efficiently
- **Async Operations**: Batch processing for large document sets

### 🛡️ Reliability
- **Multi-Provider Fallback**: Switch providers if one fails
- **Error Handling**: Graceful degradation with informative messages
- **Health Checks**: Container health endpoints for monitoring
- **Data Persistence**: PostgreSQL with backup strategy

## Architecture Layers

### 1. Presentation Layer (Gradio UI)
- **Single-Page Application**: Gradio Blocks
- **Four Main Tabs**:
  - Credentials: Input AI provider keys (not stored)
  - Reports: Upload and manage documents
  - Chat: Natural language queries
  - BI Bot: Pre-built financial analyses
- **Real-time Feedback**: Status updates, progress indicators
- **Responsive Design**: Works on desktop/tablet

### 2. Application Layer (Python Services)

#### LLM Provider Abstraction
```
┌─────────────────────────────┐
│  Multi-Provider Factory     │
├─────────────────────────────┤
│ ┌─────────┐ ┌────────┐ ┌──┐│
│ │ Azure   │ │ Google │ │AWS││
│ │ OpenAI  │ │ Gemini │ │BR││
│ └─────────┘ └────────┘ └──┘│
└─────────────────────────────┘
```

**Features**:
- Unified interface for all providers
- Automatic credential validation
- Provider-specific error handling
- Embedding generation
- Chat response generation
- BI analysis generation

#### Document Processing Pipeline
```
Upload → Validate → Extract → Chunk → Embed → Store
  ↓        ↓         ↓        ↓       ↓      ↓
 File    Format    Text     1000    Vector  DB
        Check     Tables     char
```

**Processors**:
- PDF: Uses PyPDF2 + pdfplumber for text and tables
- Excel: Pandas for structured data extraction
- CSV/JSON: Direct parsing
- DOCX: python-docx for text and tables

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

#### Audit Service
```
┌──────────────────────────┐
│   Compliance & Logging   │
├──────────────────────────┤
│ • Query tracking         │
│ • Provider usage stats   │
│ • Conversation history   │
│ • Retention policies     │
└──────────────────────────┘
```

**Logging**:
- Every query: text, provider, model, latency, success
- Every embedding: chunks processed, dimensions, provider
- Usage stats: per-provider aggregation
- Session tracking: conversation correlation

### 3. Data Layer (PostgreSQL + pgvector)

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

### 4. Infrastructure Layer (Docker & Networking)

#### Container Architecture
```
┌─────────────────────────────┐
│     Docker Host Network     │
├─────────────────────────────┤
│  ┌─────────┐ ┌────────┐    │
│  │ Gradio  │ │ Nginx  │    │
│  │ App:7860│ │:80/:443│    │
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

### Chat Query Flow
```
1. User enters question
   ↓
2. Question → Generate embedding (using LLM provider)
   ↓
3. Embedding → Search pgvector for similar chunks
   ↓
4. Top-K chunks → Build context window
   ↓
5. Context + Question → Send to LLM provider
   ↓
6. LLM → Generate response with citations
   ↓
7. Log query to audit trail
   ↓
8. Response → Display in UI with sources
```

### Report Upload Flow
```
1. User selects file
   ↓
2. Validate file type and size
   ↓
3. Extract text and tables
   ↓
4. Split into semantic chunks (1000 char, 200 overlap)
   ↓
5. Generate embeddings for each chunk
   ↓
6. Store embeddings + metadata in PostgreSQL
   ↓
7. Update report status to "ready"
   ↓
8. Log embedding generation to audit trail
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
└────────────┬────────────┘
             │ (In-memory only)
             ↓
         ┌────────────┐
         │ LLM Calls  │ → Generate embeddings
         │            │ → Chat responses
         └────────────┘
             │ (Session ends)
             ↓
        Credentials discarded
```

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
    ├── App Instance 1 (port 7860)
    ├── App Instance 2 (port 7861)
    ├── App Instance 3 (port 7862)
    └── App Instance N (port 786N)

All instances → Same PostgreSQL (connection pooling)
```

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
└── SQLite or local PostgreSQL
```

### Staging
```
Cloud VM (e.g., EC2, GCP VM)
├── Docker Swarm or Kubernetes
├── Managed PostgreSQL (AWS RDS, Azure Database)
├── SSL with Let's Encrypt
└── Monitoring + logging stack
```

### Production
```
Kubernetes Cluster (EKS/AKS/GKE)
├── Multiple Gradio pods (auto-scaling)
├── Managed database (RDS, Azure, Cloud SQL)
├── Managed Redis (for caching)
├── Load balancer (ALB, Azure LB, GCP LB)
├── CDN (CloudFront, Azure CDN, Cloud CDN)
├── Monitoring (Prometheus, Datadog)
├── Logging (ELK, Splunk, CloudWatch)
└── Backup & DR strategy
```

## Technology Stack Justification

| Component | Choice | Why |
|-----------|--------|-----|
| Frontend | Gradio | Easy UI, no JS needed, perfect for ML apps |
| Backend | Python | Simple, LLM SDKs available, rapid dev |
| Database | PostgreSQL | Mature, pgvector support, reliable |
| Vector Store | pgvector | Integrated with PostgreSQL, easy deployment |
| LLM Providers | Multiple | Avoid vendor lock-in, cost optimization |
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

### AI Provider Costs (1000 queries/day)
```
Embeddings (1000 docs, 1000 tokens):    $2 (Azure)
Chat responses (avg 500 tokens):        $5 (Azure)

Alternative with Google Gemini:        $1 (embedding-001)
Alternative with AWS Bedrock:          $10 (Claude)
```

### Total Monthly Estimate
```
Infrastructure + AI:  $375 + $10 = $385/month (Azure)
                      $375 + $5 = $380/month (Google)
                      $375 + $20 = $395/month (AWS)
```

## Future Enhancements

1. **Multi-User Support**: User authentication, separate audit trails
2. **Custom Models**: Fine-tuning on organization-specific data
3. **Real-time Collaboration**: Multiple users querying same reports
4. **Advanced Visualizations**: Charts, dashboards, trend analysis
5. **Mobile App**: React Native/Flutter client
6. **Compliance Automation**: GDPR/HIPAA/SOC2 audit reports
7. **API Gateway**: REST/GraphQL API for third-party integration
8. **Agent Framework**: AutoGPT-style autonomous analysis
9. **Knowledge Base**: Persistent context across users/organizations
10. **Predictive Analytics**: Forecasting based on historical data

---

**Document Version**: 1.0
**Last Updated**: October 2025
**Architecture Owner**: Platform Engineering Team