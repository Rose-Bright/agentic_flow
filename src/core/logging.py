"""
Logging configuration for the Contact Center system
"""

import logging
import sys
from typing import Dict, Any

import structlog
from pythonjsonlogger import jsonlogger

from src.core.config import get_settings


def setup_logging(log_level: str = "INFO") -> None:
    """Setup structured logging configuration"""
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if get_settings().debug 
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance"""
    return structlog.get_logger(name)


class ConversationLogger:
    """Logger for conversation-specific events"""
    
    def __init__(self, conversation_id: str, user_id: str = None):
        self.logger = get_logger("conversation")
        self.conversation_id = conversation_id
        self.user_id = user_id
    
    def log_agent_invocation(self, agent_name: str, input_data: Dict[str, Any]):
        """Log agent invocation"""
        self.logger.info(
            "Agent invoked",
            conversation_id=self.conversation_id,
            user_id=self.user_id,
            agent_name=agent_name,
            input_data=input_data
        )
    
    def log_agent_response(self, agent_name: str, response: Dict[str, Any], 
                          duration_ms: float):
        """Log agent response"""
        self.logger.info(
            "Agent response",
            conversation_id=self.conversation_id,
            user_id=self.user_id,
            agent_name=agent_name,
            response=response,
            duration_ms=duration_ms
        )
    
    def log_escalation(self, from_agent: str, to_agent: str, reason: str):
        """Log agent escalation"""
        self.logger.info(
            "Agent escalation",
            conversation_id=self.conversation_id,
            user_id=self.user_id,
            from_agent=from_agent,
            to_agent=to_agent,
            reason=reason
        )
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Log error with context"""
        self.logger.error(
            "Conversation error",
            conversation_id=self.conversation_id,
            user_id=self.user_id,
            error=str(error),
            error_type=type(error).__name__,
            context=context or {}
        )