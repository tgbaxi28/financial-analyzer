# 💰 Financial Analyzer

AI-powered financial document analysis and portfolio tracking system with comprehensive PII/PHI protection.

## 🌟 Features

### Core Capabilities
- **📧 Magic Link Authentication** - Passwordless login via email (AWS SES)
- **👨‍👩‍👧‍👦 Family Member Management** - Track finances for entire family
- **📄 Document Processing** - Support for PDF, Excel, CSV, Word documents
- **🔒 Password Protection** - Handle password-protected PDFs
- **🛡️ PII/PHI Protection** - Microsoft Presidio for advanced data anonymization
- **🤖 Multi-LLM Support** - OpenAI, Azure OpenAI, AWS Bedrock, Google Gemini
- **💬 RAG-based Q&A** - Chat with your financial documents
- **📊 WrenAI Dashboard** - Beautiful analytics and visualizations
- **🔍 Vector Search** - Qdrant for semantic document search
- **🔐 Multi-tenant Architecture** - Complete data isolation per user

### Security & Privacy
- ✅ Zero storage of API keys (session-only)
- ✅ Automatic PII/PHI detection and anonymization
- ✅ Temporary file storage (deleted after chunking)
- ✅ User-isolated vector collections
- ✅ Comprehensive audit logging
- ✅ HTTPS/SSL support

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Gradio UI (Port 7860)                  │
│  ┌──────────┬───────────┬──────────┬─────────────────────┐ │
│  │   Auth   │  Upload   │  Chat    │  WrenAI Dashboard   │ │
│  └──────────┴───────────┴──────────┴─────────────────────┘ │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                 FastAPI Backend (Port 8000)                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Auth Service │ Family Mgmt │ Document Processor     │  │
│  │  RAG Service  │ LLM Providers │ PII Service          │  │
│  └──────────────────────────────────────────────────────┘  │
└────────┬──────────────┬──────────────┬─────────────────────┘
         │              │              │
    ┌────▼────┐    ┌───▼────┐    ┌───▼──────┐
    │PostgreSQL│   │ Qdrant │    │  WrenAI  │
    │(Port 5432)│  │(6333)  │    │ (Port 3000)│
    └──────────┘   └────────┘    └──────────┘
```

## 📋 Prerequisites

- Docker & Docker Compose
- AWS Account (for SES email service)
- AI Provider API Keys (OpenAI, Azure OpenAI, AWS Bedrock, or Google Gemini)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
cd /Users/tanmay/Documents/Simform\ Accelerators/financial-analyzer

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 2. Configure Environment Variables

Edit `.env` file:

```env
# Database
DATABASE_URL=postgresql://finuser:securepassword@postgres:5432/financial_analyzer
POSTGRES_USER=finuser
POSTGRES_PASSWORD=securepassword
POSTGRES_DB=financial_analyzer

# Qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# AWS SES (for magic link emails)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
SES_SENDER_EMAIL=noreply@yourdomain.com

# Application
SECRET_KEY=generate-a-secure-random-key-min-32-chars
APP_URL=http://localhost:8000

# WrenAI
WRENAI_HOST=wrenai
WRENAI_PORT=3000
```

### 3. Start Services

```bash
# Build and start all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Verify all services are running
docker-compose ps
```

### 4. Access Applications

- **Gradio UI**: http://localhost:7860
- **FastAPI Backend**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **WrenAI Dashboard**: http://localhost:3000
- **Qdrant UI**: http://localhost:6333/dashboard

## 📖 User Guide

### Registration & Login

1. **Register**:
   - Go to Authentication tab
   - Enter email, first name, last name
   - Click "Register"
   - Check your email for magic link

2. **Login**:
   - Go to Authentication tab
   - Enter your email
   - Click "Send Magic Link"
   - Check your email
   - Copy token from email
   - Paste token and click "Verify & Login"

### Upload Documents

1. Go to "Upload Documents" tab
2. Click "Select Document"
3. Choose PDF, Excel, CSV, or Word file
4. Select upload for "user" or "family_member"
5. If PDF is password-protected, enter password
6. Click "Upload & Process"
7. Wait for processing to complete

**Supported Formats:**
- PDF (including password-protected)
- Excel (XLSX, XLS)
- CSV
- Word (DOCX)

### Chat with Documents

1. Go to "AI Chat" tab
2. Configure AI Provider:
   - Select provider (OpenAI, Azure OpenAI, AWS Bedrock, Google Gemini)
   - Enter your API key (NOT stored, session-only)
   - For Azure: Enter endpoint URL
   - Optionally specify model name
3. Ask questions about your documents
4. View responses with source citations

**Example Questions:**
- "What is my total investment in mutual funds?"
- "Show me my bank statement summary for last month"
- "What are my top 5 stock holdings?"
- "Calculate my total expenses in the last quarter"

### View Analytics Dashboard

1. Go to "Dashboard" tab
2. Access WrenAI for:
   - Spend analysis
   - Portfolio tracking
   - Performance metrics
   - Custom dashboards

## 🏗️ Project Structure

```
financial-analyzer/
├── app/
│   ├── api/
│   │   ├── auth.py              # Authentication endpoints
│   │   ├── family.py            # Family member management
│   │   └── documents.py         # Document upload & chat
│   ├── services/
│   │   ├── auth_service.py      # Authentication logic
│   │   ├── email_service.py     # AWS SES integration
│   │   ├── document_processor.py # Document parsing
│   │   ├── pii_service.py       # Microsoft Presidio PII/PHI
│   │   ├── qdrant_service.py    # Vector database
│   │   ├── llm_providers.py     # Multi-LLM abstraction
│   │   └── rag_service.py       # RAG query system
│   ├── utils/
│   │   ├── logger.py            # Logging configuration
│   │   └── security.py          # Security utilities
│   ├── config.py                # Configuration
│   ├── database.py              # Database connection
│   ├── models.py                # SQLAlchemy models
│   ├── schemas.py               # Pydantic schemas
│   ├── dependencies.py          # FastAPI dependencies
│   └── main.py                  # FastAPI application
├── gradio_app.py                # Gradio UI
├── docker-compose.yml           # Docker orchestration
├── Dockerfile.backend           # Backend container
├── Dockerfile.gradio            # Gradio container
├── init.sql                     # Database initialization
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## 🔧 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Request magic link
- `POST /auth/verify` - Verify magic link token
- `GET /auth/me` - Get current user info

### Family Members
- `POST /family` - Create family member
- `GET /family` - List family members
- `GET /family/{id}` - Get family member
- `PATCH /family/{id}` - Update family member
- `DELETE /family/{id}` - Delete family member

### Documents
- `POST /documents` - Upload document
- `GET /documents` - List documents
- `GET /documents/{id}` - Get document
- `DELETE /documents/{id}` - Delete document
- `POST /documents/chat` - Chat with documents (RAG)

### Health
- `GET /health` - Health check

## 🔐 Security Features

### PII/PHI Protection (Microsoft Presidio)

The system automatically detects and anonymizes:
- Person names
- Email addresses
- Phone numbers
- Addresses and locations
- Dates and times
- Credit card numbers
- Bank account numbers (IBAN, US format)
- Social Security Numbers
- Driver's license numbers
- Passport numbers
- Medical license numbers
- IP addresses
- Cryptocurrency addresses

### Data Isolation

- **Per-user Qdrant collections**: `financial_docs_user_{user_id}`
- **Per-family-member collections**: `financial_docs_family_member_{id}`
- **Database row-level filtering** by owner_id and owner_type

### Session Security

- JWT tokens with configurable expiration
- Magic link tokens expire in 15 minutes
- API keys never stored in database
- All sessions tracked with last activity

## 🧪 Development

### Running Locally (Without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Download spaCy model for Presidio
python -m spacy download en_core_web_lg

# Start PostgreSQL and Qdrant separately
# Update .env with local connection strings

# Run migrations (if using Alembic)
# alembic upgrade head

# Start backend
uvicorn app.main:app --reload --port 8000

# Start Gradio (in another terminal)
python gradio_app.py
```

### Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/
```

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f backend
docker-compose logs -f gradio

# Log files (inside containers)
# - logs/app.log (all logs)
# - logs/error.log (errors only)
```

## 🐛 Troubleshooting

### Email Not Sending

1. Verify AWS SES credentials in `.env`
2. Check SES sender email is verified in AWS
3. Check AWS region is correct
4. Review backend logs: `docker-compose logs backend`

### Document Processing Failed

1. Check file format is supported
2. For password-protected PDFs, ensure password is correct
3. Check file size < 50MB
4. Review logs for specific error

### Qdrant Connection Error

1. Ensure Qdrant container is running: `docker-compose ps`
2. Check Qdrant logs: `docker-compose logs qdrant`
3. Verify port 6333 is not in use

### Database Connection Error

1. Check PostgreSQL container: `docker-compose ps`
2. Verify credentials in `.env`
3. Check logs: `docker-compose logs postgres`

## 📊 Database Schema

### Main Tables

- **users** - User accounts
- **family_members** - Family member profiles
- **magic_link_tokens** - Authentication tokens
- **sessions** - Active user sessions
- **documents** - Uploaded document metadata
- **audit_logs** - System audit trail
- **query_history** - Chat query history
- **financial_metrics** - Cached financial data for WrenAI

## 🚢 Deployment

### Production Considerations

1. **Environment Variables**:
   - Use strong, random SECRET_KEY
   - Secure database passwords
   - Configure proper AWS credentials

2. **HTTPS/SSL**:
   - Use reverse proxy (nginx, Caddy)
   - Enable SSL certificates
   - Update APP_URL to https://

3. **Scaling**:
   - Use managed PostgreSQL (RDS, Azure Database)
   - Use managed Qdrant (Qdrant Cloud)
   - Add Redis for session caching
   - Deploy backend with multiple replicas

4. **Monitoring**:
   - Setup logging aggregation
   - Configure health check alerts
   - Monitor Qdrant storage usage
   - Track API response times

## 📝 License

This project is proprietary software developed for Simform Accelerators.

## 🤝 Support

For issues or questions, please contact the development team.

---

**Built with ❤️ using FastAPI, Gradio, Qdrant, and WrenAI**
