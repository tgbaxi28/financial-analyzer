#!/bin/bash

# Financial Analyzer - Development Environment Stop Script

set -e

echo "🛑 Stopping Financial Analyzer Development Environment"
echo "======================================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Stop development container
echo "📦 Stopping development database container..."
docker-compose -f docker-compose.dev.yml stop

echo ""
echo -e "${GREEN}✅ Development environment stopped${NC}"
echo ""
echo "💡 To completely remove containers and volumes:"
echo "   ${YELLOW}docker-compose -f docker-compose.dev.yml down${NC}     (keeps data)"
echo "   ${YELLOW}docker-compose -f docker-compose.dev.yml down -v${NC}  (removes all data)"
echo ""
echo "🔄 To restart:"
echo "   ${YELLOW}./scripts/dev-start.sh${NC}"
echo ""
