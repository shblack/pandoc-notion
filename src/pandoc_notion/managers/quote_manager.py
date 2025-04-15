"""
Manager for handling blockquote elements in conversion between Pandoc and Notion formats.

QuoteManager is responsible for converting Pandoc block quotes to Notion quote blocks,
handling rich text formatting and nested content correctly.
"""

from typing import List as PyList, Dict, Any

import panflute as pf

from pandoc_notion.models.quote import Quote
from pandoc_notion.models.text import Text
from pandoc_notion.models.list import List as NotionList
from pandoc_notion.managers.base import Manager
from pandoc_notion.managers.registry_mixin import RegistryMixin
from pandoc_notion.managers.text_manager import TextManager

# Import debug_trace for detailed diagnostics
from python_debug import debug_trace


class QuoteManager(Manager, RegistryMixin):
    """
    Manager for handling block quote elements and converting them to Notion Quote blocks.
    
    Handles panflute BlockQuote elements, including nested quotes with proper formatting.
    In Notion's structure, a blockquote can contain rich text and nested child blocks.
    """
    
    @classmethod
    def can_convert(cls, elem: pf.Element) -> bool:
        """Check if the element is a block quote that can be converted."""
        return isinstance(elem, pf.BlockQuote)
    
    @classmethod
    @debug_trace()
    def convert(cls, elem: pf.Element) -> PyList[Quote]:
        """
        Convert a panflute block quote element to a Notion Quote block object.

        In Notion's structure:
        - First element's text becomes the quote's rich text content
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
        
        # Process the first element to use as quote text
        if elem.content:
            first_elem = elem.content[0]
            print(f"First element type: {type(first_elem).__name__}") # Debug print
            cls._process_first_element(first_elem, quote)

        # Process the rest of the elements as children
        for content in elem.content[1:]:
            cls._process_child_element(content, quote)

        # Check if the quote has any text content; add empty text if needed
        if not quote.text_content:
            print("WARNING: Quote has no text content after processing, adding empty text.") # Debug print
            quote.add_text(Text(""))

        return [quote]
    
    @classmethod
    @debug_trace()
    def _process_first_element(cls, elem: pf.Element, quote: Quote) -> None:
        """
        Process the first element of a blockquote to extract its text content.
        
        Args:
            elem: The first element in the blockquote
            quote: The Notion Quote object to update
        """
        print(f"Processing first element type: {type(elem).__name__}") # Debug print
        
        # Check if the element has inline content (like Para, Header, Plain)
        if hasattr(elem, 'content') and isinstance(elem.content, list):
            print(f"Element content: {elem.content}") # Debug print
            # Use TextManager to extract rich text with formatting preserved
            text_elements = TextManager.create_text_elements(elem.content)
            print(f"Extracted text elements: {text_elements}") # Debug print
            if text_elements:
                quote.add_texts(text_elements)
                return # Text successfully extracted and added
                
        # If text couldn't be extracted directly, or element has no content list
        print(f"Converting element using registry: {type(elem).__name__}") # Debug print
        converted = cls.convert_with_manager(elem)
        print(f"Converted result type: {type(converted)}") # Debug print
        
        # Try to use the converted result's text content if available (e.g., if it was a Para)
        # Note: convert_with_manager returns a list, so check the first item
        if converted and isinstance(converted, list) and len(converted) > 0 and hasattr(converted[0], 'text_content'):
            print("Using text_content from first converted block.") # Debug print
            quote.add_texts(converted[0].text_content)
        else:
            # Add the converted element(s) as child(ren) if text extraction failed
            print("Adding converted element(s) as children instead.") # Debug print
            cls._add_converted_blocks_as_children(quote, converted)
    
    @classmethod
    @debug_trace()
    def _process_child_element(cls, elem: pf.Element, quote: Quote) -> None:
        """
        Process a subsequent element of a blockquote, adding it as a child block.
        
        Args:
            elem: A child element in the blockquote
            quote: The Notion Quote object to update
        """
        print(f"Processing child element type: {type(elem).__name__}") # Debug print
        
        if isinstance(elem, pf.BlockQuote):
            # Special handling for nested blockquotes - recursively convert
            nested_quotes = cls.convert(elem) # Returns a list of Quote objects
            for nested_quote in nested_quotes:
                quote.add_child(nested_quote)
        else:
            # Use the registry to find the appropriate manager and convert
            converted = cls.convert_with_manager(elem) # Returns a list or sometimes a single object
            print(f"Converted child element result type: {type(converted)}") # Debug print
            cls._add_converted_blocks_as_children(quote, converted)
    
    @classmethod
    @debug_trace()
    def _add_converted_blocks_as_children(cls, quote: Quote, blocks) -> None:
        """
        Add converted blocks as children to a quote. Handles various return types.
        
        Args:
            quote: The Notion Quote object to add children to
            blocks: The converted blocks (can be None, single object, list, NotionList).
        """
        print(f"Adding blocks as children, input type: {type(blocks)}") # Debug print
        
        if not blocks:
            print("No blocks to add (None or empty list)")
            return
            
        # Handle NotionList objects (model class, not directly iterable)
        if isinstance(blocks, NotionList):
            print("Adding NotionList as direct child")
            quote.add_child(blocks)
        # Handle single non-list blocks (e.g., if a manager returns a single Block)
        # Check against list explicitly, as convert_with_manager usually returns a list
        elif not isinstance(blocks, list): 
             print(f"Adding single block of type: {type(blocks).__name__}")
             quote.add_child(blocks)
        # Handle list of blocks (typical case from convert_with_manager)
        elif isinstance(blocks, list):
            print(f"Adding {len(blocks)} blocks from list")
            for block in blocks:
                # A manager might still return a NotionList inside the Python list
                if isinstance(block, NotionList): 
                    print("Adding NotionList found inside list as direct child")
                    quote.add_child(block)
                else:
                    quote.add_child(block)
        else:
             print(f"Warning: Unexpected type for blocks: {type(blocks)}")

    @classmethod
    def to_dict(cls, elem: pf.Element) -> PyList[Dict[str, Any]]:
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

