#!/usr/bin/env python3
"""
Filter for converting markdown to Notion blocks.

This module provides:
1. A programmatic interface to convert markdown to Notion blocks
2. Support for direct use with pandoc as a filter
3. Utilities for markdown -> AST -> Notion conversion
4. Comprehensive debug output when enabled
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional, Union

import panflute as pf
import pypandoc
from pandoc_notion.debug.debug_trace import debug_trace

from pandoc_notion.registry import ManagerRegistry


# Configure module logger
logger = logging.getLogger('pandoc_notion.filter')


class Filter:
    """
    Filter class for converting markdown/pandoc to Notion format.
    
    This class handles the conversion process:
    markdown -> pandoc AST -> panflute Doc -> Notion blocks
    """
    
    def __init__(self):
        """Initialize the filter."""
        logger.debug("Initializing Filter")
        self.registry = ManagerRegistry()  # Initialize with default managers
    
    @debug_trace()
    def convert_string(self, text: str, format: str = "markdown") -> Dict[str, Any]:
        """
        Convert a string to Notion blocks.
        
        Args:
            text: The text to convert
            format: The format of the input text
            
        Returns:
            Dictionary containing Notion blocks
        """
        logger.debug(f"Converting string (format: {format})")
        doc = self._string_to_doc(text, format)
        return self.to_notion_dict(doc)

    @debug_trace()
    def _string_to_doc(self, text: str, format: str = "markdown") -> pf.Doc:
        """
        Convert a string to a panflute Doc.
        
        Args:
            text: The text to convert
            format: The format of the input text
            
        Returns:
            A panflute Doc object
        """
        logger.debug(f"Converting string to Doc (format: {format})")
        try:
            # Convert to pandoc JSON AST
            ast_json = pypandoc.convert_text(text, 'json', format=format)
            logger.debug("Successfully converted to JSON AST")
            
            # Parse the JSON AST
            ast_dict = json.loads(ast_json)
            logger.debug("Parsed JSON AST to dictionary")
            
            # Extract elements and metadata from the AST
            if 'blocks' in ast_dict:
                # Create Doc object from the blocks
                blocks = ast_dict.get('blocks', [])
                metadata = ast_dict.get('meta', {})
                
                # Convert JSON blocks to panflute elements
                elements = pf.convert_text(ast_json, input_format='json', output_format='panflute')
                
                if isinstance(elements, list):
                    # Create a new Doc with the elements
                    doc = pf.Doc(*elements)
                    logger.debug(f"Created Doc with {len(doc.content)} elements")
                    return doc
                elif isinstance(elements, pf.Doc):
                    # If we got a Doc directly, return it
                    logger.debug(f"Received Doc with {len(elements.content)} elements")
                    return elements
                else:
                    raise TypeError(f"Unexpected result type: {type(elements)}")
            else:
                raise ValueError("Invalid JSON AST structure: missing 'blocks' key")
            
        except Exception as e:
            logger.error(f"Error converting string to Doc: {str(e)}")
            logger.debug("Error details:", exc_info=True)
            raise
    
    @debug_trace()
    def to_notion_dict(self, doc: pf.Doc) -> Dict[str, Any]:
        """
        Convert a panflute Doc to a Notion blocks dictionary.
        
        Args:
            doc: The panflute Doc to convert
            
        Returns:
            Dictionary containing Notion blocks
        """
        logger.debug("Converting Doc to Notion dict")
        blocks = self.to_notion_blocks(doc)
        logger.debug(f"Generated {len(blocks)} blocks")
        return {"children": blocks}
    
    @debug_trace()
    def to_notion_blocks(self, doc: pf.Doc) -> List[Dict[str, Any]]:
        """
        Convert a panflute Doc to a list of Notion blocks.
        
        Args:
            doc: The panflute Doc to convert
            
        Returns:
            List of Notion block dictionaries
        """
        logger.debug("Converting Doc to Notion blocks")
        blocks = self.registry.convert_elements_to_dicts(list(doc.content))
        logger.debug(f"Successfully converted {len(blocks)} blocks")
        return blocks


@debug_trace()
def convert_markdown_to_notion(markdown: str) -> Dict[str, Any]:
    """
    Convert markdown text to Notion blocks.
    
    Args:
        markdown: Markdown text to convert
        
    Returns:
        Dictionary containing Notion blocks
    """
    logger.debug("Converting markdown to Notion blocks")
    filter = Filter()
    return filter.convert_string(markdown)


@debug_trace()
def filter_markdown_to_notion(markdown: str) -> Dict[str, Any]:
    """
    Convert markdown to Notion blocks (alias for convert_markdown_to_notion).
    
    This function exists for backwards compatibility.
    
    Args:
        markdown: Markdown text to convert
        
    Returns:
        Dictionary containing Notion blocks
    """
    return convert_markdown_to_notion(markdown)


def main():
    """Command-line entry point."""
    import argparse
    
    # Configure logging
    logging_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=logging_format)
    
    parser = argparse.ArgumentParser(description='Convert markdown to Notion blocks')
    parser.add_argument('input', nargs='?', help='Input markdown file (omit for stdin)')
    parser.add_argument('-o', '--output', help='Output file (default: stdout)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    
    try:
        # Read input
        if args.input:
            logger.info(f"Reading from file: {args.input}")
            with open(args.input, 'r', encoding='utf-8') as f:
                markdown = f.read()
        else:
            logger.info("Reading from stdin")
            markdown = sys.stdin.read()
        
        # Convert
        logger.debug("Starting conversion")
        notion_blocks = convert_markdown_to_notion(markdown)
        
        # Output
        output_json = json.dumps(notion_blocks, indent=2)
        if args.output:
            logger.info(f"Writing to file: {args.output}")
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output_json)
        else:
            logger.debug("Writing to stdout")
            print(output_json)
            
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

