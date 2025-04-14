"""Inline element handling for TextManager."""

from typing import List, Dict, Any, Optional, Callable, Type
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import panflute as pf

from ..models.text import Annotations, Text


class NotionInlineElement(ABC):
    """
    Interface for all elements that can appear in a Notion rich text array.
    
    This is the base class for all inline elements used in Notion blocks,
    such as regular text, equations, code, mentions, etc.
    """
    
    @abstractmethod
    def get_content(self) -> str:
        """Get the text content of this element."""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Notion API dictionary format."""
        pass


@dataclass
class EquationElement(NotionInlineElement):
    """
    Represents an equation in a Notion rich text array.
    
    Equations are displayed as LaTeX in Notion and rendered according 
    to LaTeX syntax.
    """
    expression: str
    annotations: Annotations = field(default_factory=Annotations)
    
    def get_content(self) -> str:
        """Get the text content of this element."""
        return self.expression
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Notion API dictionary format."""
        return {
            "type": "equation",
            "equation": {
                "expression": self.expression
            },
            "annotations": self.annotations.to_dict(),
            "plain_text": self.expression
        }
    
    def __str__(self) -> str:
        """String representation of the equation for debugging."""
        annotations_str = ""
        if not self.annotations.is_default():
            annotations_str = f" with {self.annotations}"
        return f"Equation('{self.expression}'{annotations_str})"


@dataclass
class CodeElement(NotionInlineElement):
    """
    Represents a code element in a Notion rich text array.
    
    This differs from code blocks in that it represents inline code
    rather than block-level code.
    """
    text: str
    annotations: Annotations = field(default_factory=Annotations)
    
    def __post_init__(self):
        """Ensure code annotation is set."""
        self.annotations.set_code(True)
    
    def get_content(self) -> str:
        """Get the text content of this element."""
        return self.text
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Notion API dictionary format."""
        return {
            "type": "text",
            "text": {
                "content": self.text
            },
            "annotations": self.annotations.to_dict(),
            "plain_text": self.text
        }
    
    def __str__(self) -> str:
        """String representation of the code for debugging."""
        return f"Code('{self.text}')"


@dataclass
class MentionElement(NotionInlineElement):
    """
    Represents a mention in a Notion rich text array.
    
    Mentions can reference pages, databases, users, dates, or external resources.
    """
    mention_type: str  # page, database, user, date, etc.
    mention_data: Dict[str, Any]
    annotations: Annotations = field(default_factory=Annotations)
    plain_text: str = ""
    
    def get_content(self) -> str:
        """Get the text content of this element."""
        return self.plain_text
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Notion API dictionary format."""
        return {
            "type": "mention",
            "mention": {
                self.mention_type: self.mention_data
            },
            "annotations": self.annotations.to_dict(),
            "plain_text": self.plain_text
        }
    
    def __str__(self) -> str:
        """String representation of the mention for debugging."""
        return f"Mention({self.mention_type}, {self.plain_text})"


def merge_consecutive_texts(elements: List[NotionInlineElement]) -> List[NotionInlineElement]:
    """
    Merge consecutive Text objects with identical annotations and link status.
    
    This function only merges adjacent Text instances, leaving other types of
    inline elements unchanged.
    
    Args:
        elements: A list of NotionInlineElement objects
        
    Returns:
        A new list with consecutive similar Text objects merged
    """
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
              current.annotations.__dict__ == element.annotations.__dict__ and
              current.link == element.link):
            current.content += element.content
        else:
            result.append(current)
            current = element
    
    if current:
        result.append(current)
    
    return result


class InlineElementConverter:
    """
    Registry for element handlers, mapping Pandoc element types to handler functions.
    
    This class enables extensible conversion of Pandoc elements to Notion inline elements.
    New element types can be added by registering appropriate handler functions.
    """
    _handlers = {}
    
    @classmethod
    def register(cls, elem_type: Type[pf.Element], 
                 handler_func: Callable[[pf.Element, Optional[Annotations]], NotionInlineElement]):
        """
        Register a handler function for a specific Pandoc element type.
        
        Args:
            elem_type: The Pandoc element type to register a handler for
            handler_func: Function that converts the element to a NotionInlineElement
        """
        cls._handlers[elem_type] = handler_func
    
    @classmethod
    def convert(cls, elem: pf.Element, 
                annotations: Optional[Annotations] = None) -> Optional[NotionInlineElement]:
        """
        Convert a Pandoc element to an appropriate NotionInlineElement.
        
        Args:
            elem: The Pandoc element to convert
            annotations: Optional annotations to apply to the element
            
        Returns:
            A NotionInlineElement instance, or None if no handler was found
        """
        handler = cls._handlers.get(type(elem))
        if handler:
            return handler(elem, annotations)
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


def convert_code_element(elem: pf.Code, annotations: Optional[Annotations] = None) -> CodeElement:
    """
    Convert a Pandoc Code element to a CodeElement.
    
    Args:
        elem: The Pandoc Code element to convert
        annotations: Annotations to apply (code annotation will be forced)
        
    Returns:
        A CodeElement instance
    """
    if annotations is None:
        annotations = Annotations()
    return CodeElement(elem.text, annotations.copy())


def convert_math_element(elem: pf.Math, annotations: Optional[Annotations] = None) -> EquationElement:
    """
    Convert a Pandoc Math element to an EquationElement.
    
    Args:
        elem: The Pandoc Math element to convert
        annotations: Annotations to apply
        
    Returns:
        An EquationElement instance
    """
    if annotations is None:
        annotations = Annotations()
    expression = clean_latex_expression(elem.text)
    return EquationElement(expression, annotations.copy())


def convert_link_element(elem: pf.Link, annotations: Optional[Annotations] = None) -> Text:
    """
    Convert a Pandoc Link element to a Text with link.
    
    Args:
        elem: The Pandoc Link element to convert
        annotations: Optional annotations to apply
        
    Returns:
        A Text instance with link set
    """
    if annotations is None:
        annotations = Annotations()
    # Get the text content from the link's children
    text_content = "".join(str(child.text) for child in elem.content if isinstance(child, pf.Str))
    return Text(text_content, annotations.copy(), link=elem.url)


# Register handlers for standard element types
InlineElementConverter.register(pf.Code, convert_code_element)
InlineElementConverter.register(pf.Math, convert_math_element)
InlineElementConverter.register(pf.Link, convert_link_element)

