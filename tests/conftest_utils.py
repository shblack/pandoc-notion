"""
Shared utility functions for testing in notion-pandoc.

This module contains utility functions that are shared across
different test modules, including AST formatting, JSON formatting,
and debug state management.
"""

import os
import json
from dataclasses import dataclass
from typing import Any, Optional, List

import panflute as pf


def format_ast(node: Any, indent: int = 0) -> str:
    """Format a panflute AST node as a nicely indented string."""
    lines = _format_ast_lines(node, indent)
    return "\n".join(lines)


def _format_ast_lines(node: Any, indent: int = 0) -> List[str]:
    """Helper to format AST node as a list of indented lines."""
    result = []
    indent_str = "  " * indent
    
    # Handle lists/containers of nodes
    if isinstance(node, list) or (hasattr(node, "__iter__") and not isinstance(node, str)):
        for item in node:
            result.extend(_format_ast_lines(item, indent))
        return result
    
    # Get node type
    node_type = type(node).__name__
    
    # Handle specific node types
    if isinstance(node, pf.Str):
        result.append(f"{indent_str}{node_type}(\"{node.text}\")")
    elif isinstance(node, (pf.Space, pf.LineBreak)):
        result.append(f"{indent_str}{node_type}")
    elif isinstance(node, pf.Code):
        result.append(f"{indent_str}{node_type}(\"{node.text}\")")
    elif isinstance(node, pf.CodeBlock):
        # Enhanced CodeBlock formatting with language, text and attributes
        attrs = []
        
        # Add language if available
        language = "none"
        if node.classes:
            language = node.classes[0]
        attrs.append(f'language="{language}"')
        
        # Add text content (truncate if too long)
        text = node.text
        if len(text) > 100:
            text = text[:97] + "..."
        # Escape quotes in text
        text = text.replace('"', '\\"').replace('\n', '\\n')
        attrs.append(f'text="{text}"')
        
        # Add other attributes if available
        if node.attributes:
            for key, value in node.attributes.items():
                attrs.append(f'{key}="{value}"')
        
        result.append(f"{indent_str}{node_type}({', '.join(attrs)})")
        
    elif hasattr(node, "content") and node.content:
        # Node with content (like Strong, Emph, etc.)
        result.append(f"{indent_str}{node_type}")
        result.extend(_format_ast_lines(node.content, indent + 1))
    else:
        # Add more specific handling for other node types with attributes
        attr_str = ""
        if hasattr(node, "attributes") and node.attributes:
            attr_items = []
            for k, v in node.attributes.items():
                attr_items.append(f'{k}="{v}"')
            if attr_items:
                attr_str = f"({', '.join(attr_items)})"
        
        result.append(f"{indent_str}{node_type}{attr_str}")
    
    return result


def format_json(obj: Any) -> str:
    """Format JSON with nice indentation and sorting."""
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False)


def format_code_preview(text: str, max_length: int = 60) -> str:
    """Format a code snippet for preview, truncating if too long."""
    if not text:
        return '""'
    
    if len(text) <= max_length:
        return f'"{text}"'
    
    preview = text[:max_length - 3] + "..."
    return f'"{preview}"'


def format_markdown(text: str) -> str:
    """Format markdown with visible newlines and consistent spacing."""
    if not text:
        return ""
    
    # Replace newlines with visible indicator
    text = text.replace("\n", "↵\n")
    
    # Ensure consistent line endings
    text = text.rstrip()
    return text + "↵\n"


def is_debug_enabled(flag: str) -> bool:
    """Check if a specific debug flag is enabled.
    
    Args:
        flag: Debug flag name (e.g., 'DEBUG_TESTS_SHOW_INPUT')
        
    Returns:
        True if the flag is enabled or DEBUG_TESTS_SHOW_ALL is enabled
    """
    return os.environ.get(flag) == "1" or os.environ.get("DEBUG_TESTS_SHOW_ALL") == "1"


@dataclass
class DebugState:
    """State holder for debug information during test execution."""
    input: Optional[Any] = None
    ast: Optional[Any] = None 
    output: Optional[Any] = None


# Helper function for storing examples in documentation
def store_example(request, data):
    """
    Store a test example for documentation.
    
    This function does nothing by default but can be used to collect
    examples for generating documentation.
    
    Args:
        request: The pytest request fixture
        data: The example data to store
    """
    # This function is a stub - override in conftest if needed
    pass


def format_ast_repr(node: Any, indent: int = 0) -> str:
    """
    Format a panflute AST node using the built-in representation.
    Shows content for all nodes including Math, Str, etc.
    
    Args:
        node: A panflute node or list of nodes
        indent: Current indentation level
        
    Returns:
        Formatted string representation of the AST
    """
    lines = _format_ast_lines_repr(node, indent=0)
    return "\n".join(lines)


def _format_ast_lines_repr(node: Any, indent: int = 0) -> List[str]:
    """
    Format a panflute AST node as a list of strings with proper indentation.
    Uses panflute's built-in representation for all nodes.
    
    Args:
        node: A panflute node or list of nodes
        indent: Current indentation level
        
    Returns:
        List of strings representing the formatted AST
    """
    result = []
    indent_str = "  " * indent
    
    # Handle lists/containers of nodes
    if isinstance(node, list) or (hasattr(node, "__iter__") and not isinstance(node, str)):
        for item in node:
            result.extend(_format_ast_lines_repr(item, indent))
        return result
    
    # Use panflute's built-in representation for each node
    result.append(f"{indent_str}{repr(node)}")
    
    return result

