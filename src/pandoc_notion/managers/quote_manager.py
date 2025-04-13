from typing import List

import panflute as pf

from ..models.quote import Quote
from ..models.text import Text
from ..models.paragraph import Paragraph
from .base import Manager
from .text_manager import TextManager
from .paragraph_manager import ParagraphManager
from ..utils.debug import debug_decorator


class QuoteManager(Manager):
    """
    Manager for handling block quote elements and converting them to Notion Quote blocks.
    
    Handles panflute BlockQuote elements, including nested quotes with proper formatting.
    """
    
    @classmethod
    @debug_decorator(filename="quote_manager.py", funcname="can_convert")
    def can_convert(cls, elem: pf.Element) -> bool:
        """Check if the element is a block quote that can be converted."""
        return isinstance(elem, pf.BlockQuote)
    @classmethod
    @debug_decorator(filename="quote_manager.py", funcname="convert")
    def convert(cls, elem: pf.Element) -> Quote:
        """
        Convert a panflute block quote element to a Notion Quote block.
        
        In Notion's structure, a blockquote is represented as:
        - First paragraph -> Quote block content
        - Additional paragraphs -> Nested child Paragraph blocks
        
        Args:
            elem: A panflute BlockQuote element
            
        Returns:
            A Quote object with nested child paragraphs if any
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
                return quote
            
            # First paragraph becomes the Quote block content
            first_para = paragraphs[0]
            texts = TextManager.convert_all(first_para.content)
            quote.add_texts(texts)
            
            # Any additional paragraphs become nested child Paragraph blocks
            for para in paragraphs[1:]:
                paragraph = Paragraph()
                texts = TextManager.convert_all(para.content)
                paragraph.add_texts(texts)
                quote.add_child(paragraph)
        
        return quote
    @classmethod
    @debug_decorator(filename="quote_manager.py", funcname="create_quote")
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
    @debug_decorator(filename="quote_manager.py", funcname="create_quote_from_paragraph")
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
