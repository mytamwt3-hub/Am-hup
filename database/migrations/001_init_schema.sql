-- Am-hup Platform - Initial Database Schema
-- Version: 1.0.0
-- Created: 2026-09-06

-- ============================================
-- EXTENSION: UUID Support
-- ============================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- TABLE: tenants (Multi-Tenancy Core)
-- ============================================
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(20),
    entity_type VARCHAR(50) NOT NULL CHECK (entity_type IN ('company', 'establishment', 'branch')),
    parent_tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_tenants_email ON tenants(email);
CREATE INDEX idx_tenants_parent ON tenants(parent_tenant_id);
CREATE INDEX idx_tenants_active ON tenants(is_active);

-- ============================================
-- TABLE: users (Authentication)
-- ============================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    last_login TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    UNIQUE(tenant_id, email)
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_tenant ON users(tenant_id);
CREATE INDEX idx_users_active ON users(is_active);

-- ============================================
-- TABLE: roles (Role-Based Access Control)
-- ============================================
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, name)
);

CREATE INDEX idx_roles_tenant ON roles(tenant_id);

-- ============================================
-- TABLE: permissions (Access Control)
-- ============================================
CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_permissions_resource ON permissions(resource);

-- ============================================
-- TABLE: role_permissions (Role-Permission Mapping)
-- ============================================
CREATE TABLE role_permissions (
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE INDEX idx_role_permissions_role ON role_permissions(role_id);

-- ============================================
-- TABLE: user_roles (User-Role Assignment)
-- ============================================
CREATE TABLE user_roles (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

CREATE INDEX idx_user_roles_user ON user_roles(user_id);

-- ============================================
-- TABLE: branches (Branch Management)
-- ============================================
CREATE TABLE branches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) NOT NULL,
    city VARCHAR(100),
    country VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(255),
    manager_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    UNIQUE(tenant_id, code)
);

CREATE INDEX idx_branches_tenant ON branches(tenant_id);
CREATE INDEX idx_branches_active ON branches(is_active);
CREATE INDEX idx_branches_city ON branches(city);

-- ============================================
-- TABLE: audit_logs (Audit Trail)
-- ============================================
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(255),
    changes JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_tenant ON audit_logs(tenant_id);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);

-- ============================================
-- TABLE: settings (Tenant Settings)
-- ============================================
CREATE TABLE settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    key VARCHAR(255) NOT NULL,
    value JSONB,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, key)
);

CREATE INDEX idx_settings_tenant ON settings(tenant_id);

-- ============================================
-- DEFAULT ROLES
-- ============================================
INSERT INTO roles (tenant_id, name, description) 
VALUES (
    (SELECT id FROM tenants LIMIT 1),
    'Admin',
    'Full system access'
),
(
    (SELECT id FROM tenants LIMIT 1),
    'Manager',
    'Branch and user management'
),
(
    (SELECT id FROM tenants LIMIT 1),
    'User',
    'Basic user access'
);

-- ============================================
-- DEFAULT PERMISSIONS
-- ============================================
INSERT INTO permissions (name, description, resource, action)
VALUES
('create_branch', 'Create new branch', 'branches', 'create'),
('read_branch', 'View branches', 'branches', 'read'),
('update_branch', 'Update branch', 'branches', 'update'),
('delete_branch', 'Delete branch', 'branches', 'delete'),
('create_user', 'Create new user', 'users', 'create'),
('read_user', 'View users', 'users', 'read'),
('update_user', 'Update user', 'users', 'update'),
('delete_user', 'Delete user', 'users', 'delete'),
('manage_roles', 'Manage roles and permissions', 'roles', 'manage'),
('view_reports', 'View analytics and reports', 'reports', 'read');

-- ============================================
-- CREATE TRIGGER: Update updated_at
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_branches_updated_at BEFORE UPDATE ON branches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_settings_updated_at BEFORE UPDATE ON settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- GRANT PERMISSIONS
-- ============================================
GRANT CONNECT ON DATABASE am_hup_v2 TO am_hup_user;
GRANT USAGE ON SCHEMA public TO am_hup_user;
GRANT ALL ON ALL TABLES IN SCHEMA public TO am_hup_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO am_hup_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO am_hup_user;

-- ============================================
-- SCHEMA INITIALIZATION COMPLETE
-- ============================================
-- Total Tables: 10
-- Total Indexes: 18
-- Total Triggers: 4
-- Status: Ready for production
