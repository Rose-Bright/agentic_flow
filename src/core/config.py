"""
Application configuration management
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Application Configuration
    app_name: str = Field(default="contact-center-agentic-flow")
    app_version: str = Field(default="1.0.0")
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_prefix: str = Field(default="/api/v1")
    cors_origins: List[str] = Field(default=["*"])
    
    # Security
    secret_key: str = Field(default="change-this-secret-key")
    access_token_expire_minutes: int = Field(default=30)
    algorithm: str = Field(default="HS256")
    
    # Database Configuration
    database_url: str = Field(default="postgresql://user:pass@localhost/db")
    database_pool_size: int = Field(default=10)
    database_max_overflow: int = Field(default=20)
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_max_connections: int = Field(default=10)
    
    # Google Cloud / Vertex AI Configuration
    google_cloud_project: Optional[str] = Field(default=None)
    google_cloud_region: str = Field(default="us-central1")
    google_application_credentials: Optional[str] = Field(default=None)
    
    # Vertex AI Models
    gemini_pro_model: str = Field(default="gemini-pro")
    claude_3_model: str = Field(default="claude-3-sonnet-20240229")
    custom_model_endpoint: Optional[str] = Field(default=None)
    
    # External APIs
    twilio_account_sid: Optional[str] = Field(default=None)
    twilio_auth_token: Optional[str] = Field(default=None)
    sendgrid_api_key: Optional[str] = Field(default=None)
    
    # Monitoring & Observability
    prometheus_port: int = Field(default=9090)
    jaeger_endpoint: Optional[str] = Field(default=None)
    cloud_monitoring_enabled: bool = Field(default=False)
    
    # Feature Flags
    enable_voice_channel: bool = Field(default=True)
    enable_email_channel: bool = Field(default=True)
    enable_chat_channel: bool = Field(default=True)
    enable_social_media_channel: bool = Field(default=False)
    
    # Performance Tuning
    max_concurrent_conversations: int = Field(default=1000)
    agent_timeout_seconds: int = Field(default=30)
    tool_timeout_seconds: int = Field(default=10)
    cache_ttl_seconds: int = Field(default=3600)


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings()