# 🚀 Quick Start Guide - Am-hup Multi-Tenancy Platform

## Prerequisites

- Python 3.10+
- PostgreSQL 13+
- pip / venv

## Installation

### 1. Clone Repository
```bash
git clone https://github.com/mytamwt3-hub/Am-hup.git
cd Am-hup
git checkout refactor/multi-tenancy-core
```

### 2. Setup Python Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 4. Setup Database

**Option A: PostgreSQL Local**
```bash
# Create database
psql -U postgres
CREATE DATABASE am_hup_v2;
\q

# Apply migrations
psql -U postgres -d am_hup_v2 -f ../database/migrations/001_init_schema.sql
```

**Option B: Using SQLite (for development/testing)**
```bash
# Just run the app, SQLite will auto-create
```

### 5. Configure Environment
```bash
cp .env.example .env
# Edit .env with your database credentials
```

### 6. Run Server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server will start at: `http://localhost:8000`

---

## API Endpoints

### 🔐 Authentication

#### Register Company
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "company@example.com",
    "password": "SecurePass123!",
    "full_name": "My Company",
    "phone": "+966501234567",
    "entity_type": "company",
    "entity_name": "My Company Inc."
  }'
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_email": "company@example.com",
  "entity_type": "company"
}
```

#### Register Establishment (Under Company)
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "establishment@example.com",
    "password": "SecurePass123!",
    "full_name": "Dubai Branch",
    "phone": "+966509876543",
    "entity_type": "establishment",
    "entity_name": "Dubai Establishment",
    "parent_email": "company@example.com"
  }'
```

#### Register Branch (Under Establishment)
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "branch@example.com",
    "password": "SecurePass123!",
    "full_name": "Store 1",
    "phone": "+966505555555",
    "entity_type": "branch",
    "entity_name": "Dubai Store",
    "parent_email": "establishment@example.com"
  }'
```

#### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "company@example.com",
    "password": "SecurePass123!"
  }'
```

---

### 🏢 Tenant Management

#### Get Current Tenant
```bash
curl -X GET http://localhost:8000/api/v1/tenants/me \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: YOUR_TENANT_ID"
```

#### Update Tenant
```bash
curl -X PATCH http://localhost:8000/api/v1/tenants/me \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: YOUR_TENANT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Updated Name",
    "currency": "SAR"
  }'
```

---

### 🏪 Branch Management

#### Create Branch
```bash
curl -X POST http://localhost:8000/api/v1/branches \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: YOUR_TENANT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dubai Store",
    "code": "DXB-001",
    "address": "123 Main St",
    "city": "Dubai",
    "country": "AE",
    "phone": "+971501234567",
    "email": "dubai@store.com",
    "manager_name": "Ahmed Al-Mazrouei",
    "latitude": "25.2048",
    "longitude": "55.2708"
  }'
```

#### List Branches
```bash
curl -X GET http://localhost:8000/api/v1/branches \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: YOUR_TENANT_ID"
```

#### Get Specific Branch
```bash
curl -X GET http://localhost:8000/api/v1/branches/{branch_id} \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: YOUR_TENANT_ID"
```

#### Update Branch
```bash
curl -X PATCH http://localhost:8000/api/v1/branches/{branch_id} \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: YOUR_TENANT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "manager_name": "New Manager",
    "phone": "+971509999999"
  }'
```

#### Delete Branch (Soft Delete)
```bash
curl -X DELETE http://localhost:8000/api/v1/branches/{branch_id} \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-ID: YOUR_TENANT_ID"
```

---

### 📡 WebSocket Notifications

#### Connect to Notifications
```javascript
// JavaScript
const token = "YOUR_JWT_TOKEN";
const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/notifications?token=${token}`);

ws.onopen = () => {
  console.log("Connected to notifications");
  ws.send(JSON.stringify({ type: "ping" }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log("Notification:", message);
};

ws.onerror = (error) => {
  console.error("WebSocket error:", error);
};
```

---

## Testing

### Run All Tests
```bash
cd backend
pytest tests/ -v
```

### Run Specific Test File
```bash
pytest tests/test_auth.py -v
```

### Run Integration Tests
```bash
bash ../tests/run_tests.sh
```

### View Test Report
```bash
cat ../TEST_REPORT.md
```

---

## Architecture Overview

### Multi-Tenancy Model
- **Shared Database** with tenant isolation
- **Row-Level Security** ready (PostgreSQL)
- **JWT Authentication** for all API calls
- **Middleware-enforced** tenant context

### Entity Hierarchy
```
Company (Tenant)
├── Email: company@example.com
├── Phone: +966501234567
└── Status: active

    ├── Establishment
    │   ├── Email: establishment@example.com
    │   ├── Phone: +966509876543
    │   └── Status: pending (awaiting company approval)
    │
    │   ├── Branch
    │   │   ├── Email: branch@example.com
    │   │   ├── Phone: +966505555555
    │   │   └── Status: pending (awaiting establishment approval)
    │
    │   └── Branch 2 ...
    │
    └── Establishment 2 ...
```

### Database Tables

**tenants** - Registry of all companies/establishments/branches
```sql
id (PK), name, slug, email, phone, status, plan_type, currency, ...
```

**users** - Users within each tenant
```sql
id (PK), tenant_id (FK), email, password_hash, role, ...
```

**branches** - Store locations (future: can be under any tenant)
```sql
id (PK), tenant_id (FK), name, code, phone, ...
```

---

## Troubleshooting

### Issue: Database Connection Error
```
psycopg2.OperationalError: could not connect to server
```

**Solution**: Check `.env` file database URL and ensure PostgreSQL is running

### Issue: JWT Token Invalid
```
{"detail": "Invalid token"}
```

**Solution**: Ensure token is not expired and SECRET_KEY is correct

### Issue: Tenant ID Not Found
```
{"detail": "Tenant ID not provided"}
```

**Solution**: Add `X-Tenant-ID` header to your request

### Issue: Access Denied (403)
```
{"detail": "Access denied"}
```

**Solution**: Verify your tenant_id matches the one in your JWT token

---

## Documentation

- **[Architecture](ARCHITECTURE.md)** - System design and multi-tenancy model
- **[Test Report](TEST_REPORT.md)** - Complete test results
- **[API Docs](http://localhost:8000/docs)** - Swagger UI

---

## Support

For issues or questions:
1. Check the [Test Report](TEST_REPORT.md)
2. Review [Architecture](ARCHITECTURE.md)
3. Check API documentation: http://localhost:8000/docs

---

**Version**: 2.0.0  
**Status**: ✅ Production Ready  
**Last Updated**: 2026-09-05
