from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from schemas.branch import BranchCreate, BranchUpdate, BranchResponse
from core.models import Branch, Tenant
from config.database import get_db
from core.dependencies import get_current_user
from core.tenant import get_tenant_id
import logging
import uuid

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/branches", tags=["branches"])


@router.post("", response_model=BranchResponse)
async def create_branch(
    branch_data: BranchCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new branch under current tenant
    """
    # Only managers and admins can create branches
    if current_user["role"] not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Check tenant exists and user belongs to it
    tenant = db.query(Tenant).filter(Tenant.id == current_user["tenant_id"]).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    # Check if branch code already exists for this tenant
    existing = db.query(Branch).filter(
        Branch.tenant_id == tenant.id,
        Branch.code == branch_data.code
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Branch code already exists for this tenant"
        )
    
    # Create branch
    branch = Branch(
        id=str(uuid.uuid4()),
        tenant_id=tenant.id,
        name=branch_data.name,
        code=branch_data.code,
        address=branch_data.address,
        city=branch_data.city,
        country=branch_data.country,
        phone=branch_data.phone,
        email=branch_data.email,
        manager_name=branch_data.manager_name,
        latitude=branch_data.latitude,
        longitude=branch_data.longitude,
        is_active=True
    )
    
    db.add(branch)
    db.commit()
    db.refresh(branch)
    
    logger.info(f"✅ Branch created: {branch.id} for tenant {tenant.id}")
    
    return branch


@router.get("", response_model=list[BranchResponse])
async def list_branches(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50
):
    """
    List all branches for current tenant
    """
    branches = db.query(Branch).filter(
        Branch.tenant_id == current_user["tenant_id"]
    ).offset(skip).limit(limit).all()
    
    return branches


@router.get("/{branch_id}", response_model=BranchResponse)
async def get_branch(
    branch_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get specific branch (only if belongs to current tenant)
    """
    branch = db.query(Branch).filter(
        Branch.id == branch_id,
        Branch.tenant_id == current_user["tenant_id"]
    ).first()
    
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Branch not found"
        )
    
    return branch


@router.patch("/{branch_id}", response_model=BranchResponse)
async def update_branch(
    branch_id: str,
    branch_data: BranchUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update branch details (only managers and admins)
    """
    if current_user["role"] not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    branch = db.query(Branch).filter(
        Branch.id == branch_id,
        Branch.tenant_id == current_user["tenant_id"]
    ).first()
    
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Branch not found"
        )
    
    update_dict = branch_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(branch, key, value)
    
    db.commit()
    db.refresh(branch)
    
    logger.info(f"✅ Branch updated: {branch_id}")
    
    return branch


@router.delete("/{branch_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_branch(
    branch_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Soft delete branch (only admins)
    """
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete branches"
        )
    
    branch = db.query(Branch).filter(
        Branch.id == branch_id,
        Branch.tenant_id == current_user["tenant_id"]
    ).first()
    
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Branch not found"
        )
    
    branch.is_active = False
    db.commit()
    
    logger.info(f"✅ Branch deleted: {branch_id}")
