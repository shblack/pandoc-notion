from typing import List, Dict, Any, Optional, Callable, Type
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import panflute as pf


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


class Annotations:
    """
    Represents text annotations in Notion.
    
    Properties correspond to Notion's API text annotations:
    https://developers.notion.com/reference/rich-text
    State-changing methods (set_*) return True if the state changed, False otherwise.
    """
    def __init__(self, bold=False, italic=False, strikethrough=False, 
                 underline=False, code=False, color="default"):
        self._bold = bold
        self._italic = italic
        self._strikethrough = strikethrough
        self._underline = underline
        self._code = code
        self._color = color
    
    @property
    def bold(self) -> bool:
        return self._bold
        
    def set_bold(self, value: bool) -> bool:
        """Set bold state and return whether it changed."""
        changed = self._bold != value
        self._bold = value
        return changed
        
    @property
    def italic(self) -> bool:
        return self._italic
        
    def set_italic(self, value: bool) -> bool:
        """Set italic state and return whether it changed."""
        changed = self._italic != value
        self._italic = value
        return changed
        
    @property
    def strikethrough(self) -> bool:
        return self._strikethrough
        
    def set_strikethrough(self, value: bool) -> bool:
        """Set strikethrough state and return whether it changed."""
        changed = self._strikethrough != value
        self._strikethrough = value
        return changed
        
    @property
    def underline(self) -> bool:
        return self._underline
        
    def set_underline(self, value: bool) -> bool:
        """Set underline state and return whether it changed."""
        changed = self._underline != value
        self._underline = value
        return changed
        
    @property
    def code(self) -> bool:
        return self._code
        
    def set_code(self, value: bool) -> bool:
        """Set code state and return whether it changed."""
        changed = self._code != value
        self._code = value
        return changed
        
    @property
    def color(self) -> str:
        return self._color
        
    def set_color(self, value: str) -> bool:
        """Set color and return whether it changed."""
        changed = self._color != value
        self._color = value
        return changed
    
    def copy(self) -> 'Annotations':
        """Create a deep copy of annotations."""
        return Annotations(
            bold=self.bold,
            italic=self.italic,
            strikethrough=self.strikethrough,
            underline=self.underline,
            code=self.code,
            color=self.color
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert annotations to a dictionary representation for Notion API."""
        return {
            "bold": self.bold,
            "italic": self.italic,
            "strikethrough": self.strikethrough,
            "underline": self.underline,
            "code": self.code,
            "color": self.color
        }
    
    def is_default(self) -> bool:
        """Check if all annotations are set to their default values."""
        return (
            not self.bold and 
            not self.italic and 
            not self.strikethrough and 
            not self.underline and 
            not self.code and 
            self.color == "default"
        )


@dataclass
class Text(NotionInlineElement):
    """
    Represents a rich text object in Notion.
    
    A Text object contains content and optional annotations and links.
    Multiple Text objects can be combined to form rich text with 
    different formatting in different parts.
    """
    content: str
    annotations: Annotations = field(default_factory=Annotations)
    link: Optional[str] = None
    
    def get_content(self) -> str:
        """Get the text content of this element."""
        return self.content
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Text to a dictionary representation for Notion API."""
        result = {
            "type": "text",
            "text": {
                "content": self.content,
                "link": {"url": self.link} if self.link else None
            },
            "annotations": self.annotations.to_dict(),
            "plain_text": self.content
        }
        
        return result
    
    def __str__(self) -> str:
        """String representation of the text for debugging."""
        annotations_str = ""
        if not self.annotations.is_default():
            annotations_str = f" with {self.annotations}"
        link_str = f", link={self.link}" if self.link else ""
        return f"Text('{self.content}'{annotations_str}{link_str})"


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
    return EquationElement(elem.text, annotations.copy())


# Register handlers for standard element types
InlineElementConverter.register(pf.Code, convert_code_element)
InlineElementConverter.register(pf.Math, convert_math_element)


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


# Register the link handler
InlineElementConverter.register(pf.Link, convert_link_element)

def merge_consecutive_texts(texts: List[NotionInlineElement]) -> List[NotionInlineElement]:
    """
    Merge consecutive Text objects with identical annotations and link status.
    
    This function only merges adjacent Text instances, leaving other types of
    inline elements unchanged.
    
    Args:
        texts: A list of NotionInlineElement objects
        
    Returns:
        A new list with consecutive similar Text objects merged
    """
    if not texts:
        return []
    
    result = [texts[0]]
    
    for current in texts[1:]:
        previous = result[-1]
        
        # Only merge Text objects (not other inline elements)
        if isinstance(previous, Text) and isinstance(current, Text):
            # Check if annotations match
            annotations_match = (
                previous.annotations.bold == current.annotations.bold and
                previous.annotations.italic == current.annotations.italic and
                previous.annotations.strikethrough == current.annotations.strikethrough and
                previous.annotations.underline == current.annotations.underline and
                previous.annotations.code == current.annotations.code and
                previous.annotations.color == current.annotations.color
            )
            link_match = previous.link == current.link
            if annotations_match and link_match:
                # Merge the texts by combining their content
                previous.content += current.content
                continue
        
        # Add as a new segment (either not Text or not matching)
        result.append(current)
    
    return result

