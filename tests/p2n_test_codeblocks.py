"""
Tests for code block conversion using CodeManager.

These tests focus on the conversion of panflute CodeBlock elements to Notion code blocks,
including simple code blocks, code blocks with language specification, and code blocks with
captions/filenames. All tests validate against the Notion API expected structure:
{
  "object": "block",
  "type": "code",
  "code": {
    "rich_text": [
      {
        "type": "text",
        "text": { "content": "Code content here" },
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
    "language": "python",
    "caption": []  # Optional caption array
  }
}
"""

import pytest
import panflute as pf
from conftest import debug_p2n

from pandoc_notion.models.code import Code
from pandoc_notion.managers.code_manager import CodeManager
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


def create_code_block(code_content, language=None, caption=None):
    """Create a panflute CodeBlock element with the given content and attributes.
    
    Args:
        code_content: String containing the code
        language: Optional language for syntax highlighting
        caption: Optional caption or filename
        
    Returns:
        A panflute CodeBlock element
    """
    classes = [language] if language else []
    attributes = {}
    if caption:
        attributes["caption"] = caption
    
    return pf.CodeBlock(code_content, classes=classes, attributes=attributes)


@debug_p2n(input_is_ast=True)
def test_basic_code_block(request):
    """Test that a simple code block converts correctly using CodeManager."""
    # Create a panflute CodeBlock element without language specification
    code_content = "function hello() {\n  console.log('Hello, world!');\n}"
    code_block = create_code_block(code_content)
    
    # Store input for debugging
    debug_p2n.current.input = code_block
    
    # Convert to Notion code block using CodeManager
    code_blocks = CodeManager.convert(code_block)
    assert len(code_blocks) == 1
    
    # Get the code model
    code_block_model = code_blocks[0]
    assert isinstance(code_block_model, Code)
    
    # Convert to dictionary using to_dict()
    block = code_block_model.to_dict()
    
    # Store output for debugging
    debug_p2n.current.output = block
    
    # Basic structure checks
    assert block["object"] == "block"
    assert block["type"] == "code"
    assert "code" in block
    assert "rich_text" in block["code"]
    assert "language" in block["code"]
    assert block["code"]["language"] == "plain text"  # Default language
    
    # Validate rich text content
    rich_text = block["code"]["rich_text"]
    assert len(rich_text) == 1
    
    # Check code content
    content = rich_text[0]["text"]["content"]
    assert content == code_content
    
    # Validate annotations
    assert "annotations" in rich_text[0]
    assert rich_text[0]["annotations"]["bold"] is False
    assert rich_text[0]["annotations"]["italic"] is False
    assert rich_text[0]["annotations"]["code"] is False


@debug_p2n(input_is_ast=True)
def test_code_block_with_language(request):
    """Test that a code block with language specification converts correctly."""
    # Create a panflute CodeBlock element with Python language
    code_content = "def greet(name):\n    print(f'Hello, {name}!')\n\ngreet('World')"
    language = "python"
    code_block = create_code_block(code_content, language)
    
    # Store input for debugging
    debug_p2n.current.input = code_block
    
    # Convert to Notion code block using CodeManager
    code_blocks = CodeManager.convert(code_block)
    assert len(code_blocks) == 1
    
    # Get the code model
    code_block_model = code_blocks[0]
    assert isinstance(code_block_model, Code)
    
    # Convert to dictionary using to_dict()
    block = code_block_model.to_dict()
    
    # Store output for debugging
    debug_p2n.current.output = block
    
    # Basic structure checks
    assert block["object"] == "block"
    assert block["type"] == "code"
    assert "code" in block
    assert "rich_text" in block["code"]
    assert "language" in block["code"]
    assert block["code"]["language"] == "python"
    
    # Validate rich text content
    rich_text = block["code"]["rich_text"]
    assert len(rich_text) == 1
    
    # Check code content
    content = rich_text[0]["text"]["content"]
    assert content == code_content


@debug_p2n(input_is_ast=True)
def test_code_block_with_caption(request):
    """Test that a code block with caption converts correctly."""
    # Create a panflute CodeBlock element with caption/filename
    code_content = "SELECT * FROM users WHERE age > 18;"
    language = "sql"
    caption = "user_query.sql"
    code_block = create_code_block(code_content, language, caption)
    
    # Store input for debugging
    debug_p2n.current.input = code_block
    
    # Convert to Notion code block using CodeManager
    code_blocks = CodeManager.convert(code_block)
    assert len(code_blocks) == 1
    
    # Get the code model
    code_block_model = code_blocks[0]
    assert isinstance(code_block_model, Code)
    
    # Convert to dictionary using to_dict()
    block = code_block_model.to_dict()
    
    # Store output for debugging
    debug_p2n.current.output = block
    
    # Basic structure checks
    assert block["object"] == "block"
    assert block["type"] == "code"
    assert "code" in block
    assert "rich_text" in block["code"]
    assert "language" in block["code"]
    assert "caption" in block["code"]
    assert block["code"]["language"] == "sql"
    
    # Validate caption
    assert len(block["code"]["caption"]) == 1
    assert block["code"]["caption"][0]["text"]["content"] == caption


@debug_p2n(input_is_ast=True)
def test_code_block_language_mapping(request):
    """Test that language mapping works correctly for various languages."""
    # Test a few common language mappings
    language_tests = [
        # (input_language, expected_notion_language)
        ("js", "javascript"),
        ("py", "python"),
        ("cpp", "c++"),
        ("csharp", "c#"),
        ("sh", "bash"),
        ("yaml", "yaml"),
        ("unknown_language", "plain text")  # fallback
    ]
    
    for input_lang, expected_lang in language_tests:
        code_content = f"// Sample code in {input_lang}"
        code_block = create_code_block(code_content, input_lang)
        
        # Convert to Notion code block using CodeManager
        code_blocks = CodeManager.convert(code_block)
        assert len(code_blocks) == 1
        
        # Get the code model and convert to dictionary
        block = code_blocks[0].to_dict()
        
        # Check language mapping
        assert block["code"]["language"] == expected_lang, f"Expected {input_lang} to map to {expected_lang}"


def create_nested_structure_with_code():
    """Create a nested document structure containing code blocks."""
    # Create a code block
    code_content = "console.log('Hello!');"
    code_block = create_code_block(code_content, "javascript")
    
    # Create a paragraph
    para = pf.Para(pf.Str("Here's some code:"))
    
    # Create a bullet list with a code block in it
    nested_code = create_code_block("print('Nested code')", "python")
    list_item = pf.ListItem(pf.Plain(pf.Str("List item with code:")), nested_code)
    bullet_list = pf.BulletList(list_item)
    
    # Return a list of these elements
    return [para, code_block, bullet_list]


@debug_p2n(input_is_ast=True)
def test_code_block_in_complex_structure(request):
    """Test that code blocks within complex structures convert correctly."""
    # Create a document structure with nested code blocks
    elements = create_nested_structure_with_code()
    
    # Store input for debugging
    debug_p2n.current.input = elements
    
    # For this test, we'll focus on the standalone code block (second element)
    code_block = elements[1]
    assert isinstance(code_block, pf.CodeBlock)
    
    # Convert to Notion code block using CodeManager
    code_blocks = CodeManager.convert(code_block)
    assert len(code_blocks) == 1
    
    # Get the code model
    code_block_model = code_blocks[0]
    assert isinstance(code_block_model, Code)
    
    # Convert to dictionary using to_dict()
    block = code_block_model.to_dict()
    
    # Store output for debugging
    debug_p2n.current.output = block
    
    # Basic structure checks
    assert block["object"] == "block"
    assert block["type"] == "code"
    assert block["code"]["language"] == "javascript"
    assert block["code"]["rich_text"][0]["text"]["content"] == "console.log('Hello!');"


@debug_p2n(input_is_ast=True)
def test_multiline_code_block(request):
    """Test that multiline code blocks with indentation preserve formatting."""
    # Create a code block with complex multiline content and indentation
    code_content = """function calculateFactorial(n) {
    // Base case
    if (n === 0 || n === 1) {
        return 1;
    }
    
    // Recursive case
    return n * calculateFactorial(n - 1);
}

// Test the function
for (let i = 0; i < 5; i++) {
    console.log(`Factorial of ${i} is ${calculateFactorial(i)}`);
}"""
    
    code_block = create_code_block(code_content, "javascript")
    
    # Store input for debugging
    debug_p2n.current.input = code_block
    
    # Convert to Notion code block
    code_blocks = CodeManager.convert(code_block)
    block = code_blocks[0].to_dict()
    
    # Store output for debugging
    debug_p2n.current.output = block
    
    # Check that the exact content is preserved, including all whitespace and indentation
    rich_text = block["code"]["rich_text"]
    assert rich_text[0]["text"]["content"] == code_content
    
    # Make sure all lines are present
    lines = code_content.split("\n")
    for line in lines:
        assert line in rich_text[0]["text"]["content"]

