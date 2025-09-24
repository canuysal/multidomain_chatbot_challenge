import logging
from typing import Optional, Dict, Any
from functools import wraps
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class ChatbotError(Exception):
    """Base exception class for chatbot errors"""

    def __init__(self, message: str, error_code: str = "GENERAL_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.utcnow()
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for API responses"""
        return {
            "error": True,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


class APIConnectionError(ChatbotError):
    """Raised when external API connections fail"""

    def __init__(self, service: str, message: str = None, details: Optional[Dict[str, Any]] = None):
        default_message = f"Failed to connect to {service} service"
        super().__init__(
            message or default_message,
            error_code="API_CONNECTION_ERROR",
            details={**(details or {}), "service": service}
        )


class DatabaseError(ChatbotError):
    """Raised when database operations fail"""

    def __init__(self, operation: str, message: str = None, details: Optional[Dict[str, Any]] = None):
        default_message = f"Database {operation} operation failed"
        super().__init__(
            message or default_message,
            error_code="DATABASE_ERROR",
            details={**(details or {}), "operation": operation}
        )


class ValidationError(ChatbotError):
    """Raised when input validation fails"""

    def __init__(self, field: str, message: str = None, details: Optional[Dict[str, Any]] = None):
        default_message = f"Validation failed for field: {field}"
        super().__init__(
            message or default_message,
            error_code="VALIDATION_ERROR",
            details={**(details or {}), "field": field}
        )


class OpenAIError(ChatbotError):
    """Raised when OpenAI API calls fail"""

    def __init__(self, message: str = None, details: Optional[Dict[str, Any]] = None):
        default_message = "OpenAI service error occurred"
        super().__init__(
            message or default_message,
            error_code="OPENAI_ERROR",
            details=details
        )


def handle_tool_errors(tool_name: str):
    """Decorator to handle errors in tool functions"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except APIConnectionError as e:
                logger.error(f"{tool_name} API connection error: {e.message}")
                return f"Sorry, I'm having trouble connecting to the {tool_name} service right now. Please try again later."
            except ValidationError as e:
                logger.warning(f"{tool_name} validation error: {e.message}")
                return f"Please provide valid input for {tool_name}. {e.message}"
            except Exception as e:
                logger.error(f"Unexpected error in {tool_name}: {str(e)}\n{traceback.format_exc()}")
                return f"I encountered an unexpected error while using {tool_name}. Please try again or contact support."

        return wrapper

    return decorator


def handle_api_errors(func):
    """Decorator to handle errors in API endpoints"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ChatbotError as e:
            logger.error(f"API error: {e.message}")
            raise e  # Re-raise known errors to be handled by FastAPI
        except Exception as e:
            logger.error(f"Unexpected API error: {str(e)}\n{traceback.format_exc()}")
            raise ChatbotError(
                "An unexpected error occurred. Please try again.",
                error_code="UNEXPECTED_ERROR",
                details={"original_error": str(e)}
            )

    return wrapper


def handle_database_errors(operation: str):
    """Decorator to handle database operation errors"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Database {operation} error: {str(e)}\n{traceback.format_exc()}")
                raise DatabaseError(
                    operation=operation,
                    message=f"Failed to {operation} data in the database",
                    details={"original_error": str(e)}
                )

        return wrapper

    return decorator


def log_request_response(tool_name: str):
    """Decorator to log requests and responses for debugging"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.info(f"{tool_name} called with args: {args[:2]}...")  # Log first 2 args only
            try:
                result = func(*args, **kwargs)
                logger.info(f"{tool_name} completed successfully")
                return result
            except Exception as e:
                logger.error(f"{tool_name} failed: {str(e)}")
                raise

        return wrapper

    return decorator


class ErrorHandler:
    """Centralized error handling utilities"""

    @staticmethod
    def format_user_error(error: Exception, context: str = "") -> str:
        """Format error for user-friendly display"""
        if isinstance(error, ChatbotError):
            return error.message

        # Handle common error types
        error_str = str(error).lower()

        if "timeout" in error_str or "timed out" in error_str:
            return f"The request took too long to process. Please try again."

        if "connection" in error_str:
            return f"Unable to connect to the service. Please check your internet connection and try again."

        if "not found" in error_str or "404" in error_str:
            return f"The requested information could not be found. Please check your input and try again."

        if "unauthorized" in error_str or "401" in error_str:
            return f"Authentication failed. Please check your API configuration."

        if "rate limit" in error_str or "429" in error_str:
            return f"Service temporarily unavailable due to high demand. Please try again in a few minutes."

        # Generic error message for unknown errors
        return f"An unexpected error occurred. Please try again or contact support if the issue persists."

    @staticmethod
    def should_retry(error: Exception) -> bool:
        """Determine if an error is retryable"""
        error_str = str(error).lower()

        # Retryable errors
        retryable_keywords = [
            "timeout", "connection", "temporary", "rate limit",
            "server error", "503", "502", "429"
        ]

        return any(keyword in error_str for keyword in retryable_keywords)

    @staticmethod
    def log_error(error: Exception, context: str = "", extra_data: Optional[Dict[str, Any]] = None):
        """Log error with context and extra data"""
        error_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context
        }

        if extra_data:
            error_data.update(extra_data)

        if isinstance(error, ChatbotError):
            error_data.update(error.to_dict())

        logger.error(f"Error occurred: {error_data}")

        # Log stack trace for debugging
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Stack trace: {traceback.format_exc()}")


# Global error handler instance
error_handler = ErrorHandler()