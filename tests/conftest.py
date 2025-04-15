"""
Test configuration and debug utilities for notion-pandoc.

This module provides test utilities and debug decorators for testing the
notion-pandoc conversion process in both directions:
- Notion to Pandoc (n2p): Converting Notion JSON to Pandoc AST/Markdown
- Pandoc to Notion (p2n): Converting Markdown to Pandoc AST to Notion JSON

Environment variables:
    DEBUG_TESTS_SHOW_INPUT=1: Show the input representation
    DEBUG_TESTS_SHOW_AST=1: Show the intermediate AST
    DEBUG_TESTS_SHOW_OUTPUT=1: Show the final output
    DEBUG_TESTS_SHOW_ALL=1: Enable all debug output (equivalent to setting all above flags)
    NOTION_TOKEN: API token for Notion integration tests
    NOTION_TEST_PARENT_PAGE_ID: ID of a Notion page to use as parent for tests
"""

# Import utilities from the modular components
from tests.conftest_utils import (
    DebugState,
    format_ast,
    format_json,
    format_markdown,
    format_code_preview,
    is_debug_enabled,
    store_example,
)

# Import debug decorators
from tests.conftest_n2p import debug_n2p
from tests.conftest_p2n import debug_p2n

# Import Notion API fixtures
from tests.conftest_notion import (
    debug_notion_page,
    normalize_text,
)

# Import Notion integration testing fixtures
from conftest_notion_integration import (
    notion_client,
    notion_parent_id,
    notion_test,
)

# Register custom pytest marks
import pytest

# Filter common warnings and register custom marks
def pytest_configure(config):
    """Configure pytest with custom settings and warning filters."""
    # Register the notion_integration mark properly
    config.addinivalue_line(
        "markers", 
        "notion_integration: mark tests that require Notion API access"
    )
    
    # Filter warnings
    config.addinivalue_line(
        "filterwarnings",
        "ignore::pytest.PytestReturnNotNoneWarning"
    )

# Export all components
__all__ = [
    # Debug decorators
    'debug_n2p',
    'debug_p2n',
    
    # Debug state and utilities
    'DebugState',
    'is_debug_enabled',
    
    # Formatting utilities
    'format_ast',
    'format_json',
    'format_markdown',
    'format_code_preview',
    
    # Documentation helpers
    'store_example',
    
    # Notion API fixtures
    'notion_client',
    'notion_parent_id',
    'debug_notion_page',
    'normalize_text',
    'notion_test',
]

