#!/bin/bash
# 🌍 Production Deployment Script
# Deploys application to production server

set -e

echo ""
echo "🚀 Production Deployment Script"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${YELLOW}⚠️  This script will deploy to production${NC}"
echo ""
read -p "Continue? (yes/no): " -r
echo ""

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Deployment cancelled"
    exit 1
fi

echo -e "${BLUE}[1/6]${NC} Pulling latest code..."
git pull origin main

echo ""
echo -e "${BLUE}[2/6]${NC} Building Docker image..."
docker build -t am-hup:prod .

echo ""
echo -e "${BLUE}[3/6]${NC} Stopping old containers..."
docker-compose -f docker-compose.prod.yml down || true

echo ""
echo -e "${BLUE}[4/6]${NC} Starting new containers..."
docker-compose -f docker-compose.prod.yml up -d

echo ""
echo -e "${BLUE}[5/6]${NC} Running database migrations..."
docker-compose -f docker-compose.prod.yml exec -T backend python -m alembic upgrade head

echo ""
echo -e "${BLUE}[6/6]${NC} Verifying deployment..."
for i in {1..30}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Application is healthy${NC}"
        break
    fi
    sleep 1
done

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "Application URL: https://your-domain.com"
echo ""
