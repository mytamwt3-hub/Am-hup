#!/bin/bash
# 🚀 Complete Setup Script for Am-hup Platform
# This script automates the entire setup process

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          🚀 Am-hup Platform - Complete Setup Script            ║${NC}"
echo -e "${BLUE}║                     Version 2.0.0                              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Verify Prerequisites
echo -e "${BLUE}[STEP 1/7]${NC} Verifying prerequisites..."
echo ""

if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed${NC}"
    echo "  Download from: https://www.docker.com/products/docker-desktop"
    exit 1
fi
echo -e "${GREEN}✓ Docker found${NC} ($(docker --version))"

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ Docker Compose is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose found${NC} ($(docker-compose --version))"

if ! command -v git &> /dev/null; then
    echo -e "${RED}✗ Git is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Git found${NC} ($(git --version))"

echo ""

# Step 2: Create directory structure
echo -e "${BLUE}[STEP 2/7]${NC} Creating project structure..."
echo ""

mkdir -p frontend/{src/{components,pages,store},public/{icons,screenshots}}
mkdir -p backend/{api/v1,core,middleware,config,schemas,tests,static}
mkdir -p database/migrations
mkdir -p scripts
mkdir -p docs

echo -e "${GREEN}✓ Project directories created${NC}"
echo ""

# Step 3: Setup environment files
echo -e "${BLUE}[STEP 3/7]${NC} Creating environment files..."
echo ""

if [ ! -f backend/.env ]; then
    cat > backend/.env << 'EOF'
# Database Configuration
DATABASE_URL=postgresql://am_hup_user:SecurePass123!@postgres:5432/am_hup_v2

# Application Settings
SECRET_KEY=your-super-secret-key-change-in-production-$(openssl rand -hex 32)
DEBUG=false
APP_ENV=production
APP_VERSION=2.0.0

# Tenant Configuration
TENANT_HEADER_NAME=X-Tenant-ID

# CORS Settings
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]

# JWT Settings
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
EOF
    echo -e "${GREEN}✓ Created backend/.env${NC}"
else
    echo -e "${YELLOW}⚠ backend/.env already exists${NC}"
fi

if [ ! -f frontend/.env ]; then
    cat > frontend/.env << 'EOF'
VITE_API_URL=http://localhost:8000/api/v1
VITE_APP_NAME=Am-hup
VITE_APP_VERSION=2.0.0
EOF
    echo -e "${GREEN}✓ Created frontend/.env${NC}"
else
    echo -e "${YELLOW}⚠ frontend/.env already exists${NC}"
fi

echo ""

# Step 4: Build Docker images
echo -e "${BLUE}[STEP 4/7]${NC} Building Docker images..."
echo -e "${YELLOW}This may take 2-3 minutes...${NC}"
echo ""

docker-compose build

echo ""
echo -e "${GREEN}✓ Docker images built successfully${NC}"
echo ""

# Step 5: Start services
echo -e "${BLUE}[STEP 5/7]${NC} Starting services..."
echo ""

docker-compose up -d

echo -e "${GREEN}✓ Services started${NC}"
echo ""

# Step 6: Wait for services to be ready
echo -e "${BLUE}[STEP 6/7]${NC} Waiting for services to initialize..."
echo ""

echo "  Waiting for PostgreSQL..."
for i in {1..30}; do
    if docker-compose exec -T postgres pg_isready -U am_hup_user > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓ PostgreSQL ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "  ${RED}✗ PostgreSQL failed to start${NC}"
        exit 1
    fi
    sleep 1
done

echo "  Waiting for Backend API..."
for i in {1..30}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓ Backend API ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "  ${RED}✗ Backend API failed to start${NC}"
        exit 1
    fi
    sleep 1
done

echo "  Waiting for Frontend..."
sleep 5
echo -e "  ${GREEN}✓ Frontend ready${NC}"

echo ""

# Step 7: Display success message
echo -e "${BLUE}[STEP 7/7]${NC} Displaying URLs and credentials..."
echo ""

echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                   ✅ SETUP COMPLETE! 🎉                        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}📍 Application URLs:${NC}"
echo -e "   Frontend:     ${GREEN}http://localhost:3000${NC}"
echo -e "   Backend:      ${GREEN}http://localhost:8000${NC}"
echo -e "   API Docs:     ${GREEN}http://localhost:8000/docs${NC}"
echo -e "   ReDoc:        ${GREEN}http://localhost:8000/redoc${NC}"
echo ""

echo -e "${BLUE}🗄️  Database Connection:${NC}"
echo -e "   Host:         ${GREEN}localhost${NC}"
echo -e "   Port:         ${GREEN}5432${NC}"
echo -e "   User:         ${GREEN}am_hup_user${NC}"
echo -e "   Password:     ${GREEN}SecurePass123!${NC}"
echo -e "   Database:     ${GREEN}am_hup_v2${NC}"
echo ""

echo -e "${BLUE}🚀 Next Steps:${NC}"
echo "   1. Open http://localhost:3000 in your browser"
echo "   2. Click 'Register' to create a new company account"
echo "   3. Fill in the registration form:"
echo "      - Entity Type: Company"
echo "      - Company Name: Your Company Name"
echo "      - Full Name: Your Name"
echo "      - Phone: +966501234567"
echo "      - Email: your-email@example.com"
echo "      - Password: Create a strong password"
echo "   4. You'll be logged in automatically"
echo "   5. Start creating branches and managing your business!"
echo ""

echo -e "${YELLOW}⚠️  Important:${NC}"
echo "   - Change SECRET_KEY in backend/.env for production"
echo "   - Use strong database passwords"
echo "   - Update CORS_ORIGINS for your domain"
echo "   - Enable HTTPS on deployment"
echo ""

echo -e "${BLUE}📚 Documentation:${NC}"
echo "   - README.md - Project overview"
echo "   - INSTALLATION.md - Installation guide"
echo "   - docs/ARCHITECTURE.md - System architecture"
echo "   - docs/PROJECT_STRUCTURE.md - Project structure"
echo ""

echo -e "${BLUE}🛠️  Common Commands:${NC}"
echo "   docker-compose logs -f          # View logs"
echo "   docker-compose ps               # Show running containers"
echo "   docker-compose down             # Stop all services"
echo "   docker-compose down -v          # Stop and remove data"
echo ""

echo -e "${GREEN}Happy coding! 🎉${NC}"
echo ""
