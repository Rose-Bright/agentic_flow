from typing import Any, Dict, Optional
from fastapi import HTTPException, status

class APIException(HTTPException):
    """Base API exception class"""
    def __init__(
        self,
        status_code: int,
        detail: str,
        code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.code = code

class AuthenticationError(APIException):
    """Authentication-related errors"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            code="AUTHENTICATION_ERROR",
            headers={"WWW-Authenticate": "Bearer"}
        )

class AuthorizationError(APIException):
    """Authorization-related errors"""
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            code="AUTHORIZATION_ERROR"
        )

class ConversationError(APIException):
    """Conversation-related errors"""
    def __init__(self, detail: str, code: str = "CONVERSATION_ERROR"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            code=code
        )

class AgentError(APIException):
    """Agent-related errors"""
    def __init__(self, detail: str, code: str = "AGENT_ERROR"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            code=code
        )

class ToolExecutionError(APIException):
    """Tool execution errors"""
    def __init__(self, detail: str, code: str = "TOOL_EXECUTION_ERROR"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            code=code
        )

class ValidationError(APIException):
    """Data validation errors"""
    def __init__(self, detail: str, code: str = "VALIDATION_ERROR"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            code=code
        )

class ResourceNotFoundError(APIException):
    """Resource not found errors"""
    def __init__(self, detail: str = "Resource not found", code: str = "NOT_FOUND"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            code=code
        )

class ServiceUnavailableError(APIException):
    """Service unavailability errors"""
    def __init__(self, detail: str = "Service temporarily unavailable"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            code="SERVICE_UNAVAILABLE"
        )

class RateLimitError(APIException):
    """Rate limiting errors"""
    def __init__(self, detail: str = "Too many requests"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            code="RATE_LIMIT_EXCEEDED",
            headers={"Retry-After": "60"}
        )

class DatabaseError(APIException):
    """Database-related errors"""
    def __init__(self, detail: str = "Database error occurred"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            code="DATABASE_ERROR"
        )

class ExternalServiceError(APIException):
    """External service integration errors"""
    def __init__(self, detail: str, service_name: str):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
            code=f"{service_name.upper()}_SERVICE_ERROR"
        )