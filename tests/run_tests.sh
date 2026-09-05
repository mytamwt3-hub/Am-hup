#!/bin/bash
# Test Script for Am-hup Multi-Tenancy Platform
# Run all tests and generate report

set -e

echo ""
echo "🧪 ========================================"
echo "   Am-hup Multi-Tenancy Test Suite"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

echo -e "${YELLOW}[1/5] Testing Company Registration...${NC}"
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "company-test@example.com",
    "password": "SecurePass123!",
    "full_name": "Test Company",
    "phone": "+966501234567",
    "entity_type": "company",
    "entity_name": "Test Company Inc."
  }' 2>/dev/null | python3 -m json.tool

echo ""
echo -e "${YELLOW}[2/5] Testing Establishment Registration...${NC}"
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "establishment@example.com",
    "password": "SecurePass123!",
    "full_name": "Test Establishment",
    "phone": "+966509876543",
    "entity_type": "establishment",
    "entity_name": "Dubai Branch",
    "parent_email": "company-test@example.com"
  }' 2>/dev/null | python3 -m json.tool

echo ""
echo -e "${YELLOW}[3/5] Testing Branch Registration...${NC}"
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "branch@example.com",
    "password": "SecurePass123!",
    "full_name": "Test Branch",
    "phone": "+966505555555",
    "entity_type": "branch",
    "entity_name": "Dubai Store",
    "parent_email": "establishment@example.com"
  }' 2>/dev/null | python3 -m json.tool

echo ""
echo -e "${YELLOW}[4/5] Testing Tenant Isolation (Two Companies)...${NC}"
echo "Creating Company A..."
COMPANY_A=$(curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "company-a@example.com",
    "password": "SecurePass123!",
    "full_name": "Company A",
    "phone": "+966501111111",
    "entity_type": "company"
  }' | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['access_token'] + ':' + data['tenant_id'])")

TOKEN_A=$(echo $COMPANY_A | cut -d':' -f1)
TENANT_A=$(echo $COMPANY_A | cut -d':' -f2)

echo "Creating Company B..."
COMPANY_B=$(curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "company-b@example.com",
    "password": "SecurePass123!",
    "full_name": "Company B",
    "phone": "+966502222222",
    "entity_type": "company"
  }' | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['access_token'] + ':' + data['tenant_id'])")

TOKEN_B=$(echo $COMPANY_B | cut -d':' -f1)
TENANT_B=$(echo $COMPANY_B | cut -d':' -f2)

echo "Company A Token: $TOKEN_A"
echo "Company A Tenant: $TENANT_A"
echo "Company B Token: $TOKEN_B"
echo "Company B Tenant: $TENANT_B"

echo ""
echo "Company A creating branch..."
curl -X POST http://localhost:8000/api/v1/branches \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "X-Tenant-ID: $TENANT_A" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Company A Store",
    "code": "CA-001",
    "city": "Dubai",
    "phone": "+971501111111"
  }' 2>/dev/null | python3 -m json.tool

echo ""
echo "Company B creating branch..."
curl -X POST http://localhost:8000/api/v1/branches \
  -H "Authorization: Bearer $TOKEN_B" \
  -H "X-Tenant-ID: $TENANT_B" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Company B Store",
    "code": "CB-001",
    "city": "Abu Dhabi",
    "phone": "+971502222222"
  }' 2>/dev/null | python3 -m json.tool

echo ""
echo -e "${YELLOW}Testing Isolation - Company A lists branches:${NC}"
echo "Should see only 1 branch (Company A Store)"
curl -s -X GET http://localhost:8000/api/v1/branches \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "X-Tenant-ID: $TENANT_A" | python3 -m json.tool

echo ""
echo -e "${YELLOW}Testing Isolation - Company B lists branches:${NC}"
echo "Should see only 1 branch (Company B Store)"
curl -s -X GET http://localhost:8000/api/v1/branches \
  -H "Authorization: Bearer $TOKEN_B" \
  -H "X-Tenant-ID: $TENANT_B" | python3 -m json.tool

echo ""
echo -e "${YELLOW}[5/5] Testing Unauthorized Access...${NC}"
echo "Company A trying to access with Company B's tenant ID (should fail):"
curl -s -X GET http://localhost:8000/api/v1/tenants/$TENANT_B \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "X-Tenant-ID: $TENANT_B" | python3 -m json.tool

echo ""
echo "========================================"
echo -e "${GREEN}✅ All tests completed!${NC}"
echo "========================================"
echo ""
