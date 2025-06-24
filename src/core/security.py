from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from fastapi import HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError

from .config import get_settings
from ..models.user import TokenPayload, User

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/auth/login")

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hashed password"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)

async def validate_token(token: str = Security(oauth2_scheme)) -> User:
    """Validate JWT token and return user"""
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    from ..services.user import UserService
    user_service = UserService()
    user = await user_service.get_by_id(token_data.sub)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

async def validate_conversation_access(conversation_id: str, user: User) -> bool:
    """Validate user's access to a conversation"""
    from ..services.conversation import ConversationService
    conversation_service = ConversationService()
    
    # Check if user has access to the conversation
    has_access = await conversation_service.check_user_access(conversation_id, user)
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this conversation"
        )
    
    return True

async def validate_agent_access(agent_id: str, user: User) -> bool:
    """Validate user's access to agent operations"""
    if not user.is_admin and not user.is_supervisor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for agent operations"
        )
    return True

async def validate_tool_access(tool_name: str, user: User) -> bool:
    """Validate user's access to a specific tool"""
    from ..services.tools import ToolsService
    tools_service = ToolsService()
    
    # Get tool permissions
    tool_permissions = await tools_service.get_tool_permissions(tool_name)
    
    # Check if user has required role/permissions
    if not any(role in user.roles for role in tool_permissions.allowed_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions to use tool: {tool_name}"
        )
    
    return True

async def validate_metrics_access(user: User, metric_type: str = None) -> bool:
    """Validate user's access to metrics"""
    if metric_type == "business":
        if not user.is_admin and not user.has_role("business_analyst"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for business metrics"
            )
    elif metric_type == "export":
        if not user.is_admin and not user.has_role("metrics_export"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for metrics export"
            )
    
    return True