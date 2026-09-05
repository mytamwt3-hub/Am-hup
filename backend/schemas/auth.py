from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class RegisterRequest(BaseModel):
    """Company/Establishment/Branch registration"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2)
    phone: str = Field(..., regex=r'^\+?[0-9]{10,15}$')
    entity_type: str = Field(..., regex=r'^(company|establishment|branch)$')
    parent_email: Optional[str] = None  # For establishment/branch registration
    entity_name: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Authentication token response"""
    access_token: str
    token_type: str = "bearer"
    tenant_id: str
    user_email: str
    entity_type: str


class ApprovalRequest(BaseModel):
    """Approve establishment or branch"""
    child_email: str = EmailStr
    status: str = Field(..., regex=r'^(APPROVED|REJECTED)$')
    notes: Optional[str] = None
