"""
Integration tests for list conversions in pandoc-notion.

Tests proper conversion of Markdown lists to Notion list blocks,
including nesting, mixed list types, and formatting within list items.
"""
import pytest
from typing import Dict, Any, List, Optional

# Markdown content with various list structures
TEST_LIST_MARKDOWN = '''# List Test

## Simple Lists

### Bulleted List
* First item
* Second item
* Third item

### Numbered List
1. First item
2. Second item
3. Third item

## Nested Lists

### Nested Bulleted List
* Parent item 1
  * Child item 1.1
  * Child item 1.2
    * Grandchild item 1.2.1
* Parent item 2
  * Child item 2.1

### Nested Numbered List
1. First level item 1
   1. Second level item 1.1
   2. Second level item 1.2
      1. Third level item 1.2.1
2. First level item 2
   1. Second level item 2.1

## Mixed List Types

### Bulleted List with Numbered Sublist
* Main bullet 1
  1. Numbered sub-item 1.1
  2. Numbered sub-item 1.2
* Main bullet 2
  1. Numbered sub-item 2.1

### Numbered List with Bulleted Sublist
1. Main numbered 1
   * Bulleted sub-item 1.1
   * Bulleted sub-item 1.2
2. Main numbered 2
   * Bulleted sub-item 2.1

## Formatted List Items

### List with Formatting
* Item with **bold text**
* Item with *italic text*
* Item with `inline code`
* Item with [a link](https://example.com)

### Deep Nesting with Formatting
* Level 1
  * Level 2 with **bold**
    * Level 3 with *italic*
      * Level 4 with ***bold italic***
'''

@pytest.mark.notion_integration
def test_list_conversion(notion_test):
    """
    Test conversion of various list structures with proper nesting and formatting in Notion.
    
    This test:
    1. Creates a Notion page with various list types and structures
    2. Retrieves the page content and extracts list blocks
    3. Verifies proper conversion of lists including nesting, formatting, and mixed types
    """
    print("[DEBUG] === Test list_conversion starting ===")
    
    # ===== STEP 1: Create a single test page =====
    page_id = notion_test.create_page(
        markdown_content=TEST_LIST_MARKDOWN,
        title=f"List Test Page - {notion_test.test_name}"
    )
    
    # Verify page exists
    page = notion_test.client.client.pages.retrieve(page_id)
    assert page["id"] == page_id, "Page creation failed"
    
    # ===== STEP 2: Retrieve blocks =====
    blocks = notion_test.client.client.blocks.children.list(page_id)
    results = blocks["results"]
    
    # Get all list items
    bulleted_items = [b for b in results if b["type"] == "bulleted_list_item"]
    numbered_items = [b for b in results if b["type"] == "numbered_list_item"]
    
    # Verify we have both types of lists
    assert len(bulleted_items) > 0, "Missing bulleted list items"
    assert len(numbered_items) > 0, "Missing numbered list items"
    
    # Verify nested lists by checking for children
    nested_items = [b for b in bulleted_items + numbered_items if b.get("has_children", False)]
    assert len(nested_items) > 0, "Missing nested list items"
    
    # Verify formatting in list items
    def has_formatting_in_list_items(items, annotation_type):
        """Check if list items contain text with specific formatting."""
        for item in items:
            rich_text = item[item["type"]]["rich_text"]
            for rt in rich_text:
                if rt["type"] == "text" and rt["annotations"].get(annotation_type, False):
                    return True
        return False
    
    # Check for formatted text in list items
    assert has_formatting_in_list_items(bulleted_items + numbered_items, "bold"), "Missing bold text in list items"
    assert has_formatting_in_list_items(bulleted_items + numbered_items, "italic"), "Missing italic text in list items"
    assert has_formatting_in_list_items(bulleted_items + numbered_items, "code"), "Missing code in list items"
    
    # Check for links in list items
    link_found = False
    for item in bulleted_items + numbered_items:
        rich_text = item[item["type"]]["rich_text"]
        for rt in rich_text:
            if rt["type"] == "text" and rt["text"].get("link") is not None:
                link_found = True
                break
        if link_found:
            break
    assert link_found, "Missing links in list items"
    
    # Test deep nesting by checking recursive children
    def find_deep_nesting(item, current_depth=1, target_depth=3):
        """Recursively check for nested list items up to target depth."""
        if current_depth >= target_depth:
            return True
            
        if not item.get("has_children", False):
            return False
            
        # Get children of this item
        item_id = item["id"]
        children = notion_test.client.client.blocks.children.list(item_id)
        child_results = children["results"]
        
        # Check if any children have their own children
        for child in child_results:
            if child["type"] in ["bulleted_list_item", "numbered_list_item"]:
                if find_deep_nesting(child, current_depth + 1, target_depth):
                    return True
        
        return False
    
    # Check for deep nesting (at least 3 levels deep)
    deep_nesting_found = False
    for item in nested_items:
        if find_deep_nesting(item):
            deep_nesting_found = True
            break
            
    assert deep_nesting_found, "Missing deep nesting (at least 3 levels)"
    
    # Test mixed list types (bullet containing numbered or vice versa)
    def has_mixed_list_types():
        """Check if there are mixed list types (bullet containing numbered or vice versa)."""
        for item in nested_items:
            item_id = item["id"]
            item_type = item["type"]
            
            # Get children
            children = notion_test.client.client.blocks.children.list(item_id)
            child_results = children["results"]
            
            # Check if any children are of a different list type
            for child in child_results:
                child_type = child["type"]
                if child_type in ["bulleted_list_item", "numbered_list_item"] and child_type != item_type:
                    return True
        
        return False
        
    assert has_mixed_list_types(), "Missing mixed list types (bullet containing numbered or vice versa)"
    
    print("[DEBUG] === Test list_conversion completed successfully ===")
    
    # Return detailed data for debugging
    return {
        "list_items": {
            "bulleted_count": len(bulleted_items),
            "numbered_count": len(numbered_items),
            "nested_count": len(nested_items)
        },
        "formatting_verification": {
            "has_bold": has_formatting_in_list_items(bulleted_items + numbered_items, "bold"),
            "has_italic": has_formatting_in_list_items(bulleted_items + numbered_items, "italic"),
            "has_code": has_formatting_in_list_items(bulleted_items + numbered_items, "code"),
            "has_links": link_found
        },
        "nesting_verification": {
            "has_deep_nesting": deep_nesting_found,
            "has_mixed_types": has_mixed_list_types()
        },
        "block_count": len(results)
    }

