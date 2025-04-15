"""
Integration tests for text formatting conversions in pandoc-notion.

Tests proper conversion of Markdown text formatting to Notion rich text,
including bold, italic, strikethrough, inline code, and links.
"""
import pytest
from typing import Dict, Any, List, Optional

# Markdown content with various text formatting
TEST_FORMATTING_MARKDOWN = '''# Text Formatting Test

## Basic Formatting

This paragraph has **bold text**, *italic text*, and ***bold italic text***.

This paragraph has ~~strikethrough text~~ and `inline code`.

## Combined Formatting

This paragraph combines **bold with *nested italic* inside**.

This has *italic with **nested bold** and ~~nested strikethrough~~*.

## Links

This paragraph has [a simple link](https://example.com).

This paragraph has [**bold link**](https://example.com/bold).

This paragraph has [*italic link*](https://example.com/italic).

This paragraph has [***bold italic link***](https://example.com/bolditalic).

This paragraph has [~~strikethrough link~~](https://example.com/strikethrough).

## Formatting in Different Block Types

> This is a blockquote with **bold**, *italic*, and `code`.

* List item with **bold** and *italic*
* List item with [a link](https://example.com/list)

1. Numbered item with **bold** and *italic*
2. Numbered item with [a link](https://example.com/numbered)

```
Code block with no formatting (should be plain)
```
'''

@pytest.mark.notion_integration
def test_formatting_conversion(notion_test):
    """
    Test conversion of text formatting with proper annotations in Notion.
    
    This test:
    1. Creates a Notion page with various text formatting styles
    2. Retrieves the page content and extracts rich text blocks
    3. Verifies all expected formatting is properly rendered
    """
    print("[DEBUG] === Test formatting_conversion starting ===")
    
    # Helper function for text normalization
    def normalize_text(text: str) -> str:
        """Normalize text by removing extra whitespace and lowercasing."""
        if not text:
            return ""
        return " ".join(text.lower().split())
    
    # ===== STEP 1: Create a single test page =====
    page_id = notion_test.create_page(
        markdown_content=TEST_FORMATTING_MARKDOWN,
        title=f"Formatting Test Page - {notion_test.test_name}"
    )
    
    # Verify page exists
    page = notion_test.client.client.pages.retrieve(page_id)
    assert page["id"] == page_id, "Page creation failed"
    
    # ===== STEP 2: Retrieve blocks =====
    blocks = notion_test.client.client.blocks.children.list(page_id)
    results = blocks["results"]
    
    # Collect all rich_text elements for verification
    all_rich_texts = []
    
    # Extract rich_text from paragraphs
    paragraphs = [b for b in results if b["type"] == "paragraph"]
    for p in paragraphs:
        all_rich_texts.extend(p["paragraph"]["rich_text"])
        
    # Extract rich_text from quotes
    quotes = [b for b in results if b["type"] == "quote"]
    for q in quotes:
        all_rich_texts.extend(q["quote"]["rich_text"])
        
    # Extract rich_text from list items
    list_items = [b for b in results if b["type"] in ["bulleted_list_item", "numbered_list_item"]]
    for item in list_items:
        all_rich_texts.extend(item[item["type"]]["rich_text"])
    
    # Verify basic annotations
    def has_annotation_with_text(annotation_type, text_to_find):
        """Check if text with specific annotation exists."""
        # Corrected syntax: removed duplicate loop and fixed parentheses
        return any(
            rt["type"] == "text" and
            rt["annotations"][annotation_type] and 
            # Normalize both sides for comparison
            normalize_text(text_to_find) in normalize_text(rt.get("plain_text", ""))
            for rt in all_rich_texts
        )
    
    # Test bold text
    assert has_annotation_with_text("bold", "bold text"), "Missing bold text"
    
    # Test italic text
    assert has_annotation_with_text("italic", "italic text"), "Missing italic text"
    
    # Test strikethrough text
    assert has_annotation_with_text("strikethrough", "strikethrough text"), "Missing strikethrough text"
    
    # Test inline code
    assert has_annotation_with_text("code", "inline code"), "Missing inline code"
    
    # Test combined formatting (bold + italic)
    bold_italic_texts = [
        rt for rt in all_rich_texts 
        if rt["type"] == "text" and 
        rt["annotations"]["bold"] and
        rt["annotations"]["italic"]
    ]
    assert len(bold_italic_texts) > 0, "Missing bold+italic combination"
    # Normalize comparison
    assert any(normalize_text("bold italic text") in normalize_text(rt.get("plain_text", "")) for rt in bold_italic_texts), "Missing 'bold italic text'" # Corrected expected text

    # Test nested formatting
    assert any(
        rt["type"] == "text" and
        rt["annotations"]["bold"] and
        # Normalize comparison
        normalize_text("nested italic") in normalize_text(rt.get("plain_text", ""))
        for rt in all_rich_texts
    ), "Missing nested formatting (bold with nested italic)"
    
    # Test links
    links = [rt for rt in all_rich_texts if rt["type"] == "text" and rt["text"].get("link") is not None]
    assert len(links) > 0, "Missing links"
    
    # Verify link URLs and associated text (normalized)
    link_data = {
        normalize_text(link.get("plain_text", "")): link["text"]["link"]["url"] 
        for link in links
    }
    print(f"\nDEBUG: Normalized link data:\n{link_data}\n") # Debug print
    
    # Basic link
    assert link_data.get("a simple link") == "https://example.com/", f"Missing or incorrect URL for 'a simple link'. Found: {link_data}"
    
    # Check specific formatted link texts and URLs
    assert link_data.get("bold link") == "https://example.com/bold", f"Missing or incorrect URL for 'bold link'. Found: {link_data}"
    assert link_data.get("italic link") == "https://example.com/italic", f"Missing or incorrect URL for 'italic link'. Found: {link_data}"
    assert link_data.get("bold italic link") == "https://example.com/bolditalic", f"Missing or incorrect URL for 'bold italic link'. Found: {link_data}"
    assert link_data.get("strikethrough link") == "https://example.com/strikethrough", f"Missing or incorrect URL for 'strikethrough link'. Found: {link_data}"

    # Test formatted links (check annotations generally)
    formatted_links = [
        link for link in links 
        if (link["annotations"]["bold"] or 
            link["annotations"]["italic"] or 
            link["annotations"]["strikethrough"])
    ]
    assert len(formatted_links) > 0, "Missing formatted links"
    
    # Verify links within different block types
    # Find links in list items
    list_links = []
    for item in list_items:
        for rt in item[item["type"]]["rich_text"]:
            if rt["type"] == "text" and rt["text"].get("link") is not None:
                list_links.append(rt)
    
    assert len(list_links) > 0, "Missing links in list items"
    
    # Check if we have formatting in blockquotes
    quote_formatting = False
    for q in quotes:
        for rt in q["quote"]["rich_text"]:
            if rt["type"] == "text" and (
                rt["annotations"]["bold"] or 
                rt["annotations"]["italic"] or 
                rt["annotations"]["code"]
            ):
                quote_formatting = True
                break
    
    assert quote_formatting, "Missing formatting in blockquotes"
    
    print("[DEBUG] === Test formatting_conversion completed successfully ===")
    
    # Return detailed data for debugging
    return {
        "rich_text_elements": {
            "total_count": len(all_rich_texts),
            "bold_count": sum(1 for rt in all_rich_texts if rt["type"] == "text" and rt["annotations"]["bold"]),
            "italic_count": sum(1 for rt in all_rich_texts if rt["type"] == "text" and rt["annotations"]["italic"]),
            "strikethrough_count": sum(1 for rt in all_rich_texts if rt["type"] == "text" and rt["annotations"]["strikethrough"]),
            "code_count": sum(1 for rt in all_rich_texts if rt["type"] == "text" and rt["annotations"]["code"]),
            "link_count": len([rt for rt in all_rich_texts if rt["type"] == "text" and rt["text"].get("link") is not None]),
        },
        "block_count": len(results),
        "formatted_links": [
            {
                "text": rt.get("plain_text", ""),
                "url": rt["text"]["link"]["url"],
                "is_bold": rt["annotations"]["bold"],
                "is_italic": rt["annotations"]["italic"],
                "is_strikethrough": rt["annotations"]["strikethrough"]
            }
            for rt in all_rich_texts 
            if rt["type"] == "text" and rt["text"].get("link") is not None
        ]
    }

