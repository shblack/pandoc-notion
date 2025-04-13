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
    def convert(cls, elem: pf.Element) -> Heading:
        """
        Convert a panflute header element to a Notion Heading object.
        
        Args:
            elem: A panflute Header element
            
        Returns:
            A Notion Heading object
        """
        if not isinstance(elem, pf.Header):
            raise ValueError(f"Expected Header element, got {type(elem).__name__}")
        
        # Get the heading level (Notion supports h1, h2, h3)
        # Any deeper levels will be mapped to h3
        level = elem.level
        
        # Create a new heading
        heading = Heading(level)
        
        # Use TextManager to convert all inline elements in the heading
        texts = TextManager.convert_all(elem.content)
        heading.add_texts(texts)
        
        return heading
    
    @classmethod
    def convert_plain_text(cls, text: str, level: int = 1) -> Heading:
        """
        Create a heading from plain text.
        
        Args:
            text: Plain text content
            level: Heading level (1, 2, or 3)
            
        Returns:
            A Notion Heading object
        """
        from ..models.text import Text
        
        heading = Heading(level)
        heading.add_text(Text(text))
        return heading

