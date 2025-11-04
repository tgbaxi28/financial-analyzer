# Financial Report Analyzer - Setup & Installation Guide

## Prerequisites

- Docker & Docker Compose (for containerized deployment)
- OR Python 3.11+ (for local development)
- PostgreSQL 14+ with pgvector extension (for external database setup)
- IBM Granite-Docling (automatically installed via requirements.txt)
- 2GB+ RAM, 10GB+ disk space

## What's Included

- **IBM Granite-Docling**: Unified document processing for PDF, Excel, CSV, JSON, DOCX
- **Password Support**: Handle encrypted PDF files securely
- **Multi-Provider LLM**: Azure AI, Google Gemini, AWS Bedrock

## Option 1: Docker Compose (Recommended)

### Quickest Setup

```bash
# 1. Navigate to project directory
cd /path/to/financial-report-analyzer

# 2. Create environment file from template
cp .env .env.local

# 3. Update .env.local with your settings (optional - defaults are provided)
# The system includes sensible defaults, but you can customize:
# - DB_PASSWORD: Database password
# - SECRET_KEY: For session management
# - MAX_FILE_SIZE_MB: Maximum upload size
# - SIMILARITY_THRESHOLD: Vector search sensitivity

# 4. Start all services
docker-compose up -d

# 5. Check service health
docker-compose ps

# 6. View logs
docker-compose logs -f app

# 7. Access the application
# Web UI: http://localhost:7860
# PostgreSQL: localhost:5432
# Database: financial_reports
```

### Troubleshooting Docker Setup

```bash
# Check if ports are available
lsof -i :7860
lsof -i :5432

# Check database connection
docker-compose exec postgres psql -U finuser -d financial_reports

# Rebuild containers (if code changes)
docker-compose build --no-cache
docker-compose up -d

# Full restart
docker-compose down
docker-compose up -d

# View specific service logs
docker-compose logs postgres
docker-compose logs app
```

## Option 2: Local Development

### Step-by-Step Setup

```bash
# 1. Create and activate virtual environment
python3.11 -m venv venv

# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate

# 2. Install dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# 3. Setup PostgreSQL (if not using Docker)
# macOS: brew install postgresql@16
# Linux: sudo apt-get install postgresql postgresql-contrib
# Windows: Download from postgresql.org

# Start PostgreSQL
# macOS: brew services start postgresql@16
# Linux: sudo systemctl start postgresql
# Windows: Use pgAdmin or services

# 4. Create database
createdb -U postgres financial_reports

# Create pgvector extension
psql -U postgres financial_reports -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 5. Set environment variables
export DATABASE_URL="postgresql://postgres:password@localhost:5432/financial_reports"
export SECRET_KEY="your_secret_key_here"

# Windows (PowerShell)
$env:DATABASE_URL="postgresql://postgres:password@localhost:5432/financial_reports"
$env:SECRET_KEY="your_secret_key_here"

# 6. Initialize database tables
python -c "from models import init_db; import os; init_db(os.getenv('DATABASE_URL'))"

# 7. Run application
python main.py

# 8. Access application
# Open browser to http://localhost:7860
```

### Setting Up PostgreSQL Locally

#### macOS (Homebrew)
```bash
# Install PostgreSQL
brew install postgresql@16

# Start service
brew services start postgresql@16

# Connect to PostgreSQL
psql -U postgres

# Create user and database
createuser finuser with password 'secure_password_123';
createdb -O finuser financial_reports;

# Enable pgvector
psql -U postgres financial_reports -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

#### Ubuntu/Debian
```bash
# Install PostgreSQL and pgvector
sudo apt update
sudo apt install postgresql postgresql-contrib postgresql-16-pgvector

# Start service
sudo systemctl start postgresql

# Create user and database
sudo -u postgres createuser finuser with password 'secure_password_123';
sudo -u postgres createdb -O finuser financial_reports;

# Enable pgvector
sudo -u postgres psql financial_reports -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

#### Windows
1. Download PostgreSQL installer from https://www.postgresql.org/download/windows/
2. Run installer, choose default options
3. Remember the password for postgres user
4. During installation, check "pgvector" if available
5. Open pgAdmin and:
   - Create user "finuser"
   - Create database "financial_reports"
   - Run: `CREATE EXTENSION IF NOT EXISTS vector;`

## Credential Setup

### Azure AI (OpenAI)

1. Go to https://portal.azure.com
2. Create Azure OpenAI resource
3. Get from resource page:
   - **API Key**: Settings → Keys and Endpoint → Key 1
   - **Endpoint**: https://YOUR_RESOURCE.openai.azure.com/
   - **Deployment Name**: Models → Deployments (usually "gpt-4" or "gpt-35-turbo")

### Google Gemini

1. Go to https://makersuite.google.com/app/apikey
2. Create/select project
3. Generate API key
4. Save the API key

### AWS Bedrock

1. Go to AWS Console → Bedrock
2. Set region (not all regions support Bedrock)
3. Create IAM user with Bedrock access:
   - Policy: `bedrock:InvokeModel`
4. Get credentials:
   - **Access Key ID**: IAM → Access Keys
   - **Secret Access Key**: (shown once at creation)
   - **Region**: Where you have Bedrock access

## Verification

### Test Database Connection

```bash
# Docker setup
docker-compose exec postgres psql -U finuser -d financial_reports -c "\dt"

# Local setup
psql -U finuser -d financial_reports -c "\dt"
```

Expected output shows tables:
- audit_logs
- chunks
- conversation_messages
- reports

### Test LLM Providers

```bash
# Python shell
python

# Try Azure
from llm_providers import LLMProviderFactory, ProviderCredentials
creds = ProviderCredentials(
    provider="azure",
    credentials={
        "api_key": "YOUR_KEY",
        "endpoint": "https://..."
    },
    model="gpt-4"
)
provider = LLMProviderFactory.create_provider(creds)
print(provider.validate_credentials())  # Should print True

# Try Google
creds = ProviderCredentials(
    provider="google",
    credentials={"api_key": "YOUR_KEY"},
    model="gemini-pro"
)
provider = LLMProviderFactory.create_provider(creds)
print(provider.validate_credentials())  # Should print True

# Try AWS
creds = ProviderCredentials(
    provider="aws",
    credentials={
        "access_key": "YOUR_KEY",
        "secret_key": "YOUR_SECRET",
        "region": "us-east-1"
    },
    model="anthropic.claude-3-sonnet-20240229-v1:0"
)
provider = LLMProviderFactory.create_provider(creds)
print(provider.validate_credentials())  # Should print True

# Exit
exit()
```

### Test File Upload

#### Regular Files
1. Prepare test financial report (PDF, Excel, CSV, JSON, or DOCX)
2. Open http://localhost:7860
3. Go to Credentials tab
4. Enter valid credentials for one provider
5. Click Validate & Save
6. Go to Reports tab
7. Upload test file
8. Check status - should show "✅ Report uploaded successfully!"

#### Password-Protected Files
1. Prepare a password-protected PDF
2. Open http://localhost:7860
3. Go to Credentials tab and validate credentials
4. Go to Reports tab
5. Select your protected PDF file
6. Enter the password in the "File Password" field
7. Click "📤 Upload Report"
8. Check status - should show "✅ Report uploaded successfully!"

**Note**: If you get a password error, verify:
- File is actually password-protected
- Password is entered correctly (case-sensitive)
- PDF is not using advanced security features (only standard encryption is supported)

## Document Processing with IBM Granite-Docling

The system uses IBM Granite-Docling for all document processing:

### Supported Formats
- **PDF**: Full text and table extraction, with password support
- **Excel (XLSX)**: All sheets processed, converted to structured text
- **CSV**: Automatic delimiter detection, formatted as tables
- **JSON**: Pretty-printed and structured for analysis
- **DOCX**: Paragraphs and embedded tables extracted

### How It Works
1. Docling converts document to structured format
2. Text is extracted with page/section information
3. Document is chunked into 1000-character segments with 200-char overlap
4. Each chunk is embedded using selected LLM provider
5. Embeddings stored in pgvector for semantic search

### Configuration
In `.env`:
```bash
# Chunk size for document splitting (characters)
CHUNK_SIZE=1000

# Overlap between chunks for context preservation
CHUNK_OVERLAP=200

# Minimum text length to process (characters)
MIN_TEXT_LENGTH=500
```

## Production Deployment

### SSL/TLS Certificate Setup

```bash
# Using Let's Encrypt with Certbot

# 1. Install certbot
sudo apt-get install certbot python3-certbot-nginx

# 2. Generate certificate
sudo certbot certonly --standalone -d yourdomain.com

# 3. Copy to container volume
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./ssl/key.pem
sudo chmod 644 ssl/*

# 4. Update docker-compose.yml ports to include 443
# 5. Restart services
docker-compose restart nginx
```

### Environment for Production

```env
# .env.production

# Database (use managed service like AWS RDS, Azure Database, or GCP Cloud SQL)
DATABASE_URL=postgresql://user:password@db-instance.region.rds.amazonaws.com:5432/financial_reports

# Security
SECRET_KEY=generate_strong_random_key_here
DEBUG=False
LOG_LEVEL=WARNING

# File Upload
MAX_FILE_SIZE_MB=100
UPLOAD_DIR=/mnt/secure-storage/uploads

# Vector Search
EMBEDDING_DIMENSION=1536
SIMILARITY_THRESHOLD=0.75  # Higher threshold for better quality

# Rate Limiting
REQUESTS_PER_MINUTE=30
REQUESTS_PER_HOUR=500
```

### Monitoring Setup

```yaml
# Add to docker-compose.yml for monitoring

services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### Backup Strategy

```bash
# Automated daily backup
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
docker-compose exec -T postgres pg_dump -U finuser financial_reports | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup uploads
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz uploads/

# Keep only last 30 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete
find $BACKUP_DIR -name "uploads_*.tar.gz" -mtime +30 -delete

# Save as cron job
# 0 2 * * * /path/to/backup.sh
```

### Health Checks

```bash
# Application health
curl http://localhost:7860/health

# Database health
docker-compose exec postgres pg_isready

# Check service logs for errors
docker-compose logs --since 1h --grep ERROR
```

## Uninstallation

### Docker Setup
```bash
# Stop and remove containers
docker-compose down

# Remove volumes (⚠️ deletes data)
docker-compose down -v

# Remove images
docker rmi financial-analyzer:latest
```

### Local Setup
```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf venv

# Drop database (⚠️ deletes data)
dropdb -U postgres financial_reports

# Remove application directory
rm -rf /path/to/financial-report-analyzer
```

## Getting Help

### Common Issues

**Port Already in Use**
```bash
# Find process using port
lsof -i :7860

# Kill process
kill -9 <PID>
```

**Database Connection Refused**
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check DATABASE_URL is correct
echo $DATABASE_URL

# Restart database
docker-compose restart postgres
```

**Out of Memory**
```bash
# Increase Docker memory
# Docker Desktop → Preferences → Resources → Memory: 4GB+

# Or reduce application memory usage
# Edit docker-compose.yml:
# services:
#   app:
#     mem_limit: 2g
```

**Slow Embeddings**
- Check provider API quotas
- Reduce chunk size in document_processor.py
- Check network latency to API endpoint
- Use async processing for batch jobs

## Next Steps

1. ✅ Complete setup using Option 1 or 2
2. 📊 Upload sample financial report
3. 🔐 Configure one AI provider
4. 💬 Test chat functionality
5. 📈 Try BI Bot analysis
6. 📝 Review audit logs
7. 🚀 Deploy to production

---

**Need Help?** Check README.md for detailed documentation and API reference.