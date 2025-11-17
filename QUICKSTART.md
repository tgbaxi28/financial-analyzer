# 🚀 Quick Start Guide

Get your Financial Analyzer running in 5 minutes!

## Prerequisites

- Docker Desktop installed
- AWS SES account configured
- AI Provider API key (OpenAI, Azure OpenAI, AWS Bedrock, or Google Gemini)

## Python Virtual Environment (recommended)

It's recommended to create a project-local Python virtual environment before installing dependencies. From the project root run:

```bash
# create venv
python3 -m venv .venv
# activate venv (macOS / zsh)
source .venv/bin/activate
```

When finished working in the project, deactivate with `deactivate`.

## Step-by-Step Setup

### 1. Configure Environment

```bash
# Navigate to project directory
cd "/Users/tanmay/Documents/Simform Accelerators/financial-analyzer"

# Copy environment template
cp .env.example .env

# Edit with your actual values
nano .env
```

**Required Configuration:**

```env
# AWS SES (for sending magic link emails)
AWS_ACCESS_KEY_ID=AKIA...          # Your AWS access key
AWS_SECRET_ACCESS_KEY=...          # Your AWS secret key
SES_SENDER_EMAIL=noreply@yourdomain.com  # Verified email in SES

# Security
SECRET_KEY=generate-minimum-32-character-random-string-here

# Application
APP_URL=http://localhost:8000
```

### 2. Run Setup Script

```bash
# Make script executable
chmod +x scripts/setup.sh

# Run setup
./scripts/setup.sh
```

The script will:
- ✅ Check Docker installation
- ✅ Create required directories
- ✅ Pull and build images
- ✅ Start all services
- ✅ Verify health

### 3. Access the Application

Open your browser to: **http://localhost:7860**

## First Time Use

### Register Your Account

1. Go to **Authentication** tab
2. Enter your details:
   - Email: your@email.com
   - First Name: John
   - Last Name: Doe
3. Click **Register**
4. Check your email for magic link
5. Copy the token from email
6. Paste token and click **Verify & Login**

### Upload Your First Document

1. Go to **Upload Documents** tab
2. Click **Select Document**
3. Choose a financial document (PDF, Excel, CSV, or Word)
4. If PDF is password-protected, enter password
5. Click **Upload & Process**
6. Wait for processing to complete (you'll see status)

### Chat with Your Documents

1. Go to **AI Chat** tab
2. Configure your AI provider:
   - **Provider**: Select OpenAI (or your preferred provider)
   - **API Key**: Enter your OpenAI API key (e.g., sk-...)
   - **Model Name**: (optional) gpt-4-turbo-preview
3. Ask questions like:
   - "What is my total investment amount?"
   - "Show me my top 5 expenses last month"
   - "Summarize my portfolio performance"

## Example Workflow

### Scenario: Analyzing Investment Portfolio

```
1. Upload Documents:
   - bank_statement_march_2024.pdf
   - mutual_fund_portfolio.xlsx
   - stock_holdings.csv

2. Wait for Processing:
   ✅ bank_statement_march_2024.pdf - Completed (45 chunks)
   ✅ mutual_fund_portfolio.xlsx - Completed (28 chunks)
   ✅ stock_holdings.csv - Completed (15 chunks)

3. Ask Questions:
   Q: "What is my total portfolio value?"
   A: Based on your documents, your total portfolio value is:
      - Mutual Funds: $125,450.00
      - Stocks: $78,230.00
      - Total: $203,680.00

      Sources:
      - mutual_fund_portfolio.xlsx (Page 1, Relevance: 0.95)
      - stock_holdings.csv (Page N/A, Relevance: 0.92)

   Q: "Which mutual fund has the best performance?"
   A: [AI analyzes and provides detailed answer with sources]
```

## Adding Family Members

1. After login, you can add family members
2. Upload documents for family members
3. Switch between profiles to view different portfolios

## Viewing Analytics Dashboard

1. Go to **Dashboard** tab
2. Explore WrenAI analytics:
   - Spend analysis by category
   - Portfolio performance over time
   - Custom dashboard creation

## Troubleshooting

### Services Not Starting

```bash
# Check Docker status
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f gradio

# Restart services
docker-compose restart
```

### Email Not Sending

1. Verify AWS credentials in `.env`
2. Check SES sender email is verified in AWS Console
3. Check AWS region matches your SES setup
4. Review backend logs: `docker-compose logs backend | grep -i email`

### Document Upload Fails

1. Check file format is supported (PDF, XLSX, CSV, DOCX)
2. Ensure file size is under 50MB
3. For password-protected PDFs, verify password is correct
4. Check logs: `docker-compose logs backend | grep -i document`

### AI Chat Not Working

1. Verify API key is correct and active
2. Check you have credits/quota with your AI provider
3. Ensure documents are uploaded and processed successfully
4. Try a simpler question first

## Useful Commands

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f postgres
docker-compose logs -f qdrant

# Restart a specific service
docker-compose restart backend

# Stop all services
docker-compose down

# Stop and remove all data
docker-compose down -v

# Rebuild after code changes
docker-compose up -d --build

# Access database
docker-compose exec postgres psql -U finuser -d financial_analyzer

# Check Qdrant collections
curl http://localhost:6333/collections
```

## URLs Reference

| Service | URL | Description |
|---------|-----|-------------|
| Gradio UI | http://localhost:7860 | Main user interface |
| API Docs | http://localhost:8000/docs | Interactive API documentation |
| API ReDoc | http://localhost:8000/redoc | Alternative API docs |
| Health Check | http://localhost:8000/health | Service health status |
| WrenAI | http://localhost:3000 | Analytics dashboard |
| Qdrant Dashboard | http://localhost:6333/dashboard | Vector database UI |

## Security Best Practices

1. **Never commit `.env` file** to version control
2. **Use strong SECRET_KEY** (minimum 32 random characters)
3. **Rotate API keys** regularly
4. **Monitor AWS SES usage** to prevent abuse
5. **Enable MFA** on AWS account
6. **Use HTTPS** in production (configure reverse proxy)
7. **Regular backups** of PostgreSQL database

## Next Steps

- ✅ Configure AWS SES for production email
- ✅ Setup domain and SSL certificates for production
- ✅ Add more family members
- ✅ Upload historical financial documents
- ✅ Create custom dashboards in WrenAI
- ✅ Explore different AI models for better insights

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Review README.md for detailed documentation
3. Check API docs: http://localhost:8000/docs

---

**Happy Analyzing! 💰📊**
