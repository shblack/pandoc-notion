from typing import List, Dict, Any

import panflute as pf

from ..models.quote import Quote
from ..models.text import Text
from ..utils.debug import debug_decorator
from .base import Manager
from .registry_mixin import RegistryMixin

class QuoteManager(Manager, RegistryMixin):
    """
    Manager for handling block quote elements and converting them to Notion Quote blocks.
    
    Handles panflute BlockQuote elements, including nested quotes with proper formatting.
    In Notion's structure, a blockquote can contain rich text and nested child blocks.
    """
    
    @classmethod
    @debug_decorator
    def can_convert(cls, elem: pf.Element) -> bool:
        """Check if the element is a block quote that can be converted."""
        return isinstance(elem, pf.BlockQuote)
    
    @classmethod
    @debug_decorator
    def convert(cls, elem: pf.Element) -> List[Quote]:
        """
        Convert a panflute block quote element to a Notion Quote block object.

        In Notion's structure:
        - First paragraph becomes the quote's rich text content
        - All other elements become nested child blocks

        Args:
            elem: A panflute BlockQuote element

        Returns:
            A list containing a single Quote object,
            potentially with nested child blocks.
        """
        if not isinstance(elem, pf.BlockQuote):
            raise ValueError(f"Expected BlockQuote element, got {type(elem).__name__}")

        # Create a new quote
        quote = Quote()

        # Handle empty blockquote
        if not elem.content:
            return [quote]
        
        # Get the first element to use as quote text
        if elem.content:
            first_elem = elem.content[0]
            # Convert the first element using the registry system
            converted_blocks = cls.convert_with_manager(first_elem)
            
            # If we got valid blocks back and the first one has text_content,
            # use it for the quote's text content
            if converted_blocks and hasattr(converted_blocks[0], 'text_content'):
                quote.add_texts(converted_blocks[0].text_content)

        # Process the rest of the elements as children
        for content in elem.content[1:]:
            if isinstance(content, pf.BlockQuote):
                # Special handling for nested blockquotes
                nested_quotes = cls.convert(content)
                for nested_quote in nested_quotes:
                    quote.add_child(nested_quote)
            else:
                # Use the registry to find the appropriate manager
                blocks = cls.convert_with_manager(content)
                
                # Add all converted blocks as children
                for block in blocks:
                    quote.add_child(block)

        return [quote]
    
    @classmethod
    @debug_decorator
    def to_dict(cls, elem: pf.Element) -> List[Dict[str, Any]]:
        """
        Convert a panflute block quote element to a Notion API Quote block.

        Args:
            elem: A panflute BlockQuote element

        Returns:
            A list containing a single dictionary representing the Notion API Quote block,
            potentially with nested child blocks.
        """
        # Convert to Quote objects, then convert each to dictionary
        quotes = cls.convert(elem)
        return [quote.to_dict() for quote in quotes]
    
    @classmethod
    @debug_decorator
    def create_quote(cls, text: str) -> Quote:
        """
        Create a quote from plain text.
        
        Args:
            text: Plain text content for the quote
            
        Returns:
            A Notion Quote object
        """
        quote = Quote()
        quote.add_text(Text(text))
        return quote
    
    @classmethod
    @debug_decorator
    def create_quote_from_block(cls, block) -> Quote:
        """
        Create a quote from any block object that has text_content.
        
        Args:
            block: A block object with text_content attribute
            
        Returns:
            A Notion Quote object
        """
        quote = Quote()
        if hasattr(block, 'text_content'):
            quote.add_texts(block.text_content)
        return quote
    
    @classmethod
    def create_quote_to_dict(cls, text: str) -> Dict[str, Any]:
        """
        Create a quote dictionary from plain text.
        
        Args:
            text: Plain text content for the quote
            
        Returns:
            A dictionary representing the Notion API Quote block
        """
        quote = cls.create_quote(text)
        return quote.to_dict()

