from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from schemas.tenant import TenantResponse, TenantDetailResponse, TenantUpdate
from core.models import Tenant
from config.database import get_db
from core.dependencies import get_current_user, get_db_session
from core.tenant import get_tenant_id
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("/me", response_model=TenantDetailResponse)
async def get_current_tenant(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated tenant details
    """
    tenant = db.query(Tenant).filter(Tenant.id == current_user["tenant_id"]).first()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    return tenant


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get tenant by ID (only accessible by tenant members)
    """
    # Security: User can only view their own tenant
    if current_user["tenant_id"] != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    return tenant


@router.patch("/me", response_model=TenantResponse)
async def update_current_tenant(
    update_data: TenantUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current tenant details
    """
    tenant = db.query(Tenant).filter(Tenant.id == current_user["tenant_id"]).first()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    # Only admin can update
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update tenant"
        )
    
    update_dict = update_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(tenant, key, value)
    
    db.commit()
    logger.info(f"✅ Tenant updated: {tenant.id}")
    
    return tenant
