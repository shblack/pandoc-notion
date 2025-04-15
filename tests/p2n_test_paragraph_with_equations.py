"""
Tests for equation integration with other content.

This module tests how equations work together with other content types 
such as paragraphs with text, formatted content, and multiple equations.
"""

import pytest
import panflute as pf
from conftest import store_example

from pandoc_notion.managers.text_manager import TextManager
from pandoc_notion.managers.paragraph_manager import ParagraphManager
from pandoc_notion.registry import ManagerRegistry
from pandoc_notion.managers.registry_mixin import set_registry


@pytest.fixture(autouse=True)
def setup_registry():
    """Set up registry with default managers for all tests."""
    registry = ManagerRegistry()
    set_registry(registry)
    return registry


def test_paragraph_with_equation(request):
    """Test paragraph containing an inline equation using ParagraphManager."""
    # Create a paragraph with text and an equation
    para = pf.Para(
        pf.Str("Einstein's"),
        pf.Space(),
        pf.Str("equation:"),
        pf.Space(),
        pf.Math(text="E = mc^2", format="InlineMath")
    )
    
    # Convert the paragraph using ParagraphManager
    result = ParagraphManager.to_dict(para)
    
    # Assert the structure is correct
    assert len(result) == 1
    assert result[0]["type"] == "paragraph"
    assert "paragraph" in result[0]
    assert "rich_text" in result[0]["paragraph"]
    
    # Check the rich_text array
    rich_text = result[0]["paragraph"]["rich_text"]
    
    # Find the equation in the rich_text array
    equation = None
    for rt in rich_text:
        if rt["type"] == "equation":
            equation = rt
            break
    
    # Assert the equation was found and has the correct content
    assert equation is not None
    assert equation["equation"]["expression"] == "E = mc^2"
    
    store_example(request, {
        'markdown': "Einstein's equation: $E = mc^2$",
        'notion_api': result[0],
        'notes': 'Paragraph with text and inline equation'
    })


def test_paragraph_with_multiple_equations(request):
    """Test paragraph with multiple equations using ParagraphManager."""
    # Create a paragraph with text and multiple equations
    para = pf.Para(
        pf.Str("The"),
        pf.Space(),
        pf.Str("quadratic"),
        pf.Space(),
        pf.Str("formula"),
        pf.Space(),
        pf.Math(text="ax^2 + bx + c = 0", format="InlineMath"),
        pf.Space(),
        pf.Str("has"),
        pf.Space(),
        pf.Str("solutions"),
        pf.Space(),
        pf.Math(text=r"x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}", format="InlineMath")
    )
    
    # Convert the paragraph using ParagraphManager
    result = ParagraphManager.to_dict(para)
    
    # Assert the structure is correct
    assert len(result) == 1
    assert result[0]["type"] == "paragraph"
    
    # Check the rich_text array
    rich_text = result[0]["paragraph"]["rich_text"]
    
    # Find equations in the rich_text array
    equations = [rt for rt in rich_text if rt["type"] == "equation"]
    assert len(equations) >= 2  # Should have at least 2 equations
    
    # Check the expressions in the equations
    expressions = [eq["equation"]["expression"] for eq in equations]
    assert "ax^2 + bx + c = 0" in expressions
    
    # Check for the complex equation with fractions
    complex_expressions = [expr for expr in expressions if r"\frac" in expr]
    assert len(complex_expressions) > 0
    assert r"\sqrt" in complex_expressions[0]
    
    store_example(request, {
        'markdown': 'The quadratic formula $ax^2 + bx + c = 0$ has solutions $x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$',
        'notion_api': result[0],
        'notes': 'Paragraph with multiple inline equations'
    })


def test_formatted_equation_in_paragraph(request):
    """Test equation with formatting in a paragraph."""
    # Create a paragraph with an emphasized equation
    para = pf.Para(
        pf.Str("The"),
        pf.Space(),
        pf.Str("Pythagorean"),
        pf.Space(),
        pf.Str("theorem:"),
        pf.Space(),
        pf.Emph(
            pf.Math(text="a^2 + b^2 = c^2", format="InlineMath")
        )
    )
    
    # Convert the paragraph using ParagraphManager
    result = ParagraphManager.to_dict(para)
    
    # Find the equation in the rich_text array
    rich_text = result[0]["paragraph"]["rich_text"]
    equation = None
    for rt in rich_text:
        if rt["type"] == "equation":
            equation = rt
            break
    
    # Assert the equation was found and properly formatted
    assert equation is not None
    assert equation["equation"]["expression"] == "a^2 + b^2 = c^2"
    assert equation["annotations"]["italic"] == True
    
    store_example(request, {
        'markdown': 'The Pythagorean theorem: *$a^2 + b^2 = c^2$*',
        'notion_api': result[0],
        'notes': 'Paragraph with a formatted equation'
    })


def test_maxwell_equation_in_paragraph(request):
    """Test Maxwell's equation within a paragraph."""
    # Create a paragraph with text and Maxwell's equation
    para = pf.Para(
        pf.Str("Maxwell's"),
        pf.Space(),
        pf.Str("equation:"),
        pf.Space(),
        pf.Math(
            text=r"\nabla \times \vec{E} = -\frac{\partial \vec{B}}{\partial t}",
            format="InlineMath"
        )
    )
    
    # Convert the paragraph using ParagraphManager
    result = ParagraphManager.to_dict(para)
    
    # Find the equation in the rich_text array
    rich_text = result[0]["paragraph"]["rich_text"]
    equation = None
    for rt in rich_text:
        if rt["type"] == "equation":
            equation = rt
            break
    
    # Assert the equation was found and contains the correct expression
    assert equation is not None
    assert equation["equation"]["expression"] == r"\nabla \times \vec{E} = -\frac{\partial \vec{B}}{\partial t}"
    
    store_example(request, {
        'markdown': r'Maxwell\'s equation: $\nabla \times \vec{E} = -\frac{\partial \vec{B}}{\partial t}$',
        'notion_api': result[0],
        'notes': 'Paragraph with Maxwell\'s equation'
    })


def test_calculus_formula_in_paragraph(request):
    """Test handling of calculus formula within a paragraph."""
    # Create a paragraph with text and a calculus formula
    para = pf.Para(
        pf.Str("The"),
        pf.Space(),
        pf.Str("power"),
        pf.Space(),
        pf.Str("rule:"),
        pf.Space(),
        pf.Math(
            text=r"\frac{d}{dx}[x^n] = nx^{n-1}",
            format="InlineMath"
        )
    )
    
    # Convert the paragraph using ParagraphManager
    result = ParagraphManager.to_dict(para)
    
    # Find the equation in the rich_text array
    rich_text = result[0]["paragraph"]["rich_text"]
    equation = None
    for rt in rich_text:
        if rt["type"] == "equation":
            equation = rt
            break
    
    # Assert the equation was found and contains the correct expression
    assert equation is not None
    assert equation["equation"]["expression"] == r"\frac{d}{dx}[x^n] = nx^{n-1}"
    
    store_example(request, {
        'markdown': r'The power rule: $\frac{d}{dx}[x^n] = nx^{n-1}$',
        'notion_api': result[0],
        'notes': 'Paragraph with calculus power rule formula'
    })
