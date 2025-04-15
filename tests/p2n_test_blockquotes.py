"""
Tests for blockquote block conversion using QuoteManager.

These tests focus on the conversion of panflute BlockQuote elements to Notion quote blocks,
including simple blockquotes, nested blockquotes, and blockquotes with other elements.
All tests validate against the Notion API expected structure:
{
  "object": "block",
  "type": "quote",
  "quote": {
    "rich_text": [
      {
        "type": "text",
        "text": { "content": "Blockquote content" },
        "annotations": {
          "bold": false,
          "italic": false,
          "strikethrough": false,
          "underline": false,
          "code": false,
          "color": "default"
        }
      }
    ],
    "color": "default"
  }
}
"""

import pytest
import panflute as pf
from conftest import debug_p2n

from pandoc_notion.models.quote import Quote
from pandoc_notion.models.paragraph import Paragraph
from pandoc_notion.managers.quote_manager import QuoteManager
from pandoc_notion.managers.text_manager import TextManager
from pandoc_notion.registry import ManagerRegistry


@pytest.fixture(autouse=True)
def setup_registry():
    """
    Set up registry with default managers for all tests.
    
    This fixture runs automatically before each test to ensure
    that the registry is properly initialized.
    """
    from pandoc_notion.managers.registry_mixin import set_registry
    
    registry = ManagerRegistry()
    set_registry(registry)  # Connect the registry to our managers
    return registry
def create_blockquote(text_contents):
    """Create a panflute BlockQuote element with the given text contents.
    
    Args:
        text_contents: List of strings, each representing a paragraph within the blockquote
        
    Returns:
        A panflute BlockQuote element containing paragraphs
    """
    paragraphs = []
    for text in text_contents:
        paragraphs.append(pf.Para(pf.Str(text)))
    
    return pf.BlockQuote(*paragraphs)


def create_formatted_blockquote(text_parts_list):
    """Create a blockquote with formatted text content.
    
    Args:
        text_parts_list: List of lists of tuples (text, format) where format can be 
                         'bold', 'italic', 'code', or None.
                         Each inner list represents a paragraph.
    """
    paragraphs = []
    
    for text_parts in text_parts_list:
        elements = []
        for i, (text, fmt) in enumerate(text_parts):
            if fmt == 'bold':
                elements.append(pf.Strong(pf.Str(text)))
            elif fmt == 'italic':
                elements.append(pf.Emph(pf.Str(text)))
            elif fmt == 'code':
                elements.append(pf.Code(text))
            else:
                elements.append(pf.Str(text))
                
            # Add space between elements (except after the last one)
            if i < len(text_parts) - 1:
                elements.append(pf.Space())
                
        paragraphs.append(pf.Para(*elements))
    
    return pf.BlockQuote(*paragraphs)


@debug_p2n(input_is_ast=True)
def test_basic_blockquote(request):
    """Test that a simple blockquote converts correctly using QuoteManager."""
    # Create a panflute BlockQuote element
    text_contents = [
        "This is a basic blockquote. It spans multiple lines in markdown."
    ]
    blockquote = create_blockquote(text_contents)
    
    # Store input for debugging
    debug_p2n.current.input = blockquote
    
    # Convert to Notion quote using QuoteManager
    quote_blocks = QuoteManager.convert(blockquote)
    assert len(quote_blocks) == 1
    
    # Get the quote model
    quote_block = quote_blocks[0]
    assert isinstance(quote_block, Quote)
    
    # Convert to dictionary using to_dict()
    block = quote_block.to_dict()
    
    # Store output for debugging
    debug_p2n.current.output = block
    
    # Basic structure checks
    assert block["object"] == "block"
    assert block["type"] == "quote"
    assert "quote" in block
    assert "rich_text" in block["quote"]
    assert "color" in block["quote"]
    assert block["quote"]["color"] == "default"
    
    # Validate rich text content
    rich_text = block["quote"]["rich_text"]
    assert len(rich_text) >= 1
    
    # Check combined text content
    combined_text = "".join(segment["text"]["content"] for segment in rich_text)
    assert "This is a basic blockquote." in combined_text
    assert "It spans multiple lines in markdown." in combined_text
    
    # Validate annotations
    for segment in rich_text:
        assert "annotations" in segment
        assert "bold" in segment["annotations"]
        assert "italic" in segment["annotations"]
        assert "strikethrough" in segment["annotations"]
        assert "underline" in segment["annotations"]
        assert "code" in segment["annotations"]
        assert "color" in segment["annotations"]


def create_nested_blockquote():
    """Create a nested blockquote structure using panflute elements."""
    # Create inner blockquote
    inner_paragraphs = [
        pf.Para(pf.Str("Nested blockquote")),
        pf.Para(pf.Str("Still in nested blockquote"))
    ]
    inner_blockquote = pf.BlockQuote(*inner_paragraphs)
    
    # Create outer blockquote containing the inner one
    outer_paragraphs = [
        pf.Para(pf.Str("Outer blockquote")),
        inner_blockquote,
        pf.Para(pf.Str("Back to outer blockquote"))
    ]
    outer_blockquote = pf.BlockQuote(*outer_paragraphs)
    
    return outer_blockquote


@debug_p2n(input_is_ast=True)
def test_nested_blockquotes(request):
    """Test that nested blockquotes convert correctly using QuoteManager."""
    # Create a nested panflute BlockQuote structure
    blockquote = create_nested_blockquote()
    
    # Store input for debugging
    debug_p2n.current.input = blockquote
    
    # Convert to Notion quote using QuoteManager
    quote_blocks = QuoteManager.convert(blockquote)
    
    
    # Convert to dictionaries for testing
    blocks = [block.to_dict() for block in quote_blocks]
    
    # Store output for debugging
    debug_p2n.current.output = blocks
    # Notion API might handle nesting in different ways:
    # 1. Using 'children' property for nested quotes
    # 2. Using separate blocks with indentation
    # We'll check for both possibilities
    
    # Check that we have at least one blockquote block
    assert len(blocks) > 0
    
    # Get the first block for testing
    first_block = blocks[0]
    
    # Basic structure checks
    assert first_block["object"] == "block"
    assert first_block["type"] == "quote"
    assert "quote" in first_block
    assert "rich_text" in first_block["quote"]
    
    # Check for nesting through the children property
    has_children = "children" in first_block["quote"]
    
    if has_children:
        # Test the nested structure if children are used
        children = first_block["quote"]["children"]
        assert len(children) > 0
        
        # Check that the child is also a blockquote
        child_block = children[0]
        assert child_block["type"] == "quote"
        assert "quote" in child_block
        assert "rich_text" in child_block["quote"]
        
        # Verify content of outer and inner blockquotes
        outer_text = "".join(segment["text"]["content"] for segment in first_block["quote"]["rich_text"])
        assert "Outer blockquote" in outer_text
        
        nested_text = "".join(segment["text"]["content"] for segment in child_block["quote"]["rich_text"])
        assert "Nested blockquote" in nested_text
    else:
        # If separate blocks are used, we should have multiple blocks
        assert len(blocks) >= 2
        
        # Check each block for the expected content
        first_text = "".join(segment["text"]["content"] for segment in first_block["quote"]["rich_text"])
        assert "Outer blockquote" in first_text or "Nested blockquote" in first_text
        
        if len(blocks) >= 2:
            second_block = blocks[1]
            assert second_block["type"] == "quote"
            second_text = "".join(segment["text"]["content"] for segment in second_block["quote"]["rich_text"])
            assert ("Nested blockquote" in second_text) or ("Outer blockquote" in second_text and "Nested blockquote" not in first_text)
    

@debug_p2n(input_is_ast=True)
def test_blockquote_with_formatting(request):
    """Test that blockquotes with formatting convert correctly using QuoteManager."""
    # Create a panflute BlockQuote with formatted text
    text_parts_list = [
        [
            ("This blockquote has ", None),
            ("bold", "bold"),
            (" and ", None),
            ("italic", "italic"),
            (" formatting.", None)
        ],
        [
            ("It also has ", None),
            ("code spans", "code"),
            (" within it.", None)
        ]
    ]
    blockquote = create_formatted_blockquote(text_parts_list)
    
    # Store input for debugging
    debug_p2n.current.input = blockquote
    
    # Convert to Notion quote using QuoteManager
    quote_blocks = QuoteManager.convert(blockquote)
    assert len(quote_blocks) == 1
    
    # Get the quote model and convert to dictionary
    quote_block = quote_blocks[0]
    assert isinstance(quote_block, Quote)
    
    
    # Convert to dictionary using to_dict()
    block = quote_block.to_dict()
    
    # Store output for debugging
    debug_p2n.current.output = block
    # Basic structure checks
    assert block["object"] == "block"
    assert block["type"] == "quote"
    assert "quote" in block
    assert "rich_text" in block["quote"]
    
    # Validate rich text content - there should be multiple segments for the formatting
    rich_text = block["quote"]["rich_text"]
    assert len(rich_text) > 1
    
    # Find segments with formatting
    bold_segment = next((segment for segment in rich_text 
                       if segment["text"]["content"].strip() == "bold" 
                       and segment["annotations"]["bold"] is True), None)
    
    italic_segment = next((segment for segment in rich_text 
                         if segment["text"]["content"].strip() == "italic"
                         and segment["annotations"]["italic"] is True), None)

    # According to Notion structure, the second paragraph becomes a child block.
    # Code spans should be found within that child paragraph block.
    assert "children" in block["quote"], "Blockquote should have children for the second paragraph"
    children = block["quote"]["children"]
    assert len(children) > 0, "Expected at least one child block"

    # Find the child paragraph block
    child_para = next((child for child in children if child["type"] == "paragraph"), None)
    assert child_para is not None, "Child paragraph block not found"
    assert "paragraph" in child_para, "Child block should contain paragraph data"
    assert "rich_text" in child_para["paragraph"], "Child paragraph should have rich_text"
    
    child_rich_text = child_para["paragraph"]["rich_text"]

    # Find code segment within the child paragraph's rich text
    code_segment = next((segment for segment in child_rich_text
                       if segment["text"]["content"].strip() == "code spans"
                       and segment["annotations"]["code"] is True), None)

    # Verify that we found the formatted segments
    assert bold_segment is not None, "Bold formatting not found in blockquote's main rich_text"
    assert italic_segment is not None, "Italic formatting not found in blockquote's main rich_text"
    assert code_segment is not None, "Code formatting not found in the child paragraph block"


def create_complex_blockquote():
    """Create a blockquote with various element types using panflute."""
    # Create a heading element
    heading = pf.Header(pf.Str("Heading inside blockquote"), level=3)
    
    # Create a bullet list with items
    list_items = [
        pf.ListItem(pf.Plain(pf.Str("List item 1"))),
        pf.ListItem(pf.Plain(pf.Str("List item 2")))
    ]
    bullet_list = pf.BulletList(*list_items)
    
    # Create a code block
    code_block = pf.CodeBlock("def example():\n    return \"Code block inside blockquote\"", 
                             classes=["python"])
    
    # Combine into a blockquote
    blockquote = pf.BlockQuote(heading, bullet_list, code_block)
    
    return blockquote


@debug_p2n(input_is_ast=True)
def test_blockquote_with_other_elements(request):
    """Test that blockquotes with other elements convert correctly using QuoteManager."""
    # Create a complex blockquote with multiple element types
    blockquote = create_complex_blockquote()
    
    # Store input for debugging
    debug_p2n.current.input = blockquote
    
    # Convert to Notion quote using QuoteManager
    quote_blocks = QuoteManager.convert(blockquote)
    
    
    # Convert to dictionaries for testing
    blocks = [block.to_dict() for block in quote_blocks]
    
    # Store output for debugging
    debug_p2n.current.output = blocks
    # Notion API might handle complex blockquotes in different ways:
    # 1. Using 'children' property for contained elements
    # 2. Using separate blocks with a common parent
    # 3. Converting everything to rich text within a single quote block
    
    # Assert that converting the complex blockquote results in a single quote block
    # with the first element as rich_text and subsequent elements as children.
    assert len(blocks) == 1, f"Expected 1 main quote block, got {len(blocks)}"
    block = blocks[0]
    assert block["type"] == "quote", f"Expected block type 'quote', got {block['type']}"
    assert "quote" in block, "Block data missing 'quote' key"
    assert block["has_children"] is True, "Quote block should have children"
    assert "children" in block["quote"], "Quote data missing 'children' key"

    # Verify the main quote's rich text (from the heading)
    assert "rich_text" in block["quote"], "Quote data missing 'rich_text' key"
    assert block["quote"]["rich_text"][0]["text"]["content"] == "Heading inside blockquote"

    # Get and verify the children
    children = block["quote"]["children"]
    assert len(children) == 3, f"Expected 3 children (2 list items, 1 code), got {len(children)}"

    # Find and verify the list item blocks within children
    list_item_blocks = [child for child in children if child["type"] == "bulleted_list_item"]
    assert len(list_item_blocks) == 2, f"Expected 2 bulleted_list_item blocks, found {len(list_item_blocks)}"
    # Sort list items by content to ensure consistent checking order
    list_item_blocks.sort(key=lambda b: b["bulleted_list_item"]["rich_text"][0]["text"]["content"])
    assert list_item_blocks[0]["bulleted_list_item"]["rich_text"][0]["text"]["content"] == "List item 1"
    assert list_item_blocks[1]["bulleted_list_item"]["rich_text"][0]["text"]["content"] == "List item 2"

    # Find and verify the code block within children
    code_block = next((child for child in children if child["type"] == "code"), None)
    assert code_block is not None, "Code block not found"
    assert code_block["code"]["language"] == "python"
    assert "def example():" in code_block["code"]["rich_text"][0]["text"]["content"]

