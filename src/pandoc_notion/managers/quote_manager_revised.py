from typing import List, Dict, Any

import panflute as pf

from ..registry import find_manager
from .base import Manager
from .text_manager import TextManager
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
    def convert(cls, elem: pf.Element) -> List[Dict[str, Any]]:
        """
        Convert a panflute block quote element to a Notion Quote block.
        
        In Notion's structure, a blockquote is represented as:
        - First paragraph -> Quote block content
        - Additional paragraphs/elements -> Nested child blocks
        
        Args:
            elem: A panflute BlockQuote element
            
        Returns:
            A list containing a Notion API-compatible dictionary for the quote block
        """
        if not isinstance(elem, pf.BlockQuote):
            raise ValueError(f"Expected BlockQuote element, got {type(elem).__name__}")
        
        # Basic quote block structure
        quote_block = {
            "object": "block",
            "type": "quote",
            "quote": {
                "rich_text": [],
                "color": "default"
            }
        }
        
        # If no content, return empty quote block
        if not elem.content:
            return [quote_block]
        
        # Find the first paragraph to use as the quote's main content
        first_text_content = None
        children = []
        
        for item in elem.content:
            # For the first paragraph, extract text for the quote's main content
            if first_text_content is None and isinstance(item, pf.Para) and item.content:
                # Convert paragraph content to rich text for the quote's main content
                texts = TextManager.convert_all(item.content)
                first_text_content = [
                    {
                        "type": "text",
                        "text": {"content": text.content},
                        "annotations": {
                            "bold": text.annotations.bold,
                            "italic": text.annotations.italic,
                            "strikethrough": text.annotations.strikethrough,
                            "underline": text.annotations.underline,
                            "code": text.annotations.code,
                            "color": text.annotations.color or "default"
                        },
                        "plain_text": text.content
                    }
                    for text in texts
                ]
            # For subsequent elements, convert to Notion blocks for children
            elif first_text_content is not None:
                # Find appropriate manager for this element
                manager = find_manager(item)
                if manager:
                    # Convert to Notion API blocks
                    child_blocks = manager.convert(item)
                    children.extend(child_blocks)
        
        # If we found no paragraph, try to use any valid content
        if first_text_content is None and elem.content:
            # Use first element of any type
            first_elem = elem.content[0]
            manager = find_manager(first_elem)
            if manager:
                blocks = manager.convert(first_elem)
                if blocks and len(blocks) > 0:
                    # Extract text content from first block if possible
                    block = blocks[0]
                    block_type = block.get("type")
                    if block_type and block_type in block:
                        rich_text = block[block_type].get("rich_text", [])
                        if rich_text:
                            first_text_content = rich_text
                        
                    # Add remaining blocks as children
                    if len(blocks) > 1:
                        children.extend(blocks[1:])
        
        # Set the rich_text content if we found any
        if first_text_content:
            quote_block["quote"]["rich_text"] = first_text_content
        
        # Add children if we have any
        if children:
            quote_block["quote"]["children"] = children
            quote_block["has_children"] = True
        
        return [quote_block]
    
    @classmethod
    @debug_decorator(filename="quote_manager.py", funcname="create_quote")
    def create_quote(cls, text: str) -> List[Dict[str, Any]]:
        """
        Create a quote from plain text.
        
        Args:
            text: Plain text content for the quote
            
        Returns:
            A list containing a Notion API-compatible dictionary for the quote block
        """
        # Create a simple quote block with plain text
        return [{
            "object": "block",
            "type": "quote",
            "quote": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": text},
                        "annotations": {
                            "bold": False,
                            "italic": False,
                            "strikethrough": False,
                            "underline": False,
                            "code": False,
                            "color": "default"
                        },
                        "plain_text": text
                    }
                ],
                "color": "default"
            }
        }]
    
    @classmethod
    @debug_decorator(filename="quote_manager.py", funcname="create_quote_from_text_blocks")
    def create_quote_from_text_blocks(cls, rich_text_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create a quote from rich text blocks.
        
        Args:
            rich_text_blocks: List of Notion API rich text blocks
            
        Returns:
            A list containing a Notion API-compatible dictionary for the quote block
        """
        return [{
            "object": "block",
            "type": "quote",
            "quote": {
                "rich_text": rich_text_blocks,
                "color": "default"
            }
        }]

