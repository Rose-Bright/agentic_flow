from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator

class UserRole(BaseModel):
    """Model for user role"""
    name: str = Field(..., description="Role name")
    permissions: List[str] = Field(..., description="Role permissions")
    scope: Optional[str] = Field(None, description="Role scope")
    metadata: Dict[str, Any] = Field(default={}, description="Additional role metadata")

class UserCreate(BaseModel):
    """Model for creating a new user"""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")
    full_name: str = Field(..., description="User full name")
    roles: List[str] = Field(default=[], description="User roles")
    metadata: Dict[str, Any] = Field(default={}, description="Additional user metadata")

    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v

class User(BaseModel):
    """Model representing a user"""
    id: str = Field(..., description="User identifier")
    email: EmailStr = Field(..., description="User email")
    full_name: str = Field(..., description="User full name")
    hashed_password: str = Field(..., description="Hashed password")
    roles: List[str] = Field(default=[], description="User roles")
    is_active: bool = Field(default=True, description="Whether user is active")
    is_admin: bool = Field(default=False, description="Whether user is admin")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default={}, description="Additional user metadata")

    @property
    def is_supervisor(self) -> bool:
        """Check if user is a supervisor"""
        return "supervisor" in self.roles or self.is_admin

    def has_role(self, role: str) -> bool:
        """Check if user has specific role"""
        return role in self.roles or self.is_admin

    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        if self.is_admin:
            return True
        # In a real implementation, this would check against a role-permission mapping
        return True

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class UserUpdate(BaseModel):
    """Model for updating user information"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    roles: Optional[List[str]] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None

class Token(BaseModel):
    """Model for authentication token"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    refresh_token: Optional[str] = Field(None, description="Refresh token")

class TokenPayload(BaseModel):
    """Model for token payload"""
    sub: str = Field(..., description="Subject (user ID)")
    exp: datetime = Field(..., description="Token expiration timestamp")
    type: str = Field(default="access", description="Token type")
    roles: List[str] = Field(default=[], description="User roles")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")

class UserSession(BaseModel):
    """Model for user session"""
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    ip_address: str = Field(..., description="IP address")
    user_agent: str = Field(..., description="User agent string")
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Session start timestamp")
    last_activity: datetime = Field(default_factory=datetime.utcnow, description="Last activity timestamp")
    expires_at: datetime = Field(..., description="Session expiration timestamp")
    metadata: Dict[str, Any] = Field(default={}, description="Additional session metadata")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }