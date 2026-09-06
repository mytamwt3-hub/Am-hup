#!/bin/bash
# Database Migration Script
# Run this after database initialization

set -e

echo "🗄️  Running database migrations..."

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
    if psql -h localhost -U am_hup_user -d am_hup_v2 -c "SELECT 1" > /dev/null 2>&1; then
        echo "✓ PostgreSQL is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "✗ PostgreSQL failed to start"
        exit 1
    fi
    sleep 1
done

# Run migrations
echo "Running migration: 001_init_schema.sql"
psql -h localhost -U am_hup_user -d am_hup_v2 -f database/migrations/001_init_schema.sql

echo ""
echo "✅ Database migrations completed successfully!"
echo ""
echo "Database schema initialized with:"
echo "  - Tenants table (multi-tenancy core)"
echo "  - Users table (authentication)"
echo "  - Branches table (branch management)"
echo "  - Roles & Permissions (RBAC)"
echo ""
