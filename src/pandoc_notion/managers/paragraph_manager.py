from typing import List, Dict, Any

import panflute as pf

from ..models.paragraph import Paragraph
from ..models.text import Text
from ..utils.debug import debug_decorator
from .base import Manager
from .text_manager import TextManager
from .registry_mixin import RegistryMixin


class ParagraphManager(Manager, RegistryMixin):
    """
    Manager for handling paragraph elements and converting them to Notion Paragraph blocks.
    
    Paragraphs are one of the most common block types in documents.
    """
    
    @classmethod
    @debug_decorator
    def can_convert(cls, elem: pf.Element) -> bool:
        """Check if the element is a paragraph that can be converted."""
        return isinstance(elem, pf.Para)
    
    @classmethod
    @debug_decorator
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
        
        # Process each element in the paragraph using the registry system
        
        # Direct use of TextManager for the entire paragraph content
        # This is more reliable for handling inline formatting
        text_elements = TextManager.create_text_elements(elem.content)
        
        # Add all text elements to the paragraph
        if text_elements:
            paragraph.add_texts(text_elements)
        else:
            
            # Fallback: Process each element individually
            for inline_elem in elem.content:
                
                # Handle basic text elements directly
                if isinstance(inline_elem, (pf.Str, pf.Space)):
                    text = inline_elem.text if isinstance(inline_elem, pf.Str) else " "
                    paragraph.add_text(Text(text))
                
                # For other elements, try the registry
                elif cls.has_manager_for(inline_elem):
                    # Convert using the appropriate manager
                    inline_blocks = cls.convert_with_manager(inline_elem)
                    
                    # Add the converted elements to the paragraph
                    for block in inline_blocks:
                        if hasattr(block, 'to_text_element'):
                            paragraph.add_text(block.to_text_element())
                        elif hasattr(block, 'text_content'):
                            paragraph.add_texts(block.text_content)
                        else:
                            # Try to add directly if it's a Text-like object
                            paragraph.add_text_element(block)
                else:
                    # Last resort: try TextManager for this single element
                    fallback_elements = TextManager.create_text_elements([inline_elem])
                    if fallback_elements:
                        paragraph.add_texts(fallback_elements)
        
        # Return as a single-item list
        return [paragraph]
    
    @classmethod
    @debug_decorator
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
    @debug_decorator
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

