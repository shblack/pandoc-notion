
"""
Tests for inline equation conversion.

This module tests conversion of panflute Math elements with format='InlineMath' 
to Notion equation representations in inline contexts.
"""

import pytest
import panflute as pf
from conftest import store_example

from pandoc_notion.managers.text_manager import TextManager
from pandoc_notion.managers.text_manager_inline import (
    EquationElement, 
    convert_math_element
)
from pandoc_notion.registry import ManagerRegistry
from pandoc_notion.managers.registry_mixin import set_registry


@pytest.fixture(autouse=True)
def setup_registry():
    """Set up registry with default managers for all tests."""
    registry = ManagerRegistry()
    set_registry(registry)
    return registry


def test_inline_equation_conversion(request):
    """Test that a simple inline math equation converts correctly using TextManager."""
    # Create a Math element with format="InlineMath"
    math_elem = pf.Math(text="E = mc^2", format="InlineMath")
    
    # Convert using TextManager
    result = TextManager.to_dict([math_elem])
    
    # Assert structure is correct
    assert len(result) == 1
    assert result[0]["type"] == "equation"
    assert result[0]["equation"]["expression"] == "E = mc^2"
    assert "annotations" in result[0]
    
    store_example(request, {
        'markdown': '$E = mc^2$',
        'notion_api': result[0],
        'notes': 'Simple inline math equation converted to equation text element'
    })


def test_equation_element_directly(request):
    """Test direct conversion of Math element to EquationElement."""
    # Create a Math element with format="InlineMath"
    math_elem = pf.Math(text="E = mc^2", format="InlineMath")
    
    # Convert directly using convert_math_element
    equation_element = convert_math_element(math_elem)
    result = equation_element.to_dict()
    
    # Assert structure is correct
    assert result["type"] == "equation"
    assert result["equation"]["expression"] == "E = mc^2"
    assert "annotations" in result
    
    store_example(request, {
        'markdown': '$E = mc^2$',
        'notion_api': result,
        'notes': 'Direct conversion of Math element to EquationElement'
    })


def test_complex_inline_equation(request):
    """Test that a complex inline math equation converts correctly."""
    # Create a complex math element
    math_elem = pf.Math(
        text=r"\frac{1}{\sigma\sqrt{2\pi}}e^{-\frac{1}{2}(\frac{x-\mu}{\sigma})^2}",
        format="InlineMath"
    )
    
    # Convert using TextManager
    result = TextManager.to_dict([math_elem])
    
    # Assert LaTeX is preserved properly
    assert len(result) == 1
    assert result[0]["type"] == "equation"
    assert r"\frac" in result[0]["equation"]["expression"]
    assert r"e^{-\frac" in result[0]["equation"]["expression"]
    
    store_example(request, {
        'markdown': r'$\frac{1}{\sigma\sqrt{2\pi}}e^{-\frac{1}{2}(\frac{x-\mu}{\sigma})^2}$',
        'notion_api': result[0],
        'notes': 'Complex inline math equation with LaTeX commands'
    })
