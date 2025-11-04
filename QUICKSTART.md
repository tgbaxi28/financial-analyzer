# Quick Start Guide - 5 Minutes to Running

## The Fastest Way to Get Started

### Prerequisites Check (1 minute)
```bash
# Check Docker is installed
docker --version  # Should be 20.10+
docker-compose --version  # Should be 1.29+

# If not installed:
# - macOS: brew install docker docker-compose
# - Ubuntu: sudo apt install docker.io docker-compose
# - Windows: Download Docker Desktop
```

### Start the System (2 minutes)
```bash
# 1. Navigate to project
cd /path/to/financial-report-analyzer

# 2. Start services (first run takes ~2 minutes for image builds)
docker-compose up -d

# 3. Wait for services to be healthy (check with: docker-compose ps)
# Should show all services as "healthy" or "up"
```

### Access & Configure (2 minutes)
```bash
# 1. Open browser to: http://localhost:7860

# 2. You'll see the Gradio interface with 4 tabs
#    - 🔐 Credentials (enter API key)
#    - 📄 Reports (upload documents - now with password support!)
#    - 💬 Chat (ask questions)
#    - 📈 BI Bot (pre-built analysis)

# 3. Go to Credentials tab:
#    - Choose provider: Azure AI / Google Gemini / AWS Bedrock
#    - Enter credentials (see below for getting them)
#    - Click "Validate & Save Credentials"

# 4. After validation succeeds:
#    - Go to Reports tab
#    - Upload a financial PDF/Excel/CSV/JSON/DOCX
#    - If file is password-protected, enter the password
#    - Wait for "Report uploaded successfully!" ✅

# 5. Go to Chat tab:
#    - Ask: "What was the total revenue?"
#    - System searches documents and responds with sources

# 6. Go to BI Bot tab:
#    - Select "variance_analysis"
#    - Click "Run Analysis"
```

## Getting API Credentials (Choose One)

### 🔵 Azure AI (Easiest if you have Azure account)
1. Go to https://portal.azure.com
2. Create resource → "Azure OpenAI"
3. Fill in details, click Create
4. Go to resource → "Keys and Endpoint"
5. Copy: **Key 1** → Paste in "API Key"
6. Copy URL like `https://myresource.openai.azure.com/` → Paste in "Endpoint"
7. Model: Select `gpt-4` or `gpt-35-turbo` (depending on your deployment)

### 🟢 Google Gemini (Free tier available!)
1. Go to https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Select project (or create new)
4. Copy the key → Paste in "API Key"
5. Model: `gemini-pro`

### 🟠 AWS Bedrock (For AWS users)
1. Go to AWS Console → Bedrock (choose region)
2. Click "Get started" if needed
3. Create IAM user with Bedrock permissions
4. Get Access Key & Secret from IAM console
5. Paste Access Key, Secret Key, region (e.g., `us-east-1`)
6. Model: `anthropic.claude-3-sonnet-20240229-v1:0`

## Test with Sample Data

### Download Sample Report
```bash
# Create a test CSV file
cat > test_report.csv << 'EOF'
Date,Revenue,Expenses,Profit,Assets,Liabilities
2023-01-01,1000000,600000,400000,5000000,2000000
2023-02-01,1100000,650000,450000,5200000,2100000
2023-03-01,1200000,700000,500000,5400000,2200000
2023-04-01,1150000,720000,430000,5300000,2150000
EOF

# Or download a sample PDF from:
# https://example.com/sample-financial-report.pdf
```

### Upload & Query
1. Go to Reports tab
2. Upload `test_report.csv`
3. Wait for success message
4. Go to Chat tab
5. Ask: "What is the profit trend?"
6. You'll get analysis with sources!

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 7860 already in use | `lsof -i :7860` then `kill -9 <PID>` |
| Database connection failed | `docker-compose restart postgres` |
| Credentials validation fails | Check API key format, ensure it has right permissions |
| No upload/file input showing | Refresh browser (Ctrl+F5 or Cmd+Shift+R) |
| Embeddings generation slow | Reduce file size or wait for quota reset (usually ~1 min) |
| "No relevant documents found" | Upload more reports or ask different questions |

## What Happens Next?

✅ **Credentials are validated** but NEVER stored
- Only kept in current session memory
- Discarded when you close/refresh

✅ **Reports are uploaded and processed**
- Text extracted (handles tables, headers, etc.)
- Split into semantic chunks
- Embeddings generated using your AI provider
- Stored in pgvector database

✅ **Queries use RAG (Retrieval-Augmented Generation)**
1. Your question → Embedding generated
2. Vector similarity search → Find 10 most relevant chunks
3. Context + question → Sent to LLM
4. Response generated with sources cited

✅ **Everything is logged**
- All queries logged for audit trail
- Provider usage tracked
- Can review in audit logs

## Next Steps

1. **Upload Real Reports**: Go to Reports tab, upload actual financial documents
2. **Explore Features**: Try different analysis types in BI Bot tab
3. **Check Audit Trail**: Review what was queried and which providers used
4. **Scale Up**: For production, see SETUP.md for SSL, monitoring, backups
5. **Read Docs**: Full documentation in README.md

## System Architecture Diagram

```
📦 Upload Report
    ↓
📄 Extract Text & Tables
    ↓
✂️ Split into Chunks
    ↓
🧠 Generate Embeddings (Azure/Google/AWS)
    ↓
🗄️ Store in pgvector Database
    ↓
💬 User Asks Question
    ↓
🔍 Vector Search (find relevant chunks)
    ↓
🤖 LLM generates response with context
    ↓
📊 Show response + source citations
```

## Key Features

✨ **What makes this system special:**

1. **No Credential Storage** - Credentials entered each session, never persisted
2. **Multi-Provider Support** - Switch between Azure/Google/AWS with one click
3. **File-in-Context Only** - All answers come from YOUR documents only
4. **Semantic Search** - Finds relevant info even with different phrasing
5. **Full Audit Trail** - Track every query and provider usage
6. **Production Ready** - Docker, SSL, rate limiting, monitoring included
7. **Easy Deployment** - Single `docker-compose up` command

## Estimated Costs (Monthly)

Using 1000 queries per day:

| Provider | Cost/Month | Embedding | Chat |
|----------|-----------|-----------|------|
| Azure | $10-20 | $0.02/1M | $0.03/1K |
| Google | $5-10 | $0.0001/1M | Free (limited) |
| AWS Bedrock | $15-25 | $0.10/1M | $3/1M output |

💡 **Pro Tip**: Use Google Gemini for development, switch to Azure/AWS for production

---

**🎉 That's it! You're now running a production-ready AI financial analysis system!**

Need help? Check README.md or SETUP.md for detailed guides.