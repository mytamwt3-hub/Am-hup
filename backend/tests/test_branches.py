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


def test_create_branch(setup_db):
    """Test creating a branch"""
    # Register company
    reg_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "company@example.com",
            "password": "SecurePass123!",
            "full_name": "Test Company",
            "phone": "+966501234567",
            "entity_type": "company"
        }
    )
    token = reg_response.json()["access_token"]
    tenant_id = reg_response.json()["tenant_id"]
    
    # Create branch
    branch_response = client.post(
        "/api/v1/branches",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": tenant_id
        },
        json={
            "name": "Dubai Store",
            "code": "DXB-001",
            "address": "123 Main St",
            "city": "Dubai",
            "country": "AE",
            "phone": "+971501234567",
            "email": "dubai@store.com",
            "manager_name": "Ahmed Al-Mazrouei"
        }
    )
    
    assert branch_response.status_code == 200
    data = branch_response.json()
    assert data["name"] == "Dubai Store"
    assert data["code"] == "DXB-001"
    assert data["phone"] == "+971501234567"
    print(f"✅ Branch created: {data['id']}")


def test_list_branches(setup_db):
    """Test listing branches"""
    # Register company
    reg_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "company@example.com",
            "password": "SecurePass123!",
            "full_name": "Test Company",
            "phone": "+966501234567",
            "entity_type": "company"
        }
    )
    token = reg_response.json()["access_token"]
    tenant_id = reg_response.json()["tenant_id"]
    
    # Create 2 branches
    for i in range(2):
        client.post(
            "/api/v1/branches",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Tenant-ID": tenant_id
            },
            json={
                "name": f"Store {i+1}",
                "code": f"STR-{i+1:03d}",
                "city": "Dubai",
                "phone": f"+97150123456{i}"
            }
        )
    
    # List branches
    list_response = client.get(
        "/api/v1/branches",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": tenant_id
        }
    )
    
    assert list_response.status_code == 200
    branches = list_response.json()
    assert len(branches) == 2
    print(f"✅ Listed {len(branches)} branches")


def test_update_branch(setup_db):
    """Test updating a branch"""
    # Register company
    reg_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "company@example.com",
            "password": "SecurePass123!",
            "full_name": "Test Company",
            "phone": "+966501234567",
            "entity_type": "company"
        }
    )
    token = reg_response.json()["access_token"]
    tenant_id = reg_response.json()["tenant_id"]
    
    # Create branch
    create_response = client.post(
        "/api/v1/branches",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": tenant_id
        },
        json={
            "name": "Dubai Store",
            "code": "DXB-001",
            "city": "Dubai",
            "phone": "+971501234567"
        }
    )
    branch_id = create_response.json()["id"]
    
    # Update branch
    update_response = client.patch(
        f"/api/v1/branches/{branch_id}",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant-ID": tenant_id
        },
        json={
            "manager_name": "Mohamed Al-Mazrouei"
        }
    )
    
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["manager_name"] == "Mohamed Al-Mazrouei"
    print(f"✅ Branch updated successfully")
