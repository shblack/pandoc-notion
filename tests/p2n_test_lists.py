"""
Tests for list block conversion using pandoc_notion.filter.

These tests focus on the conversion of markdown lists to Notion list blocks,
including bullet lists, numbered lists, todo lists, and nested structures.

Expected Notion API block structures being validated:

For bulleted lists:
{
  "object": "block",
  "type": "bulleted_list_item",
  "bulleted_list_item": {
    "rich_text": [{
      "type": "text",
      "text": { "content": "List item text" },
      "annotations": {
        "bold": false,
        "italic": false,
        "strikethrough": false,
        "underline": false,
        "code": false,
        "color": "default"
      }
    }],
    "color": "default"
  }
}

For numbered lists:
{
  "object": "block",
  "type": "numbered_list_item",
  "numbered_list_item": {
    "rich_text": [{
      "type": "text",
      "text": { "content": "List item text" },
      "annotations": {
        "bold": false,
        "italic": false,
        "strikethrough": false,
        "underline": false,
        "code": false,
        "color": "default"
      }
    }],
    "color": "default"
  }
}

For todo lists:
{
  "object": "block",
  "type": "to_do",
  "to_do": {
    "rich_text": [{
      "type": "text",
      "text": { "content": "Todo item text" },
      "annotations": {
        "bold": false,
        "italic": false,
        "strikethrough": false,
        "underline": false,
        "code": false,
        "color": "default"
      }
    }],
    "color": "default",
    "checked": false
  }
}
"""

import pytest
from conftest import store_example

from pandoc_notion.filter import Filter, convert_markdown_to_notion
from pandoc_notion.registry import ManagerRegistry
from pandoc_notion.managers.registry_mixin import set_registry


@pytest.fixture(autouse=True)
def setup_registry():
    """
    Set up registry with default managers for all tests.
    
    This fixture runs automatically before each test to ensure
    that the registry is properly initialized.
    """
    registry = ManagerRegistry()
    set_registry(registry)  # Connect the registry to our managers
    return registry


# Helper functions for validating block structure

def validate_basic_block_structure(block, block_type):
    """Validate that a block has the basic structure expected in the Notion API."""
    assert block["object"] == "block"
    assert block["type"] == block_type
    assert block_type in block
    
    # Check rich_text exists and has expected structure
    assert "rich_text" in block[block_type]
    assert isinstance(block[block_type]["rich_text"], list)
    assert len(block[block_type]["rich_text"]) > 0
    
    # Validate first rich_text item
    rich_text = block[block_type]["rich_text"][0]
    assert "type" in rich_text
    assert rich_text["type"] == "text"
    assert "text" in rich_text
    assert "content" in rich_text["text"]
    
    # Check annotations
    assert "annotations" in rich_text
    
    # Check color
    assert "color" in block[block_type]
    assert block[block_type]["color"] == "default"


def validate_list_item_content(block, expected_text, block_type):
    """Validate that a list item has the expected text content."""
    rich_text = block[block_type]["rich_text"][0]
    assert expected_text in rich_text["text"]["content"]


def validate_todo_item(block, expected_text, expected_checked):
    """Validate that a todo item has expected text and checked status."""
    validate_basic_block_structure(block, "to_do")
    validate_list_item_content(block, expected_text, "to_do")
    
    # Check checked status
    assert "checked" in block["to_do"]
    assert block["to_do"]["checked"] == expected_checked


def test_basic_bullet_list(request):
    """Test that a basic bullet list converts correctly."""
    markdown = """
- First item
- Second item
- Third item
"""
    result = convert_markdown_to_notion(markdown)
    blocks = result["children"]
    
    # Should have 3 list items
    assert len(blocks) == 3
    
    # Check that all blocks are bulleted list items
    for i, block in enumerate(blocks):
        # Basic structure checks
        validate_basic_block_structure(block, "bulleted_list_item")
        
        # Check content based on index
        if i == 0:
            validate_list_item_content(block, "First item", "bulleted_list_item")
        elif i == 1:
            validate_list_item_content(block, "Second item", "bulleted_list_item")
        elif i == 2:
            validate_list_item_content(block, "Third item", "bulleted_list_item")
    
    # Store a representative example
    store_example(request, {
        'markdown': markdown.strip(),
        'notion_api': blocks[0],
        'notes': 'Basic bullet list structure in Notion API format'
    })


def test_basic_numbered_list(request):
    """Test that a basic numbered list converts correctly."""
    markdown = """
1. First item
2. Second item
3. Third item
"""
    result = convert_markdown_to_notion(markdown)
    blocks = result["children"]
    
    # Should have 3 list items
    assert len(blocks) == 3
    
    # Check that all blocks are numbered list items
    for i, block in enumerate(blocks):
        # Basic structure checks
        validate_basic_block_structure(block, "numbered_list_item")
        
        # Check content based on index
        if i == 0:
            validate_list_item_content(block, "First item", "numbered_list_item")
        elif i == 1:
            validate_list_item_content(block, "Second item", "numbered_list_item")
        elif i == 2:
            validate_list_item_content(block, "Third item", "numbered_list_item")
    
    # Store a representative example
    store_example(request, {
        'markdown': markdown.strip(),
        'notion_api': blocks[0],
        'notes': 'Basic numbered list structure in Notion API format'
    })


def test_todo_list(request):
    """Test that a list with checkbox characters converts to todo items."""
    markdown = """
- ☐ Unchecked todo item
- ☒ Checked todo item
- Regular bullet item
"""
    result = convert_markdown_to_notion(markdown)
    blocks = result["children"]
    
    # Should have 3 list items
    assert len(blocks) == 3
    
    # First item should be an unchecked todo
    validate_todo_item(blocks[0], "Unchecked todo item", False)
    
    # Second item should be a checked todo
    validate_todo_item(blocks[1], "Checked todo item", True)
    
    # Third item should be a regular bullet item
    validate_basic_block_structure(blocks[2], "bulleted_list_item")
    validate_list_item_content(blocks[2], "Regular bullet item", "bulleted_list_item")
    
    # Store a representative example
    store_example(request, {
        'markdown': markdown.strip(),
        'notion_api': [blocks[0], blocks[1]],
        'notes': 'Todo list items with checked and unchecked status'
    })


def test_mixed_list_types(request):
    """Test that a list with mixed item types converts correctly."""
    markdown = """
- ☐ Todo 1 (unchecked)
- Regular bullet item
- ☒ Todo 2 (checked)
"""
    result = convert_markdown_to_notion(markdown)
    blocks = result["children"]
    
    # Should have 3 list items
    assert len(blocks) == 3
    
    # First item should be an unchecked todo
    validate_todo_item(blocks[0], "Todo 1 (unchecked)", False)
    
    # Second item should be a regular bullet
    validate_basic_block_structure(blocks[1], "bulleted_list_item")
    validate_list_item_content(blocks[1], "Regular bullet item", "bulleted_list_item")
    
    # Third item should be a checked todo
    validate_todo_item(blocks[2], "Todo 2 (checked)", True)
    
    # Store a representative example
    store_example(request, {
        'markdown': markdown.strip(),
        'notion_api': blocks,
        'notes': 'Mixed list with todo and bullet items'
    })


def test_nested_lists(request):
    """Test that nested lists convert correctly."""
    markdown = """
- First level
  - Second level
    - ☐ Todo at third level
- Back to first level
  - ☒ Checked todo at second level
"""
    result = convert_markdown_to_notion(markdown)
    blocks = result["children"]
    
    # We should have blocks with children
    # Look for child blocks for nested items
    
    # Find a block with children
    blocks_with_children = [b for b in blocks if "has_children" in b and b["has_children"]]
    
    # If we have blocks with children, validate the nesting structure
    if blocks_with_children:
        # Validate parent-child structure
        parent = blocks_with_children[0]
        assert parent["type"] == "bulleted_list_item"
        assert "children" in parent["bulleted_list_item"]
        
        # Check children
        children = parent["bulleted_list_item"]["children"]
        assert len(children) > 0
        
        # Validate child structure
        child = children[0]
        assert "object" in child
        assert child["object"] == "block"
        
        # Store example of nested structure
        store_example(request, {
            'markdown': markdown.strip(),
            'notion_api': parent,
            'notes': 'Nested list structure with parent-child relationship'
        })
    else:
        # If children are represented as separate blocks with indentation
        # Just validate we have the expected blocks
        assert len(blocks) >= 4
        
        # First block should be first level
        validate_basic_block_structure(blocks[0], "bulleted_list_item")
        validate_list_item_content(blocks[0], "First level", "bulleted_list_item")
        
        # Check for todo items in the list
        todo_blocks = [b for b in blocks if b["type"] == "to_do"]
        assert len(todo_blocks) >= 2
        
        # One todo should be checked and one unchecked
        unchecked_todos = [t for t in todo_blocks if not t["to_do"]["checked"]]
        checked_todos = [t for t in todo_blocks if t["to_do"]["checked"]]
        assert len(unchecked_todos) >= 1
        assert len(checked_todos) >= 1
        
        # Store example of flat structure
        store_example(request, {
            'markdown': markdown.strip(),
            'notion_api': blocks[:4],
            'notes': 'Nested list represented as flat structure with indentation markers'
        })


def test_numbered_list_with_todos(request):
    """Test that a numbered list with todo items converts correctly."""
    markdown = """
1. First numbered item
2. ☐ Todo item in numbered list
3. ☒ Checked todo in numbered list
4. Last numbered item
"""
    result = convert_markdown_to_notion(markdown)
    blocks = result["children"]
    
    # Should have 4 list items
    assert len(blocks) == 4
    
    # First item should be numbered
    validate_basic_block_structure(blocks[0], "numbered_list_item")
    validate_list_item_content(blocks[0], "First numbered item", "numbered_list_item")
    
    # Second item should be an unchecked todo
    validate_todo_item(blocks[1], "Todo item in numbered list", False)
    
    # Third item should be a checked todo
    validate_todo_item(blocks[2], "Checked todo in numbered list", True)
    
    # Fourth item should be numbered
    validate_basic_block_structure(blocks[3], "numbered_list_item")
    validate_list_item_content(blocks[3], "Last numbered item", "numbered_list_item")
    
    # Store a representative example
    store_example(request, {
        'markdown': markdown.strip(),
        'notion_api': blocks,
        'notes': 'Numbered list with todo items mixed in'
    })

