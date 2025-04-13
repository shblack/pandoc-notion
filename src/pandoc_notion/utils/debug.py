"""
Debug utilities for notion-pandoc.
"""

import enum
import inspect
import logging
import os
import sys
from functools import wraps
from typing import Any, Callable, TypeVar, cast, Optional

# Type variable for generic function type
F = TypeVar('F', bound=Callable[..., Any])

# Debug settings
DEBUG_MAX_OUTPUT_LENGTH = 5000
DEBUG_LOG_FILE = 'pandoc_notion_debug.log'

# Configure logger
logger = logging.getLogger("pandoc_notion")


class LogLevel(enum.Enum):
    """Log level enumeration."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR


# Global log level, default to INFO if environment variable isn't set
_current_log_level = (
    LogLevel.DEBUG if os.environ.get('PANDOC_NOTION_DEBUG', '').lower() in ('1', 'true', 'yes', 'on') 
    else LogLevel.INFO
)

# Track if handlers have been set up
_handlers_configured = False


def get_log_level() -> LogLevel:
    """
    Get the current log level.
    
    Returns:
        The current log level
    """
    return _current_log_level


def _configure_handlers() -> None:
    """
    Configure logging handlers with appropriate formatting.
    Sets up console and file handlers for the logger.
    """
    global _handlers_configured
    
    if _handlers_configured:
        return
    
    # Clear any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Define detailed formatter
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(stream=sys.stderr)
    console_handler.setFormatter(detailed_formatter)
    logger.addHandler(console_handler)
    
    # File handler (always create it, but only logs at DEBUG level)
    file_handler = logging.FileHandler(DEBUG_LOG_FILE, mode='a')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    _handlers_configured = True


def set_log_level(level: LogLevel) -> None:
    """
    Set the current log level.
    
    Args:
        level: The log level to set
    """
    global _current_log_level
    _current_log_level = level
    
    # Ensure handlers are configured
    _configure_handlers()
    
    # Update logger level
    logger.setLevel(level.value)


def debug_decorator(func: F = None, max_output_length: int = None) -> F:
    """
    Decorator to log function calls with caller information, parameters, and return values.
    
    When the log level is set to DEBUG, this decorator will log:
    - Who called the function (file, function, line number)
    - What parameters were passed
    - What value was returned
    
    Args:
        func: The function to decorate
        max_output_length: Maximum length for return value output (defaults to DEBUG_MAX_OUTPUT_LENGTH)
        
    Returns:
        The wrapped function
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Skip logging if not at DEBUG level
            if _current_log_level != LogLevel.DEBUG:
                return func(*args, **kwargs)
            
            # Get caller information
            # Get caller information
            stack = inspect.stack()
            if len(stack) >= 2:
                caller_frame = stack[1]
                caller_filename = os.path.basename(caller_frame.filename)
                caller_function = caller_frame.function
                caller_lineno = caller_frame.lineno
                caller_info = f"{caller_filename}:{caller_function}:{caller_lineno}"
            else:
                caller_info = "unknown"
                
            # Get callee information (the decorated function)
            callee_filename = os.path.basename(inspect.getfile(func))
            callee_lines, callee_lineno = inspect.getsourcelines(func)
            callee_info = f"{callee_filename}:{func.__name__}:{callee_lineno}"
            # Get the class name if this is a method
            class_name = args[0].__class__.__name__ if args else ""
            function_name = f"{class_name}.{func.__name__}" if class_name else func.__name__
            
            # Format arguments for logging (skipping 'self' or 'cls' for methods)
            # Format arguments for logging (skipping 'self' or 'cls' for methods)
            skip_args = 1 if class_name else 0
            arg_str = ', '.join([
                f"{a}" for a in args[skip_args:]
            ] + [
                f"{k}={v}" for k, v in kwargs.items()
            ])
            # Log method call
            logger.debug(f"┌─ FUNCTION CALL ───────────────────────────────────────")
            logger.debug(f"│ CALLER: {caller_info}")
            logger.debug(f"│ CALLEE: {callee_info}")
            logger.debug(f"│ CALL: {function_name}({arg_str})")
            
            # Call the function
            result = func(*args, **kwargs)
            
            # Log the return value
            result_str = repr(result)
            max_length = max_output_length or DEBUG_MAX_OUTPUT_LENGTH
            if len(result_str) > max_length:
                result_str = result_str[:max_length-3] + "..."
            logger.debug(f"│ RETURN: {result_str}")
            logger.debug(f"└─ END {function_name} ───────────────────────────────────────")
            
            return result
        
        return cast(F, wrapper)
    
    # Support both @debug_decorator and @debug_decorator(max_output_length=100) syntax
    if func is None:
        return decorator
    return decorator(func)


# Alias for backward compatibility and convenience
debug = debug_decorator


def debug_conversion(func: F = None) -> F:
    """
    Specialized decorator for debugging conversion methods.
    Provides detailed inspection of the element being checked for conversion,
    including its type, attributes, and content structure.
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Skip logging if not at DEBUG level
            if _current_log_level != LogLevel.DEBUG:
                return func(*args, **kwargs)
            
            # Get the element being checked (typically first arg after self/cls)
            elem = args[1] if len(args) > 1 else None
            
            # Log detailed element information
            logger.debug(f"\nCONVERSION CHECK:")
            logger.debug(f"  Function: {func.__name__}")
            logger.debug(f"  Element Type: {type(elem).__name__}")
            logger.debug(f"  Element Dir: {dir(elem)}")
            if hasattr(elem, 'content'):
                content = getattr(elem, 'content')
                logger.debug(f"  Content Type: {type(content).__name__}")
                if content:
                    logger.debug(f"  Content Items: {[type(item).__name__ for item in content]}")
            
            # Call the function and log result
            result = func(*args, **kwargs)
            logger.debug(f"  Result: {result}\n")
            return result
            
        return cast(F, wrapper)
    
    # Support both @debug_conversion and @debug_conversion() syntax
    if func is None:
        return decorator
    return decorator(func)


def log_debug(message: str) -> None:
    """
    Log a debug message.
    
    Args:
        message: The message to log
    """
    if _current_log_level == LogLevel.DEBUG:
        logger.debug(message)


def log_info(message: str) -> None:
    """
    Log an info message.
    
    Args:
        message: The message to log
    """
    if _current_log_level.value <= LogLevel.INFO.value:
        logger.info(message)


def log_warning(message: str) -> None:
    """
    Log a warning message.
    
    Args:
        message: The message to log
    """
    if _current_log_level.value <= LogLevel.WARNING.value:
        logger.warning(message)


def log_error(message: str) -> None:
    """
    Log an error message.
    
    Args:
        message: The message to log
    """
    if _current_log_level.value <= LogLevel.ERROR.value:
        logger.error(message)
# Initialize the logger with the current log level
logger.setLevel(_current_log_level.value)
_configure_handlers()

# Log that debug module has been initialized
log_info(f"pandoc_notion debug module initialized with level: {_current_log_level.name}")
if _current_log_level == LogLevel.DEBUG:
    log_debug(f"Debug logging enabled, output will be written to console and {DEBUG_LOG_FILE}")
