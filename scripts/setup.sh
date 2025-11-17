#!/bin/bash

# Financial Analyzer Setup Script

set -e

echo "🚀 Financial Analyzer Setup"
echo "============================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration before continuing"
    echo ""
    read -p "Have you configured the .env file? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Please configure .env file and run this script again."
        exit 1
    fi
else
    echo "✅ .env file exists"
fi

echo ""

# Create required directories
echo "📁 Creating required directories..."
mkdir -p logs
mkdir -p /tmp/financial_uploads
echo "✅ Directories created"
echo ""

# Pull latest images
echo "🐳 Pulling Docker images..."
docker-compose pull
echo "✅ Images pulled"
echo ""

# Build custom images
echo "🔨 Building custom images..."
docker-compose build
echo "✅ Images built"
echo ""

# Start services
echo "🚀 Starting services..."
docker-compose up -d
echo "✅ Services started"
echo ""

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo ""
echo "🔍 Checking service health..."
echo ""

# Check PostgreSQL
if docker-compose exec -T postgres pg_isready -U finuser &> /dev/null; then
    echo "✅ PostgreSQL is ready"
else
    echo "❌ PostgreSQL is not ready"
fi

# Check Qdrant
if curl -s http://localhost:6333/collections &> /dev/null; then
    echo "✅ Qdrant is ready"
else
    echo "❌ Qdrant is not ready"
fi

# Check Backend
if curl -s http://localhost:8000/health &> /dev/null; then
    echo "✅ Backend is ready"
else
    echo "❌ Backend is not ready"
fi

# Check Gradio
if curl -s http://localhost:7860 &> /dev/null; then
    echo "✅ Gradio UI is ready"
else
    echo "❌ Gradio UI is not ready"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📍 Access points:"
echo "   - Gradio UI: http://localhost:7860"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - WrenAI: http://localhost:3000"
echo "   - Qdrant Dashboard: http://localhost:6333/dashboard"
echo ""
echo "📋 Next steps:"
echo "   1. Open http://localhost:7860 in your browser"
echo "   2. Register a new account"
echo "   3. Check your email for the magic link"
echo "   4. Upload financial documents"
echo "   5. Start chatting with your documents!"
echo ""
echo "📖 View logs: docker-compose logs -f"
echo "🛑 Stop services: docker-compose down"
echo ""
