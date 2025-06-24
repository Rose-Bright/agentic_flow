"""Middleware for the Contact Center API."""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
from datetime import datetime
import time

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable
    ):
        # Implement rate limiting logic here
        client_ip = request.client.host
        # You would implement actual rate limiting check here
        
        response = await call_next(request)
        return response

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable
    ):
        start_time = time.time()
        
        response = await call_next(request)
        
        # Calculate request processing time
        process_time = time.time() - start_time
        
        # Log request details
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "method": request.method,
            "path": request.url.path,
            "process_time": process_time,
            "client_ip": request.client.host,
            "status_code": response.status_code
        }
        
        # You would implement actual logging here
        
        return response

class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable
    ):
        # Implement security checks here
        # - Check headers
        # - Validate tokens
        # - Check IP allowlist
        # etc.
        
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        return response