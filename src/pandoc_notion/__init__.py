"""
Pandoc filter for converting documents to Notion syntax.

This package provides a modular approach to convert Pandoc documents to Notion format
using managers for different block types.
"""

# Import log level utilities from the shared debug module
try:
    from debug import set_log_level, get_log_level, LogLevel
    __all__ = ["set_log_level", "get_log_level", "LogLevel"]
except ImportError:
    # Fallback if debug symlink isn't set up correctly
    class LogLevel: pass
    def set_log_level(level): pass
    def get_log_level(): pass
    __all__ = []

