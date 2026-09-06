# Am-hup Global Multi-Tenant Platform
# Project Structure Guide

## 📁 Project Organization (After Refactoring)

```
Am-hup/
├── frontend/                          # React Frontend Application
│   ├── src/
│   │   ├── components/                # Reusable UI Components
│   │   │   ├── Layout.jsx             # Main layout wrapper
│   │   │   ├── Dashboard.jsx          # Dashboard component
│   │   │   └── ...
│   │   ├── pages/                     # Page components
│   │   │   ├── Login.jsx              # Login page
│   │   │   ├── Register.jsx           # Registration page
│   │   │   ├── Dashboard.jsx          # Dashboard page
│   │   │   ├── Branches.jsx           # Branches management
│   │   │   ├── Users.jsx              # Users management
│   │   │   ├── Settings.jsx           # Settings page
│   │   │   └── NotFound.jsx           # 404 page
│   │   ├── store/                     # Zustand state management
│   │   │   ├── authStore.js           # Authentication state
│   │   │   └── branchStore.js         # Branch management state
│   │   ├── App.jsx                    # Main app component
│   │   ├── main.jsx                   # Entry point
│   │   └── index.css                  # Global styles (Tailwind)
│   ├── public/
│   │   ├── manifest.json              # PWA manifest
│   │   ├── service-worker.js          # PWA service worker
│   │   ├── favicon.ico                # App icon
│   │   └── icons/                     # PWA icons
│   ├── index.html                     # Main HTML file
│   ├── package.json                   # NPM dependencies
│   ├── vite.config.js                 # Vite configuration
│   ├── tailwind.config.js             # Tailwind configuration
│   ├── postcss.config.js              # PostCSS configuration
│   └── .env                           # Environment variables
│
├── backend/                           # FastAPI Backend Application
│   ├── api/
│   │   ├── v1/
│   │   │   ├── auth.py                # Authentication routes
│   │   │   ├── branches.py            # Branch management routes
│   │   │   ├── tenants.py             # Tenant management routes
│   │   │   ├── users.py               # User management routes
│   │   │   ├── websocket.py           # WebSocket routes
│   │   │   └── health.py              # Health check routes
│   │   └── dependencies.py            # FastAPI dependencies
│   ├── core/
│   │   ├── models.py                  # SQLAlchemy ORM models
│   │   ├── security.py                # JWT & password utilities
│   │   ├── tenant.py                  # Tenant context management
│   │   └── dependencies.py            # FastAPI dependencies
│   ├── middleware/
│   │   ├── tenant_middleware.py       # Tenant isolation middleware
│   │   └── cors_middleware.py         # CORS configuration
│   ├── config/
│   │   ├── database.py                # Database configuration
│   │   ├── settings.py                # App settings
│   │   └── constants.py               # Global constants
│   ├── schemas/                       # Pydantic request/response schemas
│   │   ├── auth.py                    # Auth schemas
│   │   ├── tenant.py                  # Tenant schemas
│   │   ├── branch.py                  # Branch schemas
│   │   └── user.py                    # User schemas
│   ├── tests/
│   │   ├── test_auth.py               # Authentication tests
│   │   ├── test_tenants.py            # Tenant tests
│   │   ├── test_branches.py           # Branch tests
│   │   └── conftest.py                # Pytest configuration
│   ├── static/                        # Frontend build output (auto-generated)
│   ├── main.py                        # FastAPI application entry point
│   ├── requirements.txt               # Python dependencies
│   ├── .env.example                   # Environment template
│   └── .env                           # Environment variables (local)
│
├── database/
│   └── migrations/
│       ├── 001_init_schema.sql        # Initial database schema
│       ├── 002_add_columns.sql        # Future migrations
│       └── README.md                  # Migration guide
│
├── scripts/
│   ├── setup.sh                       # Setup script
│   ├── deploy.sh                      # Deployment script
│   ├── cleanup.sh                     # Cleanup script
│   └── migrate.sh                     # Database migration script
│
├── docs/
│   ├── ARCHITECTURE.md                # System architecture
│   ├── API_GUIDE.md                   # API documentation
│   ├── INSTALLATION.md                # Installation guide
│   └── DEPLOYMENT.md                  # Deployment guide
│
├── .github/
│   └── workflows/
│       └── ci-cd.yml                  # GitHub Actions CI/CD pipeline
│
├── Dockerfile                         # Docker container image
├── docker-compose.yml                 # Docker Compose configuration
├── .dockerignore                      # Files to exclude from Docker
├── .gitignore                         # Git ignore file
├── README.md                          # Project README
├── INSTALLATION.md                    # Installation guide
├── QUICK_START.md                     # Quick start guide
└── LICENSE                            # MIT License
```

---

## 📋 File Placement Guide

### From Old Structure → New Structure

| Old File | New Location | Purpose |
|----------|-------------|----------|
| `index.html` | `frontend/index.html` | Main frontend entry point |
| `admin.html` | `frontend/src/pages/Dashboard.jsx` | Admin dashboard (converted to React) |
| `backend_server.py` | `backend/main.py` | FastAPI application |
| `chart_of_accounts.py` | `backend/api/v1/accounting.py` | Accounting API routes (to be created) |
| `accounting_core.py` | `backend/core/accounting.py` | Accounting business logic |
| `style.css` | `frontend/src/index.css` | Global styles (Tailwind) |
| `script.js` | `frontend/src/App.jsx` & stores | Frontend logic (React + Zustand) |
| `database.sql` | `database/migrations/001_init_schema.sql` | Database schema |

---

## 🔍 Key Directories Explained

### Frontend (`frontend/`)
- **Purpose**: React-based user interface
- **Technology**: React 18 + Vite + Tailwind CSS
- **Features**: 
  - Component-based architecture
  - State management with Zustand
  - PWA ready (manifest.json, service-worker.js)
  - RTL support for Arabic
  - Responsive design

### Backend (`backend/`)
- **Purpose**: FastAPI server handling business logic
- **Technology**: Python 3.11 + FastAPI + SQLAlchemy + PostgreSQL
- **Features**:
  - Multi-tenancy support
  - JWT authentication
  - RESTful API
  - WebSocket support
  - Database ORM

### Database (`database/migrations/`)
- **Purpose**: SQL migration files for database schema
- **Features**:
  - Version control for database changes
  - Easy rollback capability
  - Documentation for schema changes

---

## 🚀 How to Navigate the Project

1. **To modify frontend UI**: Go to `frontend/src/pages/` or `frontend/src/components/`
2. **To add API endpoints**: Go to `backend/api/v1/`
3. **To modify database schema**: Create new migration in `database/migrations/`
4. **To change styles**: Edit `frontend/src/index.css` or add CSS modules
5. **To add features**: Create new Pydantic schemas in `backend/schemas/`

---

## ✅ Best Practices

✅ Keep frontend and backend separate  
✅ Use environment variables for configuration  
✅ Follow naming conventions (snake_case for Python, camelCase for JS)  
✅ Add proper error handling  
✅ Write tests for critical features  
✅ Document API endpoints  
✅ Use git branches for features  
✅ Keep dependencies updated  

