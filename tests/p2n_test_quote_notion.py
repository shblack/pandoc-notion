"""
Integration tests for blockquote conversions in pandoc-notion.

Tests proper conversion of Markdown blockquotes to Notion quote blocks,
including nesting, formatting, and mixed content within quotes.
"""
import pytest
from typing import Dict, Any, List, Optional

# Markdown content with various blockquote structures
TEST_QUOTE_MARKDOWN = '''# Blockquote Test

## Basic Blockquotes

> This is a simple blockquote with plain text.

> This is a blockquote
> that spans multiple lines
> in the markdown source.

## Formatted Blockquotes

> This blockquote has **bold text**, *italic text*, and [a link](https://example.com).

> This blockquote has `inline code` and ~~strikethrough~~ text.

## Nested Blockquotes

> This is an outer blockquote
> > This is a nested blockquote
> > > This is a deeply nested blockquote

## Blockquotes with Mixed Content

> ### Heading inside blockquote
> 
> - List item 1 inside blockquote
> - List item 2 inside blockquote
>
> ```python
> # Code block inside blockquote
> def hello():
>     print("Hello from inside a blockquote!")
> ```

## Multi-paragraph Blockquotes

> First paragraph in the blockquote.
>
> Second paragraph in the blockquote.
>
> Third paragraph in the blockquote with **formatting**.
'''

@pytest.mark.notion_integration
def test_quote_conversion(notion_test):
    """
    Test conversion of blockquotes with proper formatting and nesting in Notion.
    
    This test:
    1. Creates a Notion page with various blockquote types and structures
    2. Retrieves the page content and extracts quote blocks
    3. Verifies proper conversion including formatting, nesting, and mixed content
    """
    print("[DEBUG] === Test quote_conversion starting ===")
    
    # Helper function for text normalization
    def normalize_text(text: str) -> str:
        """Normalize text by removing extra whitespace and lowercasing."""
        if not text:
            return ""
        return " ".join(text.lower().split())
    
    # ===== STEP 1: Create a single test page =====
    page_id = notion_test.create_page(
        markdown_content=TEST_QUOTE_MARKDOWN,
        title=f"Blockquote Test Page - {notion_test.test_name}"
    )
    
    # Verify page exists
    page = notion_test.client.client.pages.retrieve(page_id)
    assert page["id"] == page_id, "Page creation failed"
    
    # ===== STEP 2: Retrieve blocks =====
    blocks = notion_test.client.client.blocks.children.list(page_id)
    results = blocks["results"]
    
    # Get all quote blocks
    quote_blocks = [b for b in results if b["type"] == "quote"]
    
    # Verify we have quote blocks
    assert len(quote_blocks) > 0, "Missing quote blocks"
    
    # Helper function to find a quote containing specific text
    def find_quote_with_text(text_to_find):
        """Find a quote block containing the given normalized text."""
        norm_text_to_find = normalize_text(text_to_find) # Normalize search term
        for block in quote_blocks:
            rich_text = block["quote"].get("rich_text", [])
            # Normalize collected content
            norm_content = normalize_text("".join(rt.get("plain_text", "") for rt in rich_text))
            if norm_text_to_find in norm_content:
                return block
        return None
    
    # ===== STEP 3: Test basic blockquote =====
    basic_quote = find_quote_with_text("simple blockquote with plain text")
    assert basic_quote is not None, "Missing basic blockquote"
    
    # ===== STEP 4: Test multi-line blockquote =====
    multiline_quote = find_quote_with_text("spans multiple lines")
    assert multiline_quote is not None, "Missing multi-line blockquote"
    
    # ===== STEP 5: Test formatted blockquote (bold, italic, and link) =====
    formatted_quote = find_quote_with_text("bold text")
    assert formatted_quote is not None, "Missing formatted blockquote"
    
    # Verify rich text formatting in the formatted blockquote
    formatted_rich_text = formatted_quote["quote"]["rich_text"]
    
    # Check for bold text formatting
    has_bold = False
    for rt in formatted_rich_text:
        if rt["type"] == "text" and rt["annotations"]["bold"]:
            has_bold = True
            break
    assert has_bold, "Missing bold formatting in blockquote"
    
    # Check for italic text formatting
    has_italic = False
    for rt in formatted_rich_text:
        if rt["type"] == "text" and rt["annotations"]["italic"]:
            has_italic = True
            break
    assert has_italic, "Missing italic formatting in blockquote"
    
    # Check for link in blockquote
    has_link = False
    for rt in formatted_rich_text:
        if rt["type"] == "text" and rt["text"].get("link") is not None:
            has_link = True
            break
    assert has_link, "Missing link in blockquote"
    
    # ===== STEP 6: Test blockquote with code and strikethrough =====
    code_quote = find_quote_with_text("inline code")
    assert code_quote is not None, "Missing blockquote with code"
    
    code_rich_text = code_quote["quote"]["rich_text"]
    
    # Check for inline code
    has_code = False
    for rt in code_rich_text:
        if rt["type"] == "text" and rt["annotations"]["code"]:
            has_code = True
            break
    assert has_code, "Missing inline code in blockquote"
    
    # Check for strikethrough
    has_strikethrough = False
    for rt in code_rich_text:
        if rt["type"] == "text" and rt["annotations"]["strikethrough"]:
            has_strikethrough = True
            break
    assert has_strikethrough, "Missing strikethrough in blockquote"
    
    # ===== STEP 7: Test nested blockquotes =====
    nested_quote = find_quote_with_text("outer blockquote")
    assert nested_quote is not None, "Missing nested blockquote"
    
    # Verify nested blockquote content (Notion puts nested markdown quotes in the text)
    nested_rich_text = nested_quote["quote"].get("rich_text", [])
    nested_content = "".join(rt.get("plain_text", "") for rt in nested_rich_text)
    expected_nested_text = "This is an outer blockquote\n> This is a nested blockquote\n> > This is a deeply nested blockquote"
    # Use normalized comparison to handle potential whitespace differences
    assert normalize_text(expected_nested_text) == normalize_text(nested_content), "Nested blockquote text content mismatch"
    
    # ===== STEP 8: Test blockquote with mixed content =====
    mixed_quote = find_quote_with_text("Heading inside blockquote")
    assert mixed_quote is not None, "Missing blockquote with mixed content"
    
    # Check if it has children
    has_mixed_children = mixed_quote.get("has_children", False)
    assert has_mixed_children, "Blockquote with mixed content should have children"
    
    # Get children of mixed content blockquote
    if has_mixed_children:
        mixed_children = notion_test.client.client.blocks.children.list(mixed_quote["id"])
        mixed_results = mixed_children["results"]
        
        # Check for list items in the blockquote
        list_items = [b for b in mixed_results if b["type"] in ["bulleted_list_item", "numbered_list_item"]]
        assert len(list_items) > 0, "Missing list items in blockquote"
        
        # Check for code block in the blockquote
        code_blocks = [b for b in mixed_results if b["type"] == "code"]
        assert len(code_blocks) > 0, "Missing code block in blockquote"
        
        # Verify code block content (normalized)
        if code_blocks:
            code_rich_text = code_blocks[0]["code"].get("rich_text", [])
            code_content = "".join(rt.get("plain_text", "") for rt in code_rich_text)
            # Normalize comparison - safe here as we check for plain string
            assert normalize_text("Hello from inside a blockquote") in normalize_text(code_content), "Missing content in code block inside blockquote"
    
    # ===== STEP 9: Test multi-paragraph blockquote =====
    multi_para_quote = find_quote_with_text("First paragraph in the blockquote")
    assert multi_para_quote is not None, "Missing multi-paragraph blockquote"
    
    # Check if it has children (additional paragraphs)
    has_para_children = multi_para_quote.get("has_children", False)
    assert has_para_children, "Multi-paragraph blockquote should have children"
    
    # Get children of multi-paragraph blockquote
    if has_para_children:
        para_children = notion_test.client.client.blocks.children.list(multi_para_quote["id"])
        para_results = para_children["results"]
        
        # Check for paragraphs in the blockquote
        paragraphs = [b for b in para_results if b["type"] == "paragraph"]
        assert len(paragraphs) >= 2, "Missing additional paragraphs in blockquote"
        
        # Verify paragraph content
        para_contents = []
        for para in paragraphs:
            # Normalize collected content
            content = normalize_text("".join(rt.get("plain_text", "") for rt in para["paragraph"].get("rich_text", [])))
            para_contents.append(content)
        
        # Normalize comparisons
        assert any(normalize_text("Second paragraph") in content for content in para_contents), "Missing second paragraph in blockquote"
        assert any(normalize_text("Third paragraph") in content for content in para_contents), "Missing third paragraph in blockquote"
        
        # Check for formatting in the third paragraph
        for para in paragraphs:
            # Normalize content for check
            content = normalize_text("".join(rt.get("plain_text", "") for rt in para["paragraph"].get("rich_text", [])))
            if normalize_text("Third paragraph") in content:
                # Check for bold formatting
                has_bold_in_para = any(rt["annotations"]["bold"] for rt in para["paragraph"].get("rich_text", []) if rt["type"] == "text")
                assert has_bold_in_para, "Missing bold formatting in third paragraph of blockquote"
    
    print("[DEBUG] === Test quote_conversion completed successfully ===")
    
    # Return detailed data for debugging
    return {
        "quote_blocks": {
            "total_count": len(quote_blocks),
            "with_children_count": sum(1 for b in quote_blocks if b.get("has_children", False))
        },
        "formatting_verification": {
            "has_bold": has_bold,
            "has_italic": has_italic,
            "has_link": has_link,
            "has_code": has_code,
            "has_strikethrough": has_strikethrough
        },
        "nested_quote_verification": {
            "nested_content_length": len(nested_content) if nested_quote else 0,
            "nesting_levels": nested_content.count(">") if nested_quote else 0
        },
        "mixed_content": {
            "has_mixed_quote": mixed_quote is not None,
            "list_items_count": len(list_items) if has_mixed_children else 0,
            "code_blocks_count": len(code_blocks) if has_mixed_children else 0
        },
        "multi_paragraph": {
            "has_multi_para_quote": multi_para_quote is not None,
            "paragraph_count": len(paragraphs) if has_para_children else 0
        },
        "block_count": len(results)
    }

