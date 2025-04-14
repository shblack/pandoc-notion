"""Manage conversion of text elements to Notion format."""

from typing import List, Optional, Union, Tuple, Dict, Any
import panflute as pf
from dataclasses import dataclass

@dataclass
class Annotations:
    """Represents Notion text annotations."""
    bold: bool = False
    italic: bool = False
    strikethrough: bool = False
    underline: bool = False
    code: bool = False
    color: str = "default"
    equation: bool = False

    def copy(self) -> 'Annotations':
        """Create a copy of these annotations."""
        return Annotations(
            bold=self.bold,
            italic=self.italic,
            strikethrough=self.strikethrough,
            underline=self.underline,
            code=self.code,
            color=self.color,
            equation=self.equation
        )

    def set_bold(self, value: bool) -> bool:
        """Set bold annotation, return True if changed."""
        changed = self.bold != value
        self.bold = value
        return changed

    def set_italic(self, value: bool) -> bool:
        """Set italic annotation, return True if changed."""
        changed = self.italic != value
        self.italic = value
        return changed
        
    def set_strikethrough(self, value: bool) -> bool:
        """Set strikethrough annotation, return True if changed."""
        changed = self.strikethrough != value
        self.strikethrough = value
        return changed
        
    def set_underline(self, value: bool) -> bool:
        """Set underline annotation, return True if changed."""
        changed = self.underline != value
        self.underline = value
        return changed
        
    def set_code(self, value: bool) -> bool:
        """Set code annotation, return True if changed."""
        changed = self.code != value
        self.code = value
        return changed
        
    def set_equation(self, value: bool) -> bool:
        """Set equation annotation, return True if changed."""
        changed = self.equation != value
        self.equation = value
        return changed

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Notion API format."""
        return {
            "bold": self.bold,
            "italic": self.italic,
            "strikethrough": self.strikethrough,
            "underline": self.underline,
            "code": self.code,
            "color": self.color
        }

from .text_manager_inline import (
    NotionInlineElement, 
    Text,
    InlineElementConverter,
    merge_consecutive_texts
)
from ..utils.debug import debug_decorator
from .base import Manager


class TextManager(Manager):
    """
    Manager for handling inline text elements and converting them to Notion inline elements.
    
    This implementation uses the NotionInlineElement abstraction to handle various inline 
    element types (text, inline equations, code, mentions) with a unified approach.
    """
    
    @classmethod
    @debug_decorator
    def can_convert(cls, elem: pf.Element) -> bool:
        """Check if this manager can convert the element."""
        return isinstance(elem, (pf.Str, pf.Space, pf.SoftBreak, pf.LineBreak, 
                               pf.Strong, pf.Emph, pf.Math))

    @classmethod
    @debug_decorator
    def convert(cls, elements: List[pf.Element]) -> List[NotionInlineElement]:
        """Convert a list of panflute elements to Notion inline elements."""
        return cls.create_text_elements(elements)

    @classmethod
    def create_text_elements(cls, elements: List[pf.Element], 
                           base_annotations: Optional[Annotations] = None) -> List[NotionInlineElement]:
        """Create Notion text elements from a list of panflute elements."""
        current_annotations = base_annotations.copy() if base_annotations else Annotations()
        result_elements = []
        current_text = ""
        
        cls._process_stream(elements, current_annotations, result_elements, current_text)
        return result_elements

    @classmethod
    def _process_stream(cls, elements: List[pf.Element], 
                       current_annotations: Annotations,
                       result_elements: List[NotionInlineElement],
                       current_text: str = "") -> None:
        """Process a stream of elements, accumulating text with the same formatting."""
        for elem in elements:
            if not cls.can_convert(elem):
                if current_text:
                    result_elements.append(Text(current_text, annotations=current_annotations.copy()))
                    current_text = ""
                continue

            # Try registered converters first
            element = InlineElementConverter.convert(elem, current_annotations.copy())
            if element:
                if current_text:
                    result_elements.append(Text(current_text, annotations=current_annotations.copy()))
                    current_text = ""
                result_elements.append(element)
                continue

            # Handle formatting elements
            if isinstance(elem, (pf.Strong, pf.Emph)):
                new_annotations = current_annotations.copy()
                if isinstance(elem, pf.Strong):
                    new_annotations.set_bold(True)
                else:  # Emph
                    new_annotations.set_italic(True)

                if current_text:
                    result_elements.append(Text(current_text, annotations=current_annotations.copy()))
                    current_text = ""

                cls._process_stream(elem.content, new_annotations, result_elements)
                continue

            # Handle basic text elements
            if isinstance(elem, pf.Str):
                current_text += elem.text
            elif isinstance(elem, pf.Space):
                current_text += " "
            elif isinstance(elem, (pf.SoftBreak, pf.LineBreak)):
                current_text += "\n"

        # Flush any remaining text
        if current_text:
            result_elements.append(Text(current_text, annotations=current_annotations.copy()))

    @classmethod
    @debug_decorator
    def to_dict(cls, elements: List[pf.Element]) -> List[Dict[str, Any]]:
        """Convert elements to Notion API format."""
        inline_elements = cls.convert(elements)
        return [element.to_dict() for element in inline_elements]

