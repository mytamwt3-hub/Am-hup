import pytest
from fastapi.testclient import TestClient
from main import app
from config.database import Base, engine

client = TestClient(app)

@pytest.fixture(scope="function")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_tenant_isolation(setup_db):
    """
    Test that Company A cannot see Company B's branches
    This is the core multi-tenancy security test
    """
    # Register Company A
    company_a_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "company-a@example.com",
            "password": "SecurePass123!",
            "full_name": "Company A",
            "phone": "+966501234567",
            "entity_type": "company"
        }
    )
    token_a = company_a_response.json()["access_token"]
    tenant_a = company_a_response.json()["tenant_id"]
    
    # Register Company B
    company_b_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "company-b@example.com",
            "password": "SecurePass123!",
            "full_name": "Company B",
            "phone": "+966509876543",
            "entity_type": "company"
        }
    )
    token_b = company_b_response.json()["access_token"]
    tenant_b = company_b_response.json()["tenant_id"]
    
    # Company A creates branches
    client.post(
        "/api/v1/branches",
        headers={
            "Authorization": f"Bearer {token_a}",
            "X-Tenant-ID": tenant_a
        },
        json={"name": "Company A Store", "code": "CA-001", "city": "Dubai", "phone": "+971501111111"}
    )
    
    # Company B creates branches
    client.post(
        "/api/v1/branches",
        headers={
            "Authorization": f"Bearer {token_b}",
            "X-Tenant-ID": tenant_b
        },
        json={"name": "Company B Store", "code": "CB-001", "city": "Abu Dhabi", "phone": "+971502222222"}
    )
    
    # Company A lists branches - should only see their own
    list_a_response = client.get(
        "/api/v1/branches",
        headers={
            "Authorization": f"Bearer {token_a}",
            "X-Tenant-ID": tenant_a
        }
    )
    branches_a = list_a_response.json()
    
    # Company B lists branches - should only see their own
    list_b_response = client.get(
        "/api/v1/branches",
        headers={
            "Authorization": f"Bearer {token_b}",
            "X-Tenant-ID": tenant_b
        }
    )
    branches_b = list_b_response.json()
    
    # Verify isolation
    assert len(branches_a) == 1
    assert branches_a[0]["name"] == "Company A Store"
    
    assert len(branches_b) == 1
    assert branches_b[0]["name"] == "Company B Store"
    
    # Verify Company A cannot see Company B's data
    assert branches_a[0]["name"] != "Company B Store"
    assert branches_b[0]["name"] != "Company A Store"
    
    print(f"✅ Tenant isolation verified: Company A and B are isolated")


def test_unauthorized_access(setup_db):
    """
    Test that user cannot access another tenant's data with their token
    """
    # Register Company A
    company_a_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "company-a@example.com",
            "password": "SecurePass123!",
            "full_name": "Company A",
            "phone": "+966501234567",
            "entity_type": "company"
        }
    )
    token_a = company_a_response.json()["access_token"]
    tenant_a = company_a_response.json()["tenant_id"]
    
    # Register Company B
    company_b_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "company-b@example.com",
            "password": "SecurePass123!",
            "full_name": "Company B",
            "phone": "+966509876543",
            "entity_type": "company"
        }
    )
    tenant_b = company_b_response.json()["tenant_id"]
    
    # Company A tries to access their own data with their token and tenant_id - SHOULD WORK
    access_own = client.get(
        "/api/v1/tenants/me",
        headers={
            "Authorization": f"Bearer {token_a}",
            "X-Tenant-ID": tenant_a
        }
    )
    assert access_own.status_code == 200
    print(f"✅ Company A can access their own data")
    
    # Company A tries to access Company B's data with Company A's token but Company B's tenant_id
    # The middleware should reject this
    access_other = client.get(
        f"/api/v1/tenants/{tenant_b}",
        headers={
            "Authorization": f"Bearer {token_a}",
            "X-Tenant-ID": tenant_b
        }
    )
    assert access_other.status_code == 403
    print(f"✅ Company A cannot access Company B's data (correctly rejected)")
