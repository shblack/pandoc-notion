from typing import List, Dict, Any

import panflute as pf

from pandoc_notion.models.paragraph import Paragraph
from pandoc_notion.models.text import Text
from pandoc_notion.managers.base import Manager
from pandoc_notion.managers.text_manager import TextManager
from pandoc_notion.managers.registry_mixin import RegistryMixin

# Import debug_trace for detailed diagnostics
from python_debug import debug_trace


class ParagraphManager(Manager, RegistryMixin):
    """
    Manager for handling paragraph elements and converting them to Notion Paragraph blocks.
    
    Paragraphs are one of the most common block types in documents.
    """
    
    @classmethod
    # Removed @debug_decorator
    def can_convert(cls, elem: pf.Element) -> bool:
        """Check if the element is a paragraph that can be converted."""
        return isinstance(elem, pf.Para)
    
    @classmethod
    # Removed @debug_decorator
    @debug_trace()
    def convert(cls, elem: pf.Element) -> List[Paragraph]:
        """
        Convert a panflute paragraph element to a Notion Paragraph block object.
        
        Args:
            elem: A panflute Para element
            
        Returns:
            A list containing a single Paragraph block object
        """
        if not isinstance(elem, pf.Para):
            raise ValueError(f"Expected Para element, got {type(elem).__name__}")
        
        # Create a new paragraph
        paragraph = Paragraph()
        
        # Convert all inline elements together using TextManager directly
        # This ensures all elements are processed as a batch
        text_elements = TextManager.create_text_elements(list(elem.content))
        for text_element in text_elements:
            paragraph.add_text(text_element)
        return [paragraph]
    
    @classmethod
    # Removed @debug_decorator
    @debug_trace()
    def to_dict(cls, elem: pf.Element) -> List[Dict[str, Any]]:
        """
        Convert a panflute paragraph element to a Notion API paragraph block.
        
        Args:
            elem: A panflute Para element
            
        Returns:
            A list containing a single paragraph block dictionary in Notion API format
        """
        # Convert to Paragraph objects, then convert each to dictionary
        paragraphs = cls.convert(elem)
        return [paragraph.to_dict() for paragraph in paragraphs]
    
    @classmethod
    def convert_plain_text(cls, text: str) -> List[Paragraph]:
        """
        Create a paragraph from plain text.
        
        Args:
            text: Plain text content
            
        Returns:
            A list containing a single Paragraph block object
        """
        paragraph = Paragraph()
        paragraph.add_text(Text(text))
        return [paragraph]
    
    @classmethod
    # Removed @debug_decorator
    def convert_plain_text_to_dict(cls, text: str) -> List[Dict[str, Any]]:
        """
        Create a paragraph dictionary from plain text.
        
        Args:
            text: Plain text content
            
        Returns:
            A list containing a single paragraph block dictionary in Notion API format
        """
        paragraphs = cls.convert_plain_text(text)
        return [paragraph.to_dict() for paragraph in paragraphs]

