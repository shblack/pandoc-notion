"""
Tests for heading block conversion using HeadingManager.

These tests focus on the conversion of panflute Header elements to Notion heading blocks,
including different levels (H1-H6), formatted headings, and headings with special characters.

Note: Notion only supports heading levels 1-3. Higher heading levels (H4-H6) are
automatically converted to H3 in the Notion API.

All tests validate against the Notion API expected structure:
{
  "object": "block",
  "type": "heading_1", // or heading_2, heading_3
  "heading_1": {      // matching key based on heading level
    "rich_text": [
      {
        "type": "text",
        "text": { "content": "Heading text" },
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

from pandoc_notion.models.heading import Heading
from pandoc_notion.managers.heading_manager import HeadingManager
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


def create_header(text, level):
    """Create a panflute Header element with the given text and level."""
    return pf.Header(pf.Str(text), level=level)


def create_formatted_header(text_parts, level):
    """Create a header with formatted text content.
    
    Args:
        text_parts: List of tuples (text, format) where format can be 
                   'bold', 'italic', 'code', or None
        level: Heading level (1-6)
    """
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
    
    return pf.Header(*elements, level=level)


def test_heading_levels(request):
    """Test that headings of all levels (H1-H6) convert correctly."""
    # Create headings of all levels
    headers = [
        create_header(f"Heading {i+1}", level=i+1)
        for i in range(6)  # Levels 1-6
    ]
    
    # Convert each header and collect results
    blocks = []
    
    for header in headers:
        # Convert to Notion heading blocks using HeadingManager
        heading_blocks = HeadingManager.convert(header)
        
        # Convert each heading block to a dictionary for testing
        for block in heading_blocks:
            blocks.append(block.to_dict())
    
    # Should have 6 heading blocks (one for each level)
    assert len(blocks) == 6
    
    # Check each heading level
    for i, block in enumerate(blocks):
        # Get expected heading level (Notion only supports H1-H3, others become H3)
        expected_level = min(i + 1, 3)  # Cap at level 3
        
        # Basic structure checks
        assert block["object"] == "block"
        assert block["type"] == f"heading_{expected_level}"
        assert f"heading_{expected_level}" in block
        
        # Verify heading block structure
        heading_data = block[f"heading_{expected_level}"]
        assert "rich_text" in heading_data
        assert "color" in heading_data
        assert heading_data["color"] == "default"
        
        # Verify that original heading level number is reflected in content
        original_level = i + 1
        heading_content = f"Heading {original_level}"
        
        # Check content
        rich_text = heading_data["rich_text"]
        assert len(rich_text) > 0
        assert "text" in rich_text[0]
        assert "content" in rich_text[0]["text"]
        assert rich_text[0]["text"]["content"] == heading_content
        
        # Validate rich_text structure
        assert "type" in rich_text[0]
        assert rich_text[0]["type"] == "text"
        assert "annotations" in rich_text[0]
    
    # Store a representative sample showing H4->H3 conversion
    store_example(request, {
        'markdown': '#### Heading 4 (will be converted to H3)',
        'notion_api': blocks[3],  # Fourth heading (originally H4) shows conversion to H3
        'notes': 'Notion API converts H4+ to H3 since only H1-H3 are supported'
    })


def test_heading_with_formatting(request):
    """Test that headings with formatting (bold, italic) convert correctly."""
    # Create formatted headers
    h1_parts = [
        ("Heading with ", None),
        ("bold", "bold")
    ]
    h1 = create_formatted_header(h1_parts, level=1)
    
    h2_parts = [
        ("Heading with ", None),
        ("italic", "italic")
    ]
    h2 = create_formatted_header(h2_parts, level=2)
    
    # For the bold and italic text, we need to nest elements
    h3 = pf.Header(
        pf.Str("Heading with "),
        pf.Strong(pf.Emph(pf.Str("bold and italic"))),
        level=3
    )
    
    # Convert each formatted heading
    h1_blocks = [block.to_dict() for block in HeadingManager.convert(h1)]
    h2_blocks = [block.to_dict() for block in HeadingManager.convert(h2)]
    h3_blocks = [block.to_dict() for block in HeadingManager.convert(h3)]
    
    # Should have one block for each heading
    assert len(h1_blocks) == 1
    assert len(h2_blocks) == 1 
    assert len(h3_blocks) == 1
    
    # Check heading 1 with bold
    h1_block = h1_blocks[0]
    assert h1_block["object"] == "block"
    assert h1_block["type"] == "heading_1"
    assert "heading_1" in h1_block
    assert "color" in h1_block["heading_1"]
    assert h1_block["heading_1"]["color"] == "default"
    
    h1_rich_text = h1_block["heading_1"]["rich_text"]
    
    # Find bold segment in h1
    bold_segment = next((segment for segment in h1_rich_text 
                        if segment["text"]["content"].strip() == "bold" 
                        and segment["annotations"]["bold"] is True), None)
    assert bold_segment is not None
    assert bold_segment["type"] == "text"
    
    # Check heading 2 with italic
    h2_block = h2_blocks[0]
    assert h2_block["object"] == "block"
    assert h2_block["type"] == "heading_2"
    assert "heading_2" in h2_block
    assert "color" in h2_block["heading_2"]
    assert h2_block["heading_2"]["color"] == "default"
    
    h2_rich_text = h2_block["heading_2"]["rich_text"]
    
    # Find italic segment in h2
    italic_segment = next((segment for segment in h2_rich_text 
                          if segment["text"]["content"].strip() == "italic" 
                          and segment["annotations"]["italic"] is True), None)
    assert italic_segment is not None
    assert italic_segment["type"] == "text"
    
    # Check heading 3 with bold and italic
    h3_block = h3_blocks[0]
    assert h3_block["object"] == "block"
    assert h3_block["type"] == "heading_3"
    assert "heading_3" in h3_block
    assert "color" in h3_block["heading_3"]
    assert h3_block["heading_3"]["color"] == "default"
    
    h3_rich_text = h3_block["heading_3"]["rich_text"]
    
    # Find bold and italic segment in h3
    bold_italic_segment = next((segment for segment in h3_rich_text 
                               if "bold and italic" in segment["text"]["content"]
                               and segment["annotations"]["bold"] is True
                               and segment["annotations"]["italic"] is True), None)
    assert bold_italic_segment is not None
    assert bold_italic_segment["type"] == "text"

    # Store a representative sample showing mixed formatting
    store_example(request, {
        'markdown': '### Heading with ***bold and italic***',
        'notion_api': h3_block,  # Third heading shows both bold and italic
        'notes': 'Heading with nested formatting (bold and italic)'
    })


def test_heading_with_special_characters(request):
    """Test that headings with special characters convert correctly."""
    # Create headers with special characters
    h1 = pf.Header(pf.Str('Heading with & < > \' "'), level=1)
    h2 = pf.Header(pf.Str('Heading with emoji 🚀 😊'), level=2)
    h3 = pf.Header(pf.Str('Heading with non-English characters: 你好, Привет, こんにちは'), level=3)
    
    # Convert to dictionaries
    h1_blocks = [block.to_dict() for block in HeadingManager.convert(h1)]
    h2_blocks = [block.to_dict() for block in HeadingManager.convert(h2)]
    h3_blocks = [block.to_dict() for block in HeadingManager.convert(h3)]
    
    # Check heading 1 with special characters
    h1_block = h1_blocks[0]
    assert h1_block["object"] == "block"
    assert h1_block["type"] == "heading_1"
    assert "heading_1" in h1_block
    assert "rich_text" in h1_block["heading_1"]
    
    h1_text = h1_block["heading_1"]["rich_text"][0]["text"]["content"]
    assert 'Heading with & < > \' "' in h1_text
    
    # Check heading 2 with emoji
    h2_block = h2_blocks[0]
    assert h2_block["object"] == "block"
    assert h2_block["type"] == "heading_2"
    assert "heading_2" in h2_block
    assert "rich_text" in h2_block["heading_2"]
    
    h2_text = h2_block["heading_2"]["rich_text"][0]["text"]["content"]
    assert 'emoji 🚀 😊' in h2_text
    
    # Check heading 3 with non-English characters
    h3_block = h3_blocks[0]
    assert h3_block["object"] == "block"
    assert h3_block["type"] == "heading_3"
    assert "heading_3" in h3_block
    assert "rich_text" in h3_block["heading_3"]
    
    h3_text = h3_block["heading_3"]["rich_text"][0]["text"]["content"]
    assert '你好' in h3_text
    assert 'Привет' in h3_text
    assert 'こんにちは' in h3_text
    
    # Store representative samples showing various special characters
    store_example(request, {
        'markdown': '## Heading with emoji 🚀 😊',
        'notion_api': h2_block,
        'notes': 'Headings support emoji characters in Notion'
    })

