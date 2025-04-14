"""Inline element handling for TextManager."""

from typing import Dict, Any, List, Optional
import panflute as pf

from .text import Annotations

class NotionInlineElement:
    """Base class for inline elements in Notion."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Notion API format."""
        raise NotImplementedError

class Text(NotionInlineElement):
    """Represents a text element with annotations."""

    def __init__(self, content: str, annotations: Optional[Annotations] = None):
        self.content = content
        self.annotations = annotations or Annotations()
        
    def __repr__(self) -> str:
        return f"Text({self.content!r}, annotations={self.annotations})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Notion API format."""
        if self.annotations.equation:
            return {
                "type": "equation",
                "equation": {
                    "expression": self.content
                },
                "annotations": self.annotations.to_dict(),
                "plain_text": self.content
            }
        else:
            return {
                "type": "text",
                "text": {
                    "content": self.content
                },
                "annotations": self.annotations.to_dict(),
                "plain_text": self.content
            }

def merge_consecutive_texts(elements: List[NotionInlineElement]) -> List[NotionInlineElement]:
    """Merge consecutive text elements with identical annotations."""
    if not elements:
        return []

    result = []
    current = None

    for element in elements:
        if not isinstance(element, Text):
            if current:
                result.append(current)
                current = None
            result.append(element)
            continue

        if current is None:
            current = element
        elif (isinstance(current, Text) and 
              current.annotations.__dict__ == element.annotations.__dict__):
            current.content += element.content
        else:
            result.append(current)
            current = element

    if current:
        result.append(current)

    return result

class InlineElementConverter:
    """Static registry of custom element converters."""
    _converters = {}
    
    @classmethod
    def register(cls, elem_type, converter_func):
        """Register a converter function for an element type."""
        cls._converters[elem_type] = converter_func
        
    @classmethod
    def convert(cls, elem, annotations=None) -> Optional[NotionInlineElement]:
        """Convert an element using a registered converter."""
        for elem_type, converter in cls._converters.items():
            if isinstance(elem, elem_type):
                return converter(elem, annotations)
        return None


def clean_latex_expression(expression: str) -> str:
    """Clean up LaTeX expression for Notion's KaTeX rendering."""
    # Remove common LaTeX environment delimiters if present
    expr = expression.strip()
    
    # Handle equation environments
    if expr.startswith(r'\begin{equation}') and expr.endswith(r'\end{equation}'):
        expr = expr[len(r'\begin{equation}'):-len(r'\end{equation}')].strip()
    elif expr.startswith(r'\begin{align}') and expr.endswith(r'\end{align}'):
        expr = expr[len(r'\begin{align}'):-len(r'\end{align}')].strip()
    elif expr.startswith(r'\begin{aligned}') and expr.endswith(r'\end{aligned}'):
        expr = expr[len(r'\begin{aligned}'):-len(r'\end{aligned}')].strip()
    elif expr.startswith(r'\begin{gather}') and expr.endswith(r'\end{gather}'):
        expr = expr[len(r'\begin{gather}'):-len(r'\end{gather}')].strip()
    
    # Remove \label{} commands as KaTeX doesn't support them
    if r'\label{' in expr:
        parts = expr.split(r'\label{')
        expr = parts[0]
        for part in parts[1:]:
            if '}' in part:
                expr += part.split('}', 1)[1]
    
    # Convert LaTeX commands to KaTeX-compatible versions
    latex_to_katex = {
        r'\eqref': r'\ref',  # KaTeX doesn't support \eqref
    }
    
    for latex_cmd, katex_cmd in latex_to_katex.items():
        expr = expr.replace(latex_cmd, katex_cmd)
    
    return expr


def convert_math_element(elem: pf.Math, annotations: Optional[Annotations] = None) -> Text:
    """Convert a Math element to a Text with equation=True."""
    if annotations is None:
        annotations = Annotations()
    else:
        annotations = annotations.copy()
    
    expression = clean_latex_expression(elem.text)
    annotations.set_equation(True)
    return Text(expression, annotations)


# Register Math element conversion
InlineElementConverter.register(pf.Math, convert_math_element)

