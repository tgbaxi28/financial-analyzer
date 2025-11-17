# 🎯 Next Steps - Getting Started with Financial Analyzer

## Immediate Actions (15 minutes)

### 1. Configure AWS SES for Email

**Why**: The system needs to send magic link emails for authentication.

**Steps**:
```bash
1. Log into AWS Console
2. Go to Amazon SES (Simple Email Service)
3. Verify your sender email:
   - Click "Verified identities"
   - Click "Create identity"
   - Select "Email address"
   - Enter your email (e.g., noreply@yourdomain.com)
   - Check your email and click verification link
4. Note your AWS credentials:
   - AWS Access Key ID
   - AWS Secret Access Key
   - Region (e.g., us-east-1)
```

**Cost**: Free tier includes 62,000 emails/month

### 2. Get AI Provider API Key

**Choose ONE provider** (you can add more later):

**Option A: OpenAI** (Recommended for beginners)
```bash
1. Go to https://platform.openai.com/
2. Sign up / Log in
3. Go to API Keys section
4. Click "Create new secret key"
5. Copy the key (starts with sk-...)
```
**Cost**: ~$0.01-0.02 per query

**Option B: Azure OpenAI**
```bash
1. Azure Portal → Create Azure OpenAI resource
2. Get endpoint URL and API key
3. Deploy a model (gpt-4 or gpt-35-turbo)
```

**Option C: AWS Bedrock**
```bash
1. AWS Console → Amazon Bedrock
2. Enable Claude 3 Sonnet model
3. Use your AWS credentials
```

**Option D: Google Gemini**
```bash
1. Google AI Studio → https://makersuite.google.com/
2. Get API key
```

### 3. Configure Environment

```bash
cd "/Users/tanmay/Documents/Simform Accelerators/financial-analyzer"

# Edit .env file
nano .env

# Update these REQUIRED values:
AWS_ACCESS_KEY_ID=your_actual_key
AWS_SECRET_ACCESS_KEY=your_actual_secret
SES_SENDER_EMAIL=verified@yourdomain.com
SECRET_KEY=generate_a_random_32_character_string_here

# Optional: Change database password
POSTGRES_PASSWORD=choose_a_strong_password
```

**Generate SECRET_KEY** (Python):
```python
import secrets
print(secrets.token_urlsafe(32))
```

### 4. Run Setup Script

```bash
# Make executable
chmod +x scripts/setup.sh

# Run
./scripts/setup.sh
```

**Expected output**:
```
✅ Docker and Docker Compose are installed
✅ .env file exists
✅ Directories created
✅ Images pulled
✅ Images built
✅ Services started
✅ PostgreSQL is ready
✅ Qdrant is ready
✅ Backend is ready
✅ Gradio UI is ready
🎉 Setup complete!
```

### 5. Access Application

Open browser: **http://localhost:7860**

## First Use Workflow (10 minutes)

### Step 1: Register Account

1. Go to "Authentication" tab
2. Fill in:
   - Email: your@email.com (use a real email you can access)
   - First Name: John
   - Last Name: Doe
3. Click "Register"
4. **Check your email** for magic link
5. Copy the **token** from the email (long random string)
6. Paste token in "Magic Link Token" field
7. Click "Verify & Login"

**Expected**: "✅ Welcome, John!" message

### Step 2: Upload Test Document

**Prepare a test document**:
- Use a real financial document (bank statement, investment summary)
- OR create a test PDF/Excel with sample financial data

1. Go to "Upload Documents" tab
2. Click "Select Document"
3. Choose your file
4. Select "user" (for yourself)
5. If PDF is password-protected, enter password
6. Click "Upload & Process"

**Expected**: Processing status → "Completed (X chunks)"

**Processing time**: 10-30 seconds depending on file size

### Step 3: Chat with Your Document

1. Go to "AI Chat" tab
2. Configure AI provider:
   - **Provider**: OpenAI (or your choice)
   - **API Key**: Paste your API key here
   - **Model Name**: (leave empty for default)
3. Ask a question:

**Example questions**:
```
"What is the total balance in this document?"
"Summarize the key financial information"
"What are the largest expenses?"
"Show me all transactions over $1000"
```

4. Click "Send"

**Expected**: AI response with source citations

**Response time**: 2-5 seconds

## Verify Everything Works

### Checklist

- [ ] Services running: `docker-compose ps` (all should be "Up")
- [ ] Can access Gradio UI: http://localhost:7860
- [ ] Can access API docs: http://localhost:8000/docs
- [ ] Magic link email received
- [ ] Successfully logged in
- [ ] Document uploaded and processed
- [ ] AI chat responds with relevant answers
- [ ] Sources are cited in responses

## Troubleshooting Quick Fixes

### Email Not Received

```bash
# Check backend logs
docker-compose logs backend | grep -i email

# Common issues:
1. AWS credentials wrong → Check .env
2. Sender email not verified → Verify in AWS SES Console
3. Email in spam → Check spam folder
```

### Document Upload Fails

```bash
# Check logs
docker-compose logs backend | grep -i document

# Common issues:
1. File too large → Max 50MB
2. Unsupported format → Use PDF, XLSX, CSV, DOCX
3. Wrong password → Check PDF password
```

### AI Chat Not Working

```bash
# Common issues:
1. Wrong API key → Verify it's correct
2. No credits → Check your AI provider account
3. No documents uploaded → Upload first
4. Wrong provider selected → Match provider with your key
```

### Services Not Starting

```bash
# Restart everything
docker-compose down
docker-compose up -d

# Check individual service
docker-compose logs [service_name]
# service_name: postgres, qdrant, backend, gradio
```

## Production Deployment (Next Phase)

### When You're Ready

1. **Get a Domain**: your-company.com
2. **Setup SSL**: Use Let's Encrypt (free)
3. **Configure Nginx**: Reverse proxy with HTTPS
4. **Use Managed Services**:
   - Amazon RDS for PostgreSQL
   - Qdrant Cloud for vectors
   - AWS ECS/EKS for containers
5. **Setup Monitoring**: CloudWatch, Datadog, or New Relic
6. **Configure Backups**: Automated PostgreSQL backups

### Production Checklist

- [ ] Change all default passwords
- [ ] Use strong SECRET_KEY (32+ chars)
- [ ] Enable HTTPS
- [ ] Setup database backups
- [ ] Configure monitoring/alerts
- [ ] Enable AWS CloudWatch logging
- [ ] Setup CI/CD pipeline
- [ ] Load testing
- [ ] Security audit

## Adding Features

### Add Family Members

```
1. After login, use API directly or add to Gradio UI
2. POST /family endpoint
3. Upload documents for family members
4. Switch owner_type to "family_member"
```

### WrenAI Dashboard

```
1. Go to Dashboard tab in Gradio
2. Access WrenAI at http://localhost:3000
3. Connect to PostgreSQL database
4. Create custom dashboards
5. Build spend analysis views
```

### Multiple AI Providers

```
You can use different providers for different queries:
- OpenAI for general queries
- Claude (Bedrock) for complex analysis
- Gemini for cost-effective queries
```

## Support & Resources

### Documentation
- **README.md**: Complete feature documentation
- **QUICKSTART.md**: 5-minute setup guide
- **ARCHITECTURE.md**: Technical deep-dive
- **PROJECT_SUMMARY.md**: Implementation overview

### Useful Commands

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f backend

# Restart service
docker-compose restart backend

# Stop everything
docker-compose down

# Start everything
docker-compose up -d

# Rebuild after changes
docker-compose up -d --build

# Check service status
docker-compose ps

# Access database
docker-compose exec postgres psql -U finuser -d financial_analyzer
```

### API Testing

Interactive API docs: http://localhost:8000/docs

**Test endpoints**:
1. Click "Authorize" button
2. Enter: `Bearer your_jwt_token`
3. Try endpoints interactively

## Success Criteria

### You're Ready to Use the System When:

✅ All Docker services are running
✅ You can receive magic link emails
✅ You can login successfully
✅ Documents process without errors
✅ AI responds to your queries
✅ Sources are cited correctly

### Expected Performance:

- **Login**: Instant (magic link sent < 1 second)
- **Document Upload**: 10-30 seconds
- **AI Query**: 2-5 seconds
- **Dashboard Load**: < 2 seconds

## What to Expect

### First Document
- Upload time: ~20 seconds
- PII detection: Automatic (silent)
- Chunks created: 20-100 (depending on size)
- Ready to query: Immediately after processing

### First Query
- Response time: 3-5 seconds
- Relevance: High (if documents match query)
- Sources: 1-3 documents cited
- Token cost: ~$0.01-0.02 per query

### Growing Your Data
- 10 documents: Works great
- 100 documents: Scales well
- 1000+ documents: May need pagination

## Quick Wins

### Day 1
- [x] Setup complete
- [x] First document uploaded
- [x] First AI query successful

### Week 1
- [ ] Upload all recent financial documents
- [ ] Invite family members
- [ ] Create first WrenAI dashboard
- [ ] Explore different AI providers

### Month 1
- [ ] Full document history uploaded
- [ ] Custom analytics dashboards
- [ ] Regular financial insights
- [ ] Cost optimization (choose best AI provider)

## Getting Help

### Log Files
```bash
# Application logs
docker-compose logs backend > app_logs.txt

# Error logs
docker-compose logs backend | grep ERROR > errors.txt

# Database logs
docker-compose logs postgres > db_logs.txt
```

### Health Check
```bash
curl http://localhost:8000/health | jq
```

**Expected response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-11-17T...",
  "version": "1.0.0",
  "database": "healthy",
  "qdrant": "healthy"
}
```

## Remember

1. **API Keys are NOT stored** - Enter them each session
2. **Files are temporary** - Deleted after chunking
3. **PII is anonymized** - Automatic before storage
4. **Data is isolated** - Each user has separate collections
5. **Emails are real** - Magic links sent via AWS SES

---

**Ready to start?** Run: `./scripts/setup.sh`

**Questions?** Check README.md or ARCHITECTURE.md

**Enjoy your Financial Analyzer! 💰📊**
