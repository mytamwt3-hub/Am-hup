import pytest
from fastapi.testclient import TestClient
from main import app
from config.database import Base, engine, SessionLocal
from core.models import Tenant, User
import json

client = TestClient(app)

# Setup test database
@pytest.fixture(scope="function")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_company_registration(setup_db):
    """Test registering a new company"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "company@example.com",
            "password": "SecurePass123!",
            "full_name": "Test Company",
            "phone": "+966501234567",
            "entity_type": "company",
            "entity_name": "Test Company Inc."
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"]
    assert data["tenant_id"]
    assert data["entity_type"] == "company"
    print(f"✅ Company registration successful: {data['tenant_id']}")


def test_establishment_registration(setup_db):
    """Test registering a new establishment under a company"""
    # First register company
    company_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "company@example.com",
            "password": "SecurePass123!",
            "full_name": "Test Company",
            "phone": "+966501234567",
            "entity_type": "company",
            "entity_name": "Test Company Inc."
        }
    )
    assert company_response.status_code == 200
    
    # Now register establishment
    est_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "establishment@example.com",
            "password": "SecurePass123!",
            "full_name": "Test Establishment",
            "phone": "+966509876543",
            "entity_type": "establishment",
            "entity_name": "Dubai Branch",
            "parent_email": "company@example.com"
        }
    )
    
    assert est_response.status_code == 200
    data = est_response.json()
    assert data["access_token"]
    assert data["tenant_id"]
    assert data["entity_type"] == "establishment"
    print(f"✅ Establishment registration successful: {data['tenant_id']}")


def test_branch_registration(setup_db):
    """Test registering a branch under an establishment"""
    # Register company
    company_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "company@example.com",
            "password": "SecurePass123!",
            "full_name": "Test Company",
            "phone": "+966501234567",
            "entity_type": "company",
            "entity_name": "Test Company Inc."
        }
    )
    company_token = company_response.json()["access_token"]
    
    # Register establishment
    est_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "establishment@example.com",
            "password": "SecurePass123!",
            "full_name": "Test Establishment",
            "phone": "+966509876543",
            "entity_type": "establishment",
            "entity_name": "Dubai Branch",
            "parent_email": "company@example.com"
        }
    )
    est_token = est_response.json()["access_token"]
    
    # Register branch
    branch_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "branch@example.com",
            "password": "SecurePass123!",
            "full_name": "Test Branch",
            "phone": "+966505555555",
            "entity_type": "branch",
            "entity_name": "Dubai Store",
            "parent_email": "establishment@example.com"
        }
    )
    
    assert branch_response.status_code == 200
    data = branch_response.json()
    assert data["access_token"]
    assert data["tenant_id"]
    print(f"✅ Branch registration successful: {data['tenant_id']}")


def test_login(setup_db):
    """Test login functionality"""
    # Register
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User",
            "phone": "+966501234567",
            "entity_type": "company"
        }
    )
    
    # Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "user@example.com",
            "password": "SecurePass123!"
        }
    )
    
    assert login_response.status_code == 200
    data = login_response.json()
    assert data["access_token"]
    print(f"✅ Login successful")


def test_invalid_login(setup_db):
    """Test login with wrong password"""
    # Register
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User",
            "phone": "+966501234567",
            "entity_type": "company"
        }
    )
    
    # Try login with wrong password
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "user@example.com",
            "password": "WrongPassword!"
        }
    )
    
    assert login_response.status_code == 401
    print(f"✅ Invalid login correctly rejected")
