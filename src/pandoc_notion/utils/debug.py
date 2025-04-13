"""
Debug utilities for notion-pandoc.

Provides logging configuration and a debug decorator for detailed function call tracing.
"""

import enum
import inspect
import logging
import os
import sys
from functools import wraps
from typing import Any, Callable, TypeVar, cast

# Type variable for generic function type
F = TypeVar('F', bound=Callable[..., Any])

# Debug settings
DEBUG_MAX_OUTPUT_LENGTH = 5000
DEBUG_LOG_FILE = 'pandoc_notion_debug.log'

# Configure logger
logger = logging.getLogger("pandoc_notion")


class LogLevel(enum.Enum):
    """Log level enumeration for easier configuration."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR


# Global log level, default to INFO unless debug environment variable is set
_current_log_level = (
    LogLevel.DEBUG if os.environ.get('PANDOC_NOTION_DEBUG', '').lower() in ('1', 'true', 'yes', 'on') 
    else LogLevel.INFO
)


def get_log_level() -> LogLevel:
    """Get the current log level."""
    return _current_log_level


def set_log_level(level: LogLevel) -> None:
    """
    Set the debug log level and configure handlers if needed.
    
    Args:
        level: The log level to set
    """
    global _current_log_level
    _current_log_level = level
    
    # Configure handlers if not already done
    if not logger.handlers:
        # Set up formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        
        # Console handler
        console = logging.StreamHandler(stream=sys.stderr)
        console.setFormatter(formatter)
        logger.addHandler(console)
        
        # File handler for debug logs
        file_handler = logging.FileHandler(DEBUG_LOG_FILE, mode='a')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Update logger level
    logger.setLevel(level.value)


def debug_decorator(func: F = None, filename: str = None, funcname: str = None, max_output_length: int = None) -> F:
    """
    Decorator that logs detailed information about function calls and their results.
    
    When debug mode is enabled, logs:
    - Caller and callee information (file, function, line)
    - Function arguments
    - Return values
    
    Args:
        func: The function to decorate
        filename: Optional filename override for caller info
        funcname: Optional function name override for caller info
        max_output_length: Maximum length for return value output
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Skip logging if not in debug mode
            if _current_log_level != LogLevel.DEBUG:
                return func(*args, **kwargs)
            # Get caller information
            if filename or funcname:
                # Use provided information if available
                caller_file = filename or "unknown_file"
                caller_func = funcname or "unknown_func"
                caller_info = f"{caller_file}:{caller_func}"
            else:
                # Auto-detect caller information
                stack = inspect.stack()
                if len(stack) >= 2:
                    caller_frame = stack[1]
                    caller_file = os.path.basename(caller_frame.filename)
                    caller_func = caller_frame.function
                    caller_line = caller_frame.lineno
                    caller_info = f"{caller_file}:{caller_func}:{caller_line}"
                else:
                    caller_info = "unknown"
            
            # Get function information
            function_name = func.__name__
            
            # Format arguments (skip self/cls if it's a method)
            is_method = len(args) > 0 and hasattr(args[0], '__class__')
            skip_args = 1 if is_method else 0
            
            # If it's a method, include the class name
            if is_method and hasattr(args[0], '__class__'):
                function_name = f"{args[0].__class__.__name__}.{function_name}"
            
            # Format arguments for logging
            arg_str = ', '.join([
                repr(a) for a in args[skip_args:]
            ] + [
                f"{k}={repr(v)}" for k, v in kwargs.items()
            ])
            
            # Log function call
            logger.debug(f"CALL: {function_name}({arg_str}) from {caller_info}")
            
            # Call the function
            result = func(*args, **kwargs)
            
            # Format the return value
            result_str = repr(result)
            max_length = max_output_length or DEBUG_MAX_OUTPUT_LENGTH
            if len(result_str) > max_length:
                result_str = result_str[:max_length-3] + "..."
            
            # Log the return value
            logger.debug(f"RETURN: {function_name} -> {result_str}")
            
            return result
        
        return cast(F, wrapper)
    
    # Support both @debug_decorator and @debug_decorator() syntax
    if func is None:
        return decorator
    return decorator(func)


# Initialize logger with current level
set_log_level(_current_log_level)
logger.debug(f"Debug logging initialized at level {_current_log_level.name}")
