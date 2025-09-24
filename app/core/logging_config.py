import logging
import logging.config
import sys
from datetime import datetime
from typing import Dict, Any
from app.core.config import get_settings


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""

    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }

    def format(self, record):
        # Add color to level name
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"

        return super().format(record)


class RequestResponseFilter(logging.Filter):
    """Filter for request/response logging"""

    def filter(self, record):
        return hasattr(record, 'request_id') or hasattr(record, 'response_data')


def setup_logging():
    """Setup logging configuration based on environment settings"""
    settings = get_settings()
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Create logs directory if it doesn't exist
    import os
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Logging configuration
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                'format': '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(funcName)s() | %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'simple': {
                'format': '%(asctime)s | %(levelname)-8s | %(message)s',
                'datefmt': '%H:%M:%S'
            },
            'colored': {
                '()': ColoredFormatter,
                'format': '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
                'datefmt': '%H:%M:%S'
            },
            'json': {
                'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "function": "%(funcName)s", "line": %(lineno)d, "message": "%(message)s"}',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'filters': {
            'request_response': {
                '()': RequestResponseFilter,
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'colored',
                'stream': sys.stdout
            },
            'file_all': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': logging.DEBUG,
                'formatter': 'detailed',
                'filename': f'{log_dir}/chatbot.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5
            },
            'file_errors': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': logging.ERROR,
                'formatter': 'detailed',
                'filename': f'{log_dir}/errors.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 3
            },
            'file_tools': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': logging.INFO,
                'formatter': 'detailed',
                'filename': f'{log_dir}/tools.log',
                'maxBytes': 5242880,  # 5MB
                'backupCount': 3
            },
            'file_requests': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': logging.DEBUG,
                'formatter': 'json',
                'filename': f'{log_dir}/requests.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5
            }
        },
        'loggers': {
            # Root logger
            '': {
                'level': log_level,
                'handlers': ['console', 'file_all'],
                'propagate': False
            },
            # Application loggers
            'app': {
                'level': logging.DEBUG,
                'handlers': ['console', 'file_all'],
                'propagate': False
            },
            'app.services': {
                'level': logging.DEBUG,
                'handlers': ['console', 'file_all', 'file_requests'],
                'propagate': False
            },
            'app.tools': {
                'level': logging.INFO,
                'handlers': ['console', 'file_all', 'file_tools'],
                'propagate': False
            },
            'app.api': {
                'level': logging.INFO,
                'handlers': ['console', 'file_all', 'file_requests'],
                'propagate': False
            },
            'app.chat': {
                'level': logging.INFO,
                'handlers': ['console', 'file_all'],
                'propagate': False
            },
            'app.utils.error_handlers': {
                'level': logging.WARNING,
                'handlers': ['console', 'file_all', 'file_errors'],
                'propagate': False
            },
            # External libraries
            'httpx': {
                'level': logging.WARNING,
                'handlers': ['file_all'],
                'propagate': False
            },
            'requests': {
                'level': logging.WARNING,
                'handlers': ['file_all'],
                'propagate': False
            },
            'urllib3': {
                'level': logging.WARNING,
                'handlers': ['file_all'],
                'propagate': False
            },
            'openai': {
                'level': logging.INFO,
                'handlers': ['file_all'],
                'propagate': False
            }
        }
    }

    logging.config.dictConfig(config)

    # Log startup info
    logger = logging.getLogger('app')
    logger.info(f"🚀 Logging initialized with level: {settings.log_level}")
    logger.info(f"📁 Log files location: {os.path.abspath(log_dir)}/")

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name"""
    return logging.getLogger(name)


def log_request_start(logger: logging.Logger, method: str, endpoint: str, data: Any = None):
    """Log the start of a request"""
    request_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    logger.debug(f"🔵 REQUEST START [{request_id}] {method} {endpoint}",
                 extra={'request_id': request_id, 'method': method, 'endpoint': endpoint})
    if data and logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"📝 REQUEST DATA [{request_id}]: {data}", extra={'request_id': request_id})
    return request_id


def log_request_end(logger: logging.Logger, request_id: str, status_code: int = None, response_data: Any = None):
    """Log the end of a request"""
    status_emoji = "✅" if (status_code and 200 <= status_code < 300) else "❌" if status_code else "🔵"
    status_text = f" [{status_code}]" if status_code else ""
    logger.debug(f"{status_emoji} REQUEST END [{request_id}]{status_text}",
                 extra={'request_id': request_id, 'status_code': status_code})
    if response_data and logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"📤 RESPONSE DATA [{request_id}]: {response_data}",
                     extra={'request_id': request_id, 'response_data': response_data})


def log_tool_call(logger: logging.Logger, tool_name: str, function_name: str, args: Dict[str, Any]):
    """Log a tool function call"""
    logger.info(f"🔧 TOOL CALL: {tool_name}.{function_name}({args})")


def log_tool_result(logger: logging.Logger, tool_name: str, function_name: str, success: bool, result_length: int = None):
    """Log a tool function result"""
    status_emoji = "✅" if success else "❌"
    result_info = f" (response length: {result_length})" if result_length else ""
    logger.info(f"{status_emoji} TOOL RESULT: {tool_name}.{function_name}{result_info}")


def log_error_with_context(logger: logging.Logger, error: Exception, context: str, extra_data: Dict[str, Any] = None):
    """Log an error with context and extra data"""
    error_data = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'context': context
    }
    if extra_data:
        # Avoid conflicts with reserved logging fields
        for key, value in extra_data.items():
            if key not in ['message', 'asctime']:  # Reserved logging fields
                error_data[key] = value
            else:
                error_data[f'user_{key}'] = value  # Prefix with 'user_' to avoid conflicts

    logger.error(f"💥 ERROR in {context}: {type(error).__name__}: {error}", extra=error_data)

    # Log stack trace at debug level
    if logger.isEnabledFor(logging.DEBUG):
        import traceback
        logger.debug(f"📚 STACK TRACE for {context}:\n{traceback.format_exc()}")


# Initialize logging on module import
setup_logging()