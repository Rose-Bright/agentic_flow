# Re-export auth functions from api.auth for core module compatibility
from ..api.auth import (
    get_current_user,
    get_current_active_user,
    User,
    UserInDB,
    Token,
    TokenData,
    authenticate_user,
    create_access_token,
    verify_password,
    get_password_hash
)

__all__ = [
    "get_current_user",
    "get_current_active_user", 
    "User",
    "UserInDB",
    "Token",
    "TokenData",
    "authenticate_user",
    "create_access_token",
    "verify_password",
    "get_password_hash"
]