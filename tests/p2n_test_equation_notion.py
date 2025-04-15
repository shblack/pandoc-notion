"""
Integration tests for equation conversions in pandoc-notion.

Tests proper conversion of Markdown math expressions to Notion blocks,
including inline and block equations, complex expressions, and various contexts.
"""
import time
import pytest
from typing import Dict, Any, List

# Markdown content with various equation types
TEST_EQUATION_MARKDOWN = '''# Mathematical Equations Test

## Inline Equations

This paragraph contains an inline equation $E = mc^2$ within the text.

Here's another paragraph with multiple inline equations:
$a + b = c$ for addition, $a - b = c$ for subtraction, and $a \\times b = c$ for multiplication.

## Block Equations

The quadratic formula is:

$$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$

The normal distribution formula:

$$f(x) = \\frac{1}{\\sigma\\sqrt{2\\pi}}e^{-\\frac{1}{2}(\\frac{x-\\mu}{\\sigma})^2}$$

## Complex Equations

Maxwell's equation in differential form:

$$\\nabla \\times \\vec{E} = -\\frac{\\partial \\vec{B}}{\\partial t}$$

Einstein's field equations:

$$G_{\\mu\\nu} + \\Lambda g_{\\mu\\nu} = \\frac{8\\pi G}{c^4}T_{\\mu\\nu}$$

## Multi-line Equations

A system of equations:

$$
\\begin{align}
3x + 2y &= 5 \\\\
2x - 3y &= -4
\\end{align}
$$

Matrix representation:

$$
A = \\begin{bmatrix}
a_{11} & a_{12} & a_{13} \\\\
a_{21} & a_{22} & a_{23} \\\\
a_{31} & a_{32} & a_{33}
\\end{bmatrix}
$$

## Equations in Different Contexts

### In Lists

* First item with equation $F = ma$
* Second item with equation $E = hf$
* Third item with equation $PV = nRT$

### In Blockquotes

> Energy equation: $E = mc^2$
>
> Momentum equation: $p = mv$

### With Formatting

The equation **$F = G\\frac{m_1 m_2}{r^2}$** is Newton's law of gravitation.

The equation *$e^{i\\pi} + 1 = 0$* is Euler's identity.
'''


@pytest.mark.notion_integration
def test_equation_conversion(notion_test):
    """
    Test conversion of equations with proper rendering and placement in Notion.
    
    This test:
    1. Creates a Notion page with various equation types
    2. Retrieves the page content and extracts equations
    3. Verifies all expected equations are properly rendered
    """
    print("[DEBUG] === Test equation_conversion starting ===")

    # ===== STEP 1: Create a single test page =====
    page_id = notion_test.create_page(
        markdown_content=TEST_EQUATION_MARKDOWN,
        title=f"Equation Test Page - {notion_test.test_name}"
    )
    
    # Verify page exists
    page = notion_test.client.client.pages.retrieve(page_id)
    assert page["id"] == page_id, "Page creation failed"
    
    # ===== STEP 2: Retrieve blocks and extract equations =====
    # Allow Notion API time to process blocks
    print("[DEBUG] Waiting 1 second before retrieving blocks...")
    time.sleep(1)
    
    # Get all blocks from the page
    blocks_response = notion_test.client.client.blocks.children.list(page_id)
    results = blocks_response["results"]
    
    # Initialize collections for storing equations
    inline_equations = []
    block_equation_blocks = []
    expected_context_texts = []

    # ===== STEP 3: Process blocks and extract equations =====
    print("[DEBUG] Extracting equations from retrieved blocks...")
    for block in results:
        block_type = block.get("type")
        content_key = block_type  # e.g., "paragraph", "bulleted_list_item"
        
        # Extract text content for context verification
        if block_type and content_key in block:
            rich_text_array = block[content_key].get("rich_text", [])
            joined_text = "".join([rt.get("plain_text", "") for rt in rich_text_array])
            if joined_text.strip():
                expected_context_texts.append(joined_text)
            
            # Find inline equations
            for rt in rich_text_array:
                if rt.get("type") == "equation":
                    print(f"[DEBUG] Found inline equation in {block_type}: {rt['equation']['expression']}")
                    inline_equations.append(rt)
            
            # Check for nested blocks (quotes, etc.)
            if block.get("has_children"):
                print(f"[DEBUG] Block {block['id']} ({block_type}) has children, fetching...")
                try:
                    child_response = notion_test.client.client.blocks.children.list(block["id"])
                    for child_block in child_response.get("results", []):
                        child_type = child_block.get("type")
                        child_content_key = child_type
                        print(f"[DEBUG]  - Child block type: {child_type}")
                        
                        if child_type and child_content_key in child_block:
                            child_rich_text = child_block[child_content_key].get("rich_text", [])
                            child_joined_text = "".join([rt.get("plain_text", "") for rt in child_rich_text])
                            if child_joined_text.strip():
                                expected_context_texts.append(child_joined_text)
                                
                            # Extract equations from child blocks
                            for child_rt in child_rich_text:
                                if child_rt.get("type") == "equation":
                                    print(f"[DEBUG] Found inline equation in child {child_type}: {child_rt['equation']['expression']}")
                                    inline_equations.append(child_rt)
                except Exception as child_err:
                    print(f"[WARNING] Error fetching children for block {block['id']}: {child_err}")
    
    # ===== STEP 4: Identify block equations =====
    # In Notion's API, block equations are paragraph blocks with a single equation
    block_equation_blocks = [
        b for b in results 
        if b.get("type") == "paragraph" 
        and len(b.get("paragraph", {}).get("rich_text", [])) == 1 
        and b.get("paragraph", {}).get("rich_text", [])[0].get("type") == "equation"
    ]
    
    # ===== STEP 5: Extract equation expressions =====
    inline_expressions = [eq.get("equation", {}).get("expression", "") for eq in inline_equations]
    print(f"\n--- Found {len(inline_equations)} inline equations ---")
    print(f"Inline Expressions Found: {inline_expressions}")
    
    block_expressions = [
        b.get("paragraph", {}).get("rich_text", [])[0].get("equation", {}).get("expression", "") 
        for b in block_equation_blocks
    ]
    print(f"\n--- Found {len(block_equation_blocks)} block equation paragraphs ---")
    print(f"Block Expressions Found: {block_expressions}")
    
    # ===== STEP 6: Verify equations =====
    # 1. Check inline equations
    assert len(inline_equations) > 0, "No inline equations found"
    assert "E = mc^2" in inline_expressions, "Missing inline Einstein's equation (E=mc^2)"
    assert "a + b = c" in inline_expressions, "Missing inline addition equation (a+b=c)"
    assert "F = ma" in inline_expressions, "Missing inline Newton's second law (F=ma) from list"
    assert "E = hf" in inline_expressions, "Missing inline Planck's equation (E=hf) from list"
    assert "PV = nRT" in inline_expressions, "Missing inline Ideal Gas Law (PV=nRT) from list"
    assert "p = mv" in inline_expressions, "Missing inline momentum equation (p=mv) from quote"
    assert any("F = G\\frac{m_1 m_2}{r^2}" in expr for expr in inline_expressions), "Missing Newton's gravitation law"
    assert any("e^{i\\pi} + 1 = 0" in expr for expr in inline_expressions), "Missing Euler's identity"
    
    # 2. Check block equations
    assert len(block_equation_blocks) > 0, "No block equations found"
    assert any("x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}" in expr for expr in block_expressions), "Missing block quadratic formula"
    assert any("f(x) = \\frac{1}{\\sigma\\sqrt{2\\pi}}e^{-\\frac{1}{2}(\\frac{x-\\mu}{\\sigma})^2}" in expr for expr in block_expressions), "Missing block normal distribution"
    assert any("\\nabla \\times \\vec{E} = -\\frac{\\partial \\vec{B}}{\\partial t}" in expr for expr in block_expressions), "Missing block Maxwell's equation"
    assert any("G_{\\mu\\nu} + \\Lambda g_{\\mu\\nu} = \\frac{8\\pi G}{c^4}T_{\\mu\\nu}" in expr for expr in block_expressions), "Missing block Einstein's field equations"
    
    # 3. Check multi-line equations
    assert any("\\begin{align}" in expr and "3x + 2y &= 5" in expr for expr in block_expressions), "Missing block system of equations"
    assert any("\\begin{bmatrix}" in expr and "a_{11}" in expr for expr in block_expressions), "Missing block matrix representation"
    
    # 4. Verify context text
    expected_context_phrases = [
        "quadratic formula is",
        "normal distribution formula",
        "equation in differential form",
        "field equations",
        "system of equations",
        "Matrix representation"
    ]
    
    for phrase in expected_context_phrases:
        assert any(phrase in text for text in expected_context_texts), f"Missing context text: '{phrase}'"
    
    print("[DEBUG] === Test equation_conversion completed successfully ===")
    
    # Return detailed data for debugging
    return {
        "inline_equations": inline_expressions,
        "block_equations": block_expressions,
        "context_texts": expected_context_texts,
        "block_count": len(results),
        "equation_analysis": {
            "inline_count": len(inline_equations),
            "block_count": len(block_equation_blocks),
            "specific_equations": {
                "quadratic_formula": any("x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}" in expr for expr in block_expressions),
                "einstein": "E = mc^2" in inline_expressions,
                "maxwell": any("\\nabla \\times \\vec{E}" in expr for expr in block_expressions)
            }
        }
    }

