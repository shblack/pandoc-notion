"""
Tests for paragraph block conversion using ParagraphManager.

These tests focus on the conversion of panflute paragraph elements to Notion paragraph blocks,
including basic paragraphs, formatted paragraphs, and multiple paragraphs.

All tests validate against the Notion API expected structure:
{
  "object": "block",
  "type": "paragraph",
  "paragraph": {
    "rich_text": [
      {
        "type": "text",
        "text": { "content": "Example content" },
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
from conftest import store_example

from pandoc_notion.models.paragraph import Paragraph
from pandoc_notion.managers.paragraph_manager import ParagraphManager
from pandoc_notion.managers.text_manager import TextManager


def create_para_element(text):
    """Create a panflute paragraph element with the given text."""
    return pf.Para(pf.Str(text))

def create_formatted_para(text_parts):
    """Create a paragraph with formatted text.
    
    Args:
        text_parts: List of tuples (text, format) where format can be 'bold', 'italic', 'code', or None
    """
    elements = []
    for text, fmt in text_parts:
        if fmt == 'bold':
            elements.append(pf.Strong(pf.Str(text)))
        elif fmt == 'italic':
            elements.append(pf.Emph(pf.Str(text)))
        elif fmt == 'code':
            elements.append(pf.Code(text))
        else:
            elements.append(pf.Str(text))
        
        # Add space between elements (except after the last one)
        if text_parts.index((text, fmt)) < len(text_parts) - 1:
            elements.append(pf.Space())
            
    return pf.Para(*elements)

def test_basic_paragraph_conversion(request):
    """Test that a simple paragraph converts to a Notion paragraph block."""
    # Create a panflute paragraph element
    text = "This is a basic paragraph."
    para = create_para_element(text)
    
    # Convert to Notion paragraph using ParagraphManager
    paragraph_blocks = ParagraphManager.convert(para)
    assert len(paragraph_blocks) == 1
    
    # Get the paragraph model
    paragraph_block = paragraph_blocks[0]
    assert isinstance(paragraph_block, Paragraph)
    
    # Convert to dictionary using to_dict()
    block = paragraph_block.to_dict()
    
    # Basic structure checks
    assert block["object"] == "block"
    assert block["type"] == "paragraph"
    assert "paragraph" in block
    assert "rich_text" in block["paragraph"]
    assert "color" in block["paragraph"]
    assert block["paragraph"]["color"] == "default"
    
    # Validate rich text content
    rich_text = block["paragraph"]["rich_text"]
    assert len(rich_text) == 1
    
    # Check text content
    assert "text" in rich_text[0]
    assert "content" in rich_text[0]["text"]
    assert rich_text[0]["text"]["content"] == "This is a basic paragraph."
    
    # Validate annotations
    assert "annotations" in rich_text[0]
    assert rich_text[0]["annotations"]["bold"] is False
    assert rich_text[0]["annotations"]["italic"] is False
    assert "strikethrough" in rich_text[0]["annotations"]
    assert "underline" in rich_text[0]["annotations"]
    assert "underline" in rich_text[0]["annotations"]
    assert "code" in rich_text[0]["annotations"]
    assert "color" in rich_text[0]["annotations"]
    
    # Store a representative example of a basic paragraph
    store_example(request, {
        'markdown': 'This is a basic paragraph.',
        'notion_api': block
    })

def test_paragraph_with_formatting(request):
    """Test that paragraphs with bold and italic formatting convert correctly."""
    # Create a panflute paragraph with formatted text
    text_parts = [
        ("This paragraph has", None),
        ("bold", "bold"),
        ("and", None),
        ("italic", "italic"),
        ("formatting.", None)
    ]
    para = create_formatted_para(text_parts)
    
    # Convert to Notion paragraph using ParagraphManager
    paragraph_blocks = ParagraphManager.convert(para)
    assert len(paragraph_blocks) == 1
    
    # Get the paragraph model
    paragraph_block = paragraph_blocks[0]
    assert isinstance(paragraph_block, Paragraph)
    
    # Convert to dictionary using to_dict()
    block = paragraph_block.to_dict()
    
    # Basic structure checks
    assert block["object"] == "block"
    assert block["type"] == "paragraph"
    assert "paragraph" in block
    assert "rich_text" in block["paragraph"]
    assert "color" in block["paragraph"]
    assert block["paragraph"]["color"] == "default"
    
    # Validate rich text content
    rich_text = block["paragraph"]["rich_text"]
    assert len(rich_text) > 1  # Should have multiple segments for formatting
    
    # Find the bold segment
    bold_segment = next((segment for segment in rich_text 
                        if segment["text"]["content"].strip() == "bold" 
                        and segment["annotations"]["bold"] is True), None)
    assert bold_segment is not None
    assert bold_segment["type"] == "text"
    
    # Find the italic segment
    italic_segment = next((segment for segment in rich_text 
                          if segment["text"]["content"].strip() == "italic" 
                          and segment["annotations"]["italic"] is True), None)
    assert italic_segment is not None
    assert italic_segment["type"] == "text"
    
    # Store a representative example of a paragraph with formatting
    store_example(request, {
        'markdown': 'This paragraph has **bold** and *italic* formatting.',
        'notion_api': block
    })

    # Store updated example
    store_example(request, {
        'markdown': 'This paragraph has **bold** and *italic* formatting.',
        'notion_api': block
    })

def test_multiple_paragraphs(request):
    """Test that multiple paragraphs convert correctly."""
    # Create three paragraph elements
    para1 = create_para_element("First paragraph.")
    para2 = create_para_element("Second paragraph.")
    para3 = create_para_element("Third paragraph.")
    
    # Convert each paragraph separately
    # Convert each paragraph separately
    blocks = []
    
    for para in [para1, para2, para3]:
        paragraph_blocks = ParagraphManager.convert(para)
        blocks.extend([block.to_dict() for block in paragraph_blocks])
    # Verify we have three paragraphs
    assert len(blocks) == 3
    
    # Check each block is a paragraph with proper API structure
    for i, block in enumerate(blocks):
        # Basic structure checks
        assert block["object"] == "block"
        assert block["type"] == "paragraph"
        assert "paragraph" in block
        assert "rich_text" in block["paragraph"]
        assert "color" in block["paragraph"]
        assert block["paragraph"]["color"] == "default"
        
        # Check correct content for each paragraph
        rich_text = block["paragraph"]["rich_text"]
        if i == 0:
            assert rich_text[0]["text"]["content"] == "First paragraph."
        elif i == 1:
            assert rich_text[0]["text"]["content"] == "Second paragraph."
        elif i == 2:
            assert rich_text[0]["text"]["content"] == "Third paragraph."
        
        # Verify each rich_text entry has the required API structure
        for segment in rich_text:
            assert "type" in segment
            assert "text" in segment
            assert "text" in segment
            assert "content" in segment["text"]
            assert "annotations" in segment
    
    # Store a representative example of a single paragraph (from the three)
    store_example(request, {
        'markdown': 'First paragraph.\n\nSecond paragraph.\n\nThird paragraph.',
        'notion_api': blocks[0],
        'notes': 'Multiple paragraphs are represented as separate block objects in Notion API'
    })

def test_paragraph_with_mixed_formatting(request):
    """Test paragraphs with mixed formatting styles."""
    # Create a panflute paragraph with mixed formatting
    # For nested formatting, we need to create nested panflute elements
    nested_content = pf.Emph(pf.Str("nested italic"))
    
    elements = [
        pf.Str("This has"),
        pf.Space(),
        pf.Strong(pf.Str("bold text with"), pf.Space(), nested_content),
        pf.Space(),
        pf.Str("and"),
        pf.Space(),
        pf.Code("code"),
        pf.Str(".")
    ]
    
    para = pf.Para(*elements)
    
    # Convert to Notion paragraph using ParagraphManager
    paragraph_blocks = ParagraphManager.convert(para)
    assert len(paragraph_blocks) == 1
    
    # Get the paragraph model
    paragraph_block = paragraph_blocks[0]
    assert isinstance(paragraph_block, Paragraph)
    
    # Convert to dictionary using to_dict()
    block = paragraph_block.to_dict()
    
    # Basic structure checks
    assert block["object"] == "block"
    assert block["type"] == "paragraph"
    assert "paragraph" in block
    assert "rich_text" in block["paragraph"]
    assert "color" in block["paragraph"]
    assert block["paragraph"]["color"] == "default"
    
    # At least 3 segments (normal, bold+italic, code)
    rich_text = block["paragraph"]["rich_text"]
    assert len(rich_text) >= 3
    
    # Check for code segment
    code_segment = next((segment for segment in rich_text 
                        if segment["text"]["content"].strip() == "code" 
                        and segment["annotations"]["code"] is True), None)
    assert code_segment is not None
    assert code_segment["type"] == "text"
    
    # Find text with both bold and italic
    nested_segment = next((segment for segment in rich_text
                          if "nested italic" in segment["text"]["content"]
                          and segment["annotations"]["bold"] is True
                          and segment["annotations"]["italic"] is True), None)
    assert nested_segment is not None
    assert nested_segment["type"] == "text"
    
    # Store a representative example of mixed formatting
    store_example(request, {
        'markdown': 'This has **bold text with *nested italic*** and `code`.',
        'notion_api': block,
        'notes': 'Shows how nested formatting and code are represented in Notion API'
    })

