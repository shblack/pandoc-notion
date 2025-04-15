"""
Integration tests for heading conversions in pandoc-notion.

Tests proper conversion of Markdown headings to Notion heading blocks,
including fallback behavior for h4-h6 headings.
"""
import pytest
from typing import Dict, Any, List, Optional

# Markdown content with headings of all levels (h1-h6)
TEST_HEADING_MARKDOWN = '''# Heading 1

Content under heading 1.

## Heading 2

Content under heading 2.

### Heading 3

Content under heading 3.

#### Heading 4 (should be converted to h3 in Notion)

Content under heading 4.

##### Heading 5 (should be converted to h3 in Notion)

Content under heading 5.

###### Heading 6 (should be converted to h3 in Notion)

Content under heading 6.
'''

@pytest.mark.notion_integration
def test_heading_conversion(notion_test):
    """
    Test conversion of headings at all levels with proper fallback in Notion.
    
    This test:
    1. Creates a Notion page with headings of all levels (h1-h6)
    2. Retrieves the page content and extracts heading blocks
    3. Verifies proper conversion including fallback of h4-h6 to h3
    """
    print("[DEBUG] === Test heading_conversion starting ===")
    
    # Helper function for text normalization
    def normalize_text(text: str) -> str:
        """Normalize text by removing extra whitespace and lowercasing."""
        if not text:
            return ""
        return " ".join(text.lower().split())
    
    # ===== STEP 1: Create a single test page =====
    page_id = notion_test.create_page(
        markdown_content=TEST_HEADING_MARKDOWN,
        title=f"Heading Test Page - {notion_test.test_name}"
    )
    
    # Verify page exists
    page = notion_test.client.client.pages.retrieve(page_id)
    assert page["id"] == page_id, "Page creation failed"
    
    # ===== STEP 2: Retrieve blocks =====
    blocks = notion_test.client.client.blocks.children.list(page_id)
    results = blocks["results"]
    
    # Get all heading blocks
    heading_blocks = [b for b in results if b["type"].startswith("heading_")]
    
    # Verify we have at least 6 headings (one for each level in the markdown)
    assert len(heading_blocks) >= 6, f"Expected 6 headings, found {len(heading_blocks)}"
    
    # Check that heading_1, heading_2, and heading_3 types exist
    heading_types = set(b["type"] for b in heading_blocks)
    assert "heading_1" in heading_types, "Missing heading_1"
    assert "heading_2" in heading_types, "Missing heading_2"
    assert "heading_3" in heading_types, "Missing heading_3"
    
    # Heading 4-6 should be converted to heading_3
    assert all(b["type"] != "heading_4" for b in heading_blocks), "heading_4 found, expected fallback to heading_3"
    assert all(b["type"] != "heading_5" for b in heading_blocks), "heading_5 found, expected fallback to heading_3"
    assert all(b["type"] != "heading_6" for b in heading_blocks), "heading_6 found, expected fallback to heading_3"
    
    # Verify the content of headings
    heading_contents = {
        "heading_1": [],
        "heading_2": [],
        "heading_3": []
    }
    
    for block in heading_blocks:
        heading_type = block["type"]
        # Normalize collected text content
        text_content = normalize_text("".join(rt.get("plain_text", "") for rt in block[heading_type].get("rich_text", [])))
        heading_contents[heading_type].append(text_content)
    
    # Verify specific heading content (using normalized comparison)
    assert normalize_text("Heading 1") in heading_contents["heading_1"], "Heading 1 content not found"
    assert normalize_text("Heading 2") in heading_contents["heading_2"], "Heading 2 content not found"
    
    # For heading_3, we should have all of h3, h4, h5, and h6 content (normalized)
    h3_contents = heading_contents["heading_3"]
    assert any(normalize_text("Heading 3") in content for content in h3_contents), "Heading 3 content not found"
    assert any(normalize_text("Heading 4") in content for content in h3_contents), "Heading 4 content not found (should be h3)"
    assert any(normalize_text("Heading 5") in content for content in h3_contents), "Heading 5 content not found (should be h3)"
    assert any(normalize_text("Heading 6") in content for content in h3_contents), "Heading 6 content not found (should be h3)"
    
    print("[DEBUG] === Test heading_conversion completed successfully ===")
    
    # Return detailed data for debugging
    return {
        "heading_contents": heading_contents,
        "heading_types": list(heading_types),
        "heading_count": len(heading_blocks),
        "block_count": len(results),
        "h3_fallback_verification": {
            "h4_converted": any(normalize_text("Heading 4") in content for content in heading_contents["heading_3"]),
            "h5_converted": any(normalize_text("Heading 5") in content for content in heading_contents["heading_3"]),
            "h6_converted": any(normalize_text("Heading 6") in content for content in heading_contents["heading_3"])
        }
    }

