#!/usr/bin/env python3
"""
Pandoc filter for converting between Markdown and Notion formats.

This module provides:
1. A programmatic interface for converting Markdown to Notion format
2. A filter that can be used directly with pandoc
3. Utility methods for handling markdown -> AST -> notion conversion
4. Support for both string and document handling

Usage as a pandoc filter:
    pandoc input.md --filter pandoc-notion -o output.json

Usage as a Python module:
    from pandoc_notion.filter import convert_markdown_to_notion
    notion_blocks = convert_markdown_to_notion("# Hello world")
"""

import json
import sys
from typing import Dict, List, Any, Optional, Union

import panflute as pf
import pypandoc

from pandoc_notion.registry import ManagerRegistry
from pandoc_notion.models.base import Block


class Filter:
    """
    Main filter class for converting between Markdown and Notion.
    
    This class serves as both a programmatic interface and a pandoc filter.
    """
    
    def __init__(self, registry: Optional[ManagerRegistry] = None):
        """
        Initialize the filter with an optional manager registry.
        
        Args:
            registry: A ManagerRegistry instance, or None to use the default
        """
        self.registry = registry or ManagerRegistry()
    
    def apply(self, elem: pf.Element, doc: Optional[pf.Doc] = None) -> Optional[pf.Element]:
        """
        Apply the filter to a panflute element.
        
        This method is used when running as a pandoc filter.
        
        Args:
            elem: The panflute element to convert
            doc: The parent document
            
        Returns:
            The converted element, or None to keep the original
        """
        # This method is intentionally minimal in a filter - we're not 
        # transforming the document in place, but rather converting to Notion format
        # When run as a filter, the main action happens in the action() method
        return None
    
    def to_notion_blocks(self, doc: pf.Doc) -> List[Block]:
        """
        Convert a panflute Doc to Notion blocks.
        
        Args:
            doc: A panflute document
            
        Returns:
            A list of Notion Block objects
        """
        results = []
        
        for elem in doc.content:
            try:
                notion_blocks = self.registry.convert_element(elem)
                if notion_blocks:
                    if isinstance(notion_blocks, list):
                        results.extend(notion_blocks)
                    else:
                        results.append(notion_blocks)
            except Exception as e:
                import logging
                logging.error(f"Error converting element {type(elem).__name__}: {str(e)}")
        
        return results
    
    def to_notion_dict(self, doc: pf.Doc) -> Dict[str, Any]:
        """
        Convert a panflute Doc to a Notion API-compatible dictionary.
        
        Args:
            doc: A panflute document
            
        Returns:
            A dictionary in Notion API format with blocks
        """
        blocks = []
        
        for elem in doc.content:
            manager = self.registry.find_manager(elem)
            if manager:
                try:
                    notion_blocks = manager.to_dict(elem)
                    if isinstance(notion_blocks, list):
                        blocks.extend(notion_blocks)
                    else:
                        blocks.append(notion_blocks)
                except Exception as e:
                    import logging
                    logging.error(f"Error converting element to dict {type(elem).__name__}: {str(e)}")
        
        return {"children": blocks}
    
    def action(self) -> None:
        """
        Run the filter on a document from stdin and output the result to stdout.
        
        This method is used when running as a pandoc filter from the command line.
        """
        doc = pf.load()
        notion_dict = self.to_notion_dict(doc)
        json.dump(notion_dict, sys.stdout, indent=2)
    
    def convert_string(self, text: str, format: str = "markdown") -> Dict[str, Any]:
        """
        Convert a string of text to Notion format.
        
        Args:
            text: The text to convert
            format: The format of the input text (default: markdown)
            
        Returns:
            A dictionary in Notion API format with blocks
        """
        # Use panflute to convert the string to a Doc
        doc = self._string_to_doc(text, format)
        
        # Convert the Doc to Notion format
        return self.to_notion_dict(doc)
    
    def _string_to_doc(self, text: str, format: str = "markdown") -> pf.Doc:
        """
        Convert a string to a panflute Doc.
        
        Args:
            text: The text to convert
            format: The format of the input text
            
        Returns:
            A panflute Doc object
        """
        # Use pypandoc to convert the string to JSON AST
        ast_json = pypandoc.convert_text(text, 'json', format=format)
        
        # Parse the JSON AST into a panflute Doc
        return pf.load(json.loads(ast_json))


def convert_markdown_to_notion(markdown: str) -> Dict[str, Any]:
    """
    Utility function to convert markdown text to Notion blocks.
    
    Args:
        markdown: Markdown text to convert
        
    Returns:
        A dictionary in Notion API format with blocks
    """
    filter = Filter()
    return filter.convert_string(markdown)


def markdown_to_notion_blocks(markdown: str) -> List[Block]:
    """
    Utility function to convert markdown text to Notion Block objects.
    
    Args:
        markdown: Markdown text to convert
        
    Returns:
        A list of Notion Block objects
    """
    filter = Filter()
    doc = filter._string_to_doc(markdown)
    return filter.to_notion_blocks(doc)


def main():
    """Entry point for running as a pandoc filter."""
    Filter().action()


if __name__ == "__main__":
    main()

