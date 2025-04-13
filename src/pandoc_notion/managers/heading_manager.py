from typing import Any

import panflute as pf

from ..models.heading import Heading
from .base import Manager
from .text_manager import TextManager


class HeadingManager(Manager):
    """
    Manager for handling heading elements and converting them to Notion Heading blocks.
    
    Handles panflute Header elements and maps them to Notion's heading format,
    respecting that Notion only supports h1, h2, and h3.
    """
    
    @classmethod
    def can_convert(cls, elem: pf.Element) -> bool:
        """Check if the element is a header that can be converted."""
        return isinstance(elem, pf.Header)
    
    @classmethod
    def convert(cls, elem: pf.Element) -> list[dict[str, Any]]:
        """
        Convert a panflute header element to a Notion API heading block.
        
        Args:
            elem: A panflute Header element
            
        Returns:
            A list containing a single heading block dictionary in Notion API format
        """
        if not isinstance(elem, pf.Header):
            raise ValueError(f"Expected Header element, got {type(elem).__name__}")
        
        # Get the heading level (Notion supports h1, h2, h3)
        # Any deeper levels will be mapped to h3
        level = elem.level
        
        # Create a new heading
        heading = Heading(level)
        
        # Use TextManager to convert all inline elements in the heading
        texts = TextManager.create_text_elements(elem.content)
        heading.add_texts(texts)
        
        # Convert to Notion API format and return as a single-item list
        return [heading.to_dict()]
    
    @classmethod
    def convert_plain_text(cls, text: str, level: int = 1) -> list[dict[str, Any]]:
        """
        Create a heading from plain text.
        
        Args:
            text: Plain text content
            level: Heading level (1, 2, or 3)
            
        Returns:
            A list containing a single heading block dictionary in Notion API format
        """
        from ..models.text import Text
        
        heading = Heading(level)
        heading.add_text(Text(text))
        return [heading.to_dict()]
