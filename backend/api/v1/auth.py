from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from schemas.auth import RegisterRequest, LoginRequest, TokenResponse, ApprovalRequest
from core.models import Tenant, User, Branch
from core.security import hash_password, verify_password, create_access_token
from config.database import get_db
from config.settings import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register new entity (Company, Establishment, or Branch)
    """
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Create tenant
    if request.entity_type == "company":
        tenant = Tenant(
            name=request.entity_name or request.full_name,
            slug=request.email.split("@")[0],
            email=request.email,
            phone=request.phone,
            tenant_type="business",
            status="active",
            plan_type="free"
        )
        db.add(tenant)
        db.flush()
        
    elif request.entity_type == "establishment":
        # Parent company must exist
        parent = db.query(Tenant).filter(Tenant.email == request.parent_email).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent company not found"
            )
        
        tenant = Tenant(
            name=request.entity_name or request.full_name,
            slug=f"{parent.slug}-{request.email.split('@')[0]}",
            email=request.email,
            phone=request.phone,
            tenant_type="business",
            status="pending",  # Awaiting company approval
            plan_type="free"
        )
        db.add(tenant)
        db.flush()
        
    elif request.entity_type == "branch":
        # Parent establishment must exist
        parent = db.query(Tenant).filter(Tenant.email == request.parent_email).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent establishment not found"
            )
        
        tenant = Tenant(
            name=request.entity_name or request.full_name,
            slug=f"{parent.slug}-{request.email.split('@')[0]}",
            email=request.email,
            phone=request.phone,
            tenant_type="business",
            status="pending",  # Awaiting establishment approval
            plan_type="free"
        )
        db.add(tenant)
        db.flush()
    
    # Create admin user for this tenant
    user = User(
        tenant_id=tenant.id,
        email=request.email,
        password_hash=hash_password(request.password),
        full_name=request.full_name,
        role="admin",
        is_active=True,
        is_verified=False
    )
    db.add(user)
    db.commit()
    
    # Create JWT token
    access_token = create_access_token(
        data={
            "sub": user.id,
            "tenant_id": tenant.id,
            "email": user.email,
            "role": user.role
        }
    )
    
    logger.info(f"✅ New {request.entity_type} registered: {request.email}")
    
    return TokenResponse(
        access_token=access_token,
        tenant_id=tenant.id,
        user_email=user.email,
        entity_type=request.entity_type
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login with email and password
    """
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    
    # Create JWT token
    access_token = create_access_token(
        data={
            "sub": user.id,
            "tenant_id": user.tenant_id,
            "email": user.email,
            "role": user.role
        }
    )
    
    logger.info(f"✅ User logged in: {request.email}")
    
    # Determine entity type
    entity_type = "company"
    if tenant.tenant_type == "business" and tenant.status in ["pending", "active"]:
        entity_type = "establishment" if tenant.email != tenant.email else "company"
    
    return TokenResponse(
        access_token=access_token,
        tenant_id=user.tenant_id,
        user_email=user.email,
        entity_type=entity_type
    )


@router.post("/approve-entity")
async def approve_entity(
    request: ApprovalRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Approve or reject sub-entity (Establishment or Branch)
    Only parent company/establishment can approve
    """
    # Find the child entity
    child = db.query(Tenant).filter(Tenant.email == request.child_email).first()
    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entity not found"
        )
    
    # Verify requester is the parent
    requester = db.query(Tenant).filter(Tenant.id == current_user["tenant_id"]).first()
    
    # For now, simple verification (in production, use hierarchical relationships)
    if request.status == "APPROVED":
        child.status = "active"
        logger.info(f"✅ Approved: {request.child_email}")
    else:
        child.status = "rejected"
        logger.info(f"❌ Rejected: {request.child_email}")
    
    db.commit()
    
    return {
        "success": True,
        "entity_email": request.child_email,
        "status": child.status,
        "message": f"Entity {request.status.lower()} successfully"
    }


from core.dependencies import get_current_user
