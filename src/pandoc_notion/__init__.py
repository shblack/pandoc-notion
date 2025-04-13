"""
Pandoc filter for converting documents to Notion syntax.

This package provides a modular approach to convert Pandoc documents to Notion format
using managers for different block types.
"""

from .utils.debug import set_log_level, get_log_level, LogLevel

__all__ = ["set_log_level", "get_log_level", "LogLevel"]

