"""
Integration tests for markdown_notion tool.

Tests actual conversion and uploading of content to Notion, verifying
all supported block types work correctly.
"""
import pytest
from typing import Dict, Any, List, Optional

# Fixture for test markdown content that exercises all supported features
TEST_MARKDOWN = '''# Test Document

This is a paragraph with **bold**, *italic*, ~~strikethrough~~, and `inline code`.

## Code Block
```python
def hello():
    print("Hello Notion!")
```

> This is a quote

* Bullet point 1
* Bullet point 2

1. Numbered item 1
2. Numbered item 2

Here's an equation: $E = mc^2$

And a block equation:
$$
\\frac{d}{dx}[x^n] = nx^{n-1}
$$

[A link](https://example.com)
'''

@pytest.mark.notion_integration
def test_create_page(notion_test):
    """
    Test creating a new page with all supported block types.
    
    This test:
    1. Creates a Notion page with various block types and formatting
    2. Retrieves the page content and verifies all blocks
    3. Checks specific formatting and annotations
    """
    print("[DEBUG] === Test create_page starting ===")
    
    # ===== STEP 1: Create a single test page =====
    page_id = notion_test.create_page(
        markdown_content=TEST_MARKDOWN,
        title=f"Integration Test Page - {notion_test.test_name}"
    )
    
    # Verify page exists
    page = notion_test.client.client.pages.retrieve(page_id)
    assert page["id"] == page_id, "Page creation failed"
    
    # ===== STEP 2: Retrieve blocks =====
    blocks = notion_test.client.client.blocks.children.list(page_id)
    results = blocks["results"]
    
    # Verify each block type
    block_types = [b["type"] for b in results]
    assert "heading_1" in block_types, "Missing H1"
    assert "heading_2" in block_types, "Missing H2"
    assert "paragraph" in block_types, "Missing paragraph"
    assert "code" in block_types, "Missing code block"
    assert "quote" in block_types, "Missing quote"
    assert "bulleted_list_item" in block_types, "Missing bullet list"
    assert "numbered_list_item" in block_types, "Missing numbered list"
    
    # Verify equations in paragraph content
    paragraphs = [b for b in results if b["type"] == "paragraph"]
    all_text = []
    for p in paragraphs:
        all_text.extend(p["paragraph"]["rich_text"])
    
    # Check for inline equation
    assert any(
        rt["type"] == "equation" for rt in all_text
    ), "Missing inline equation"
    
    # Verify text formatting in paragraphs
    rich_text = []
    for p in paragraphs:
        rich_text.extend(p["paragraph"]["rich_text"])
    
    # Use list comprehension instead of set conversion since dicts are unhashable
    annotations = [rt["annotations"] for rt in rich_text if rt["type"] == "text"]
    assert any(f["bold"] for f in annotations), "Missing bold text"
    assert any(f["italic"] for f in annotations), "Missing italic text"
    assert any(f["strikethrough"] for f in annotations), "Missing strikethrough text"
    assert any(f["code"] for f in annotations), "Missing inline code"
    
    # Verify links
    assert any(
        rt["type"] == "text" and rt["text"].get("link") is not None
        for p in paragraphs
        for rt in p["paragraph"]["rich_text"]
    ), "Missing link"
    
    print("[DEBUG] === Test create_page completed successfully ===")
    
    # Return detailed data for debugging
    return {
        "block_types": block_types,
        "block_count": len(results),
        "formatting_verification": {
            "has_bold": any(f["bold"] for f in annotations),
            "has_italic": any(f["italic"] for f in annotations),
            "has_strikethrough": any(f["strikethrough"] for f in annotations),
            "has_code": any(f["code"] for f in annotations),
            "has_link": any(
                rt["type"] == "text" and rt["text"].get("link") is not None
                for p in paragraphs
                for rt in p["paragraph"]["rich_text"]
            ),
            "has_equation": any(rt["type"] == "equation" for rt in all_text)
        }
    }

@pytest.mark.notion_integration
def test_append_to_page(notion_test):
    """
    Test appending content to an existing page.
    
    This test:
    1. Creates a Notion page
    2. Appends additional content to the page
    3. Verifies the content was properly appended
    """
    print("[DEBUG] === Test append_to_page starting ===")
    
    # ===== STEP 1: Create initial page =====
    page_id = notion_test.create_page(
        markdown_content=TEST_MARKDOWN,
        title=f"Append Test Page - {notion_test.test_name}"
    )
    assert page_id, "Failed to create page"
    
    # Get initial block count
    initial_blocks = notion_test.client.client.blocks.children.list(page_id)
    initial_count = len(initial_blocks["results"])
    
    # ===== STEP 2: Append content to the page =====
    # Create a temporary file with the markdown content for appending
    temp_file = notion_test.create_markdown_file(TEST_MARKDOWN)
    
    # Append content
    notion_test.client.append_to_page(page_id, temp_file)
    
    # ===== STEP 3: Verify content was appended =====
    # Get new block count
    final_blocks = notion_test.client.client.blocks.children.list(page_id)
    final_count = len(final_blocks["results"])
    
    # Verify content was appended
    assert final_count > initial_count, "Content not appended"
    
    print("[DEBUG] === Test append_to_page completed successfully ===")
    
    # Return detailed data for debugging
    return {
        "initial_block_count": initial_count,
        "final_block_count": final_count,
        "blocks_added": final_count - initial_count,
        "page_id": page_id
    }

