#!/bin/bash

# Financial Analyzer - Development Environment Startup Script

set -e

echo "🚀 Financial Analyzer - Development Setup"
echo "==========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    echo "Please install Docker Desktop from https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker daemon is not running${NC}"
    echo "Please start Docker Desktop"
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found, creating from template...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env with your credentials before running the app${NC}"
    echo ""
fi

# Pull images first (faster than building)
echo "📥 Pulling Docker images..."
docker-compose -f docker-compose.dev.yml pull

# Start development containers
echo ""
echo "📦 Starting development database containers..."
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to be ready (this may take 10-15 seconds)..."
sleep 5

# Check PostgreSQL
echo ""
echo "🐘 Checking PostgreSQL..."
MAX_RETRIES=10
RETRY=0
while [ $RETRY -lt $MAX_RETRIES ]; do
    if docker exec financial_analyzer_postgres_dev pg_isready -U finuser -d financial_analyzer &> /dev/null; then
        echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
        echo "   Connection: postgresql://finuser:securepassword@localhost:5432/financial_analyzer"
        break
    fi
    RETRY=$((RETRY+1))
    if [ $RETRY -eq $MAX_RETRIES ]; then
        echo -e "${RED}❌ PostgreSQL failed to start${NC}"
        echo "   Check logs: docker-compose -f docker-compose.dev.yml logs postgres-dev"
        exit 1
    fi
    sleep 1
done

# Check Qdrant
echo ""
echo "🔍 Checking Qdrant..."
RETRY=0
while [ $RETRY -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:6333/ > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Qdrant is ready${NC}"
        echo "   API: http://localhost:6333"
        echo "   Dashboard: http://localhost:6333/dashboard"
        break
    fi
    RETRY=$((RETRY+1))
    if [ $RETRY -eq $MAX_RETRIES ]; then
        echo -e "${RED}❌ Qdrant failed to start${NC}"
        echo "   Check logs: docker-compose -f docker-compose.dev.yml logs qdrant-dev"
        exit 1
    fi
    sleep 1
done

# Check for virtual environment
echo ""
echo "🐍 Checking Python virtual environment..."
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found${NC}"
    echo "   Creating virtual environment..."
    python3 -m venv .venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment exists${NC}"
fi

# Activate venv and check dependencies
source .venv/bin/activate

echo ""
echo "📚 Checking Python dependencies..."
if python -c "import fastapi" 2>/dev/null; then
    echo -e "${GREEN}✅ Dependencies are installed${NC}"
else
    echo -e "${YELLOW}⚠️  Installing dependencies (this will take 3-4 minutes)...${NC}"
    pip install -q --upgrade pip
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Dependencies installed${NC}"
fi

# Check spaCy model
echo ""
echo "🔤 Checking spaCy model..."
if python -c "import spacy; spacy.load('en_core_web_sm')" 2>/dev/null; then
    echo -e "${GREEN}✅ spaCy model is installed${NC}"
else
    echo -e "${YELLOW}⚠️  Downloading spaCy model (one-time, ~12MB)...${NC}"
    python -m spacy download en_core_web_sm
    echo -e "${GREEN}✅ spaCy model installed${NC}"
fi

# Create logs directory
mkdir -p logs

echo ""
echo "==========================================="
echo -e "${GREEN}🎉 Development environment is ready!${NC}"
echo "==========================================="
echo ""
echo "📊 Service Status:"
echo "   🐘 PostgreSQL:  localhost:5432"
echo "   🔍 Qdrant API:  http://localhost:6333"
echo "   🎨 Qdrant UI:   http://localhost:6333/dashboard"
echo ""
echo "🔗 Connection Strings:"
echo "   ${BLUE}DATABASE_URL${NC}: postgresql://finuser:securepassword@localhost:5432/financial_analyzer"
echo "   ${BLUE}QDRANT_HOST${NC}:  localhost"
echo "   ${BLUE}QDRANT_PORT${NC}:  6333"
echo ""
echo "🚀 Next Steps:"
echo ""
echo "   1. Keep this terminal open, and open TWO new terminals"
echo ""
echo "   2. In Terminal 1 - Run FastAPI backend:"
echo "      ${YELLOW}source .venv/bin/activate${NC}"
echo "      ${YELLOW}uvicorn app.main:app --reload --host 0.0.0.0 --port 8000${NC}"
echo ""
echo "   3. In Terminal 2 - Run Gradio UI:"
echo "      ${YELLOW}source .venv/bin/activate${NC}"
echo "      ${YELLOW}python gradio_app.py${NC}"
echo ""
echo "   4. Access the application:"
echo "      ${BLUE}http://localhost:7860${NC} (Gradio UI)"
echo "      ${BLUE}http://localhost:8000/docs${NC} (API Docs)"
echo ""
echo "📝 Useful Commands:"
echo "   View logs:        ${YELLOW}docker-compose -f docker-compose.dev.yml logs -f${NC}"
echo "   Stop services:    ${YELLOW}./scripts/dev-stop.sh${NC}"
echo "   Restart services: ${YELLOW}docker-compose -f docker-compose.dev.yml restart${NC}"
echo "   PostgreSQL CLI:   ${YELLOW}docker exec -it financial_analyzer_postgres_dev psql -U finuser -d financial_analyzer${NC}"
echo "   Qdrant stats:     ${YELLOW}curl http://localhost:6333/collections | jq${NC}"
echo ""
echo "📖 Full documentation: ${BLUE}DEV_SETUP.md${NC}"
echo ""
