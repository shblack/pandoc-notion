from typing import List, Dict, Any

import panflute as pf

from ..models.quote import Quote
from ..models.text import Text
from ..models.paragraph import Paragraph
from ..utils.debug import debug_decorator
from .base import Manager
from .text_manager import TextManager
from .paragraph_manager import ParagraphManager


class QuoteManager(Manager):
    """
    Manager for handling block quote elements and converting them to Notion Quote blocks.
    
    Handles panflute BlockQuote elements, including nested quotes with proper formatting.
    In Notion's structure, a blockquote is represented as:
    - First paragraph → Quote block content
    - Additional paragraphs → Nested child Paragraph blocks
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

        In Notion's structure, a blockquote is represented as:
        - First paragraph → Quote block content
        - Additional paragraphs → Nested child Paragraph blocks

        Args:
            elem: A panflute BlockQuote element

        Returns:
            A list containing a single Quote object,
            potentially with nested child paragraph blocks.
        """
        if not isinstance(elem, pf.BlockQuote):
            raise ValueError(f"Expected BlockQuote element, got {type(elem).__name__}")

        # Create a new quote
        quote = Quote()

        # Process all paragraphs in the quote
        if elem.content:
            # Get all paragraphs
            paragraphs = [p for p in elem.content if isinstance(p, pf.Para) and p.content]

            if not paragraphs:
                # Return empty quote block if no content
                return [quote]

            # First paragraph becomes the Quote block content
            first_para = paragraphs[0]
            texts = TextManager.create_text_elements(first_para.content)
            quote.add_texts(texts)

            # Any additional paragraphs become nested child Paragraph blocks
            for para in paragraphs[1:]:
                paragraph = Paragraph()
                texts = TextManager.create_text_elements(para.content)
                paragraph.add_texts(texts)
                quote.add_child(paragraph)

        # Return the Quote object wrapped in a list
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
            potentially with nested child paragraph blocks.
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
    def create_quote_from_paragraph(cls, paragraph: Paragraph) -> Quote:
        """
        Create a quote from a Paragraph object.
        
        Args:
            paragraph: A Paragraph object to convert to a quote
            
        Returns:
            A Notion Quote object
        """
        quote = Quote()
        quote.add_texts(paragraph.text_content)
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

