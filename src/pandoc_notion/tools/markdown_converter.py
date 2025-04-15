"""
Markdown to Notion converter module.

This module provides a simple interface for converting Markdown-formatted text to 
Notion blocks, leveraging the existing Pandoc-based conversion pipeline.
"""

import json
import os
from typing import Dict, Any, List, Optional, Union, Callable
from pathlib import Path
import warnings

import panflute as pf

from pandoc_notion.registry import ManagerRegistry
from notion_pandoc.filter import NotionFilter, NotionConfig
from pandoc_notion.models.base import Block

# Import debug_trace for detailed diagnostics
try:
    from pandoc_notion.debug.debug_trace import debug_trace
except ImportError:
    # Fallback decorator that does nothing if debug module not found
    def debug_trace(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if kwargs or not args else decorator(args[0])


class MarkdownConverter:
    """
    Converter for transforming Markdown text into Notion blocks.
    
    This class provides a simple interface for converting Markdown-formatted text
    to Notion blocks that can be used with the Notion API.
    """
    
    def __init__(self, custom_managers=None, pandoc_options=None):
        """
        Initialize the Markdown converter.
        
        Args:
            custom_managers: Optional list of custom manager classes to register
                            in addition to the default managers.
            pandoc_options: Optional dictionary of Pandoc conversion options.
        """
        # Initialize the registry with default and custom managers
        self.registry = ManagerRegistry()
        if custom_managers:
            for manager in custom_managers:
                self.registry.register_manager(manager)
                
        # Configure Pandoc options
        self.pandoc_options = pandoc_options or {}
        
        # Initialize the Notion filter
        self.config = NotionConfig()
        if pandoc_options:
            for key, value in pandoc_options.items():
                self.config.set(key, value)
        
        self.filter = NotionFilter(config=self.config, registry=self.registry)
        
        # Initialize handler dictionary for direct element conversion
        self.element_handlers = {
            pf.Para: self._convert_paragraph,
            pf.Header: self._convert_header,
            pf.BulletList: self._convert_bullet_list,
            pf.OrderedList: self._convert_ordered_list,
            pf.CodeBlock: self._convert_code_block,
            pf.BlockQuote: self._convert_block_quote,
            pf.Image: self._convert_image,
            pf.Table: self._convert_table,
            pf.HorizontalRule: self._convert_horizontal_rule,
        }
    
    @debug_trace()
    def convert_blocks(self, markdown_text: str) -> List[Block]:
        """
        Convert Markdown text to a list of Notion blocks.
        
        Args:
            markdown_text: A string containing Markdown-formatted text
            
        Returns:
            A list of Notion block objects ready for use with the Notion API
        """
        # Parse markdown to panflute document
        doc = self._parse_markdown(markdown_text)
        
        # Convert to Notion blocks
        result = self.filter.convert_doc(doc)
        
        # Extract blocks from the converted document
        return self._process_blocks(result)

    def convert(self, markdown_text: str) -> List[Block]:
        """
        Deprecated alias for convert_blocks(). Use convert_blocks() instead.
        
        Args:
            markdown_text: A string containing Markdown-formatted text
            
        Returns:
            A list of Notion block objects ready for use with the Notion API
        """
        warnings.warn(
            "The convert() method is deprecated. Use convert_blocks() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.convert_blocks(markdown_text)
    
    @debug_trace()
    def convert_file(self, file_path: Union[str, Path]) -> List[Block]:
        """
        Convert Markdown from a file to a list of Notion blocks.
        
        Args:
            file_path: Path to a Markdown file
            
        Returns:
            A list of Notion block objects ready for use with the Notion API
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Markdown file not found: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            markdown_text = f.read()
        
        return self.convert_blocks(markdown_text)
    
    def convert_to_dict(self, markdown_text: str) -> List[Dict[str, Any]]:
        """
        Convert Markdown text to a list of Notion API-compatible dictionaries.
        
        Args:
            markdown_text: A string containing Markdown-formatted text
            
        Returns:
            A list of dictionaries in the format required by the Notion API
        """
        blocks = self.convert_blocks(markdown_text)
        return self._to_api_format(blocks)
    
    @debug_trace()
    def _parse_markdown(self, markdown_text: str) -> pf.Doc:
        """
        Parse markdown text to Pandoc AST.
        
        Args:
            markdown_text: Markdown-formatted text
            
        Returns:
            A panflute document
        """
        return pf.convert_text(markdown_text, standalone=True, input_format='markdown-smart')
    
    @debug_trace()
    def _process_blocks(self, result: Dict[str, Any]) -> List[Block]:
        """
        Process the converted document to extract block objects.
        
        Args:
            result: The result dictionary from the filter
            
        Returns:
            List of Notion block objects
        """
        return self.filter.blocks
    
    def _to_api_format(self, blocks: List[Block]) -> List[Dict[str, Any]]:
        """
        Convert block objects to Notion API format.
        
        Args:
            blocks: List of Notion block objects
            
        Returns:
            List of dictionaries in Notion API format
        """
        serialized = []
        
        for block in blocks:
            if isinstance(block, Block):
                # Single block objects
                block_dict = block.to_dict()
                if isinstance(block_dict, list):
                    # Some blocks (like lists) return multiple block dicts
                    serialized.extend(block_dict)
                else:
                    serialized.append(block_dict)
            elif isinstance(block, list):
                # Lists of blocks
                for sub_block in block:
                    if isinstance(sub_block, Block):
                        block_dict = sub_block.to_dict()
                        if isinstance(block_dict, list):
                            serialized.extend(block_dict)
                        else:
                            serialized.append(block_dict)
        
        return serialized
    
    # Direct element conversion methods
    @debug_trace()
    def _convert_element(self, elem: pf.Element) -> Block:
        """
        Convert a panflute element to a Notion block using the handler pattern.
        
        Args:
            elem: A panflute element
            
        Returns:
            A Notion block object or None if no handler is available
        """
        handler = self.element_handlers.get(type(elem))
        if handler:
            return handler(elem)
        else:
            # Default to using the filter's conversion
            return self.filter.action(elem)
    
    @debug_trace()
    def _convert_paragraph(self, elem: pf.Para) -> Block:
        """Convert a paragraph element to a Notion paragraph block."""
        return self.filter.registry.get_manager_for_element(elem).convert(elem)
    
    @debug_trace()
    def _convert_header(self, elem: pf.Header) -> Block:
        """Convert a header element to a Notion heading block."""
        return self.filter.registry.get_manager_for_element(elem).convert(elem)
    
    @debug_trace()
    def _convert_bullet_list(self, elem: pf.BulletList) -> Block:
        """Convert a bullet list element to Notion bulleted list blocks."""
        return self.filter.registry.get_manager_for_element(elem).convert(elem)
    
    @debug_trace()
    def _convert_ordered_list(self, elem: pf.OrderedList) -> Block:
        """Convert an ordered list element to Notion numbered list blocks."""
        return self.filter.registry.get_manager_for_element(elem).convert(elem)
    
    def _convert_code_block(self, elem: pf.CodeBlock) -> Block:
        """Convert a code block element to a Notion code block."""
        return self.filter.registry.get_manager_for_element(elem).convert(elem)
    
    def _convert_block_quote(self, elem: pf.BlockQuote) -> Block:
        """Convert a block quote element to a Notion quote block."""
        return self.filter.registry.get_manager_for_element(elem).convert(elem)
    
    def _convert_image(self, elem: pf.Image) -> Block:
        """Convert an image element to a Notion image block."""
        return self.filter.registry.get_manager_for_element(elem).convert(elem)
    
    def _convert_table(self, elem: pf.Table) -> Block:
        """Convert a table element to a Notion table block."""
        return self.filter.registry.get_manager_for_element(elem).convert(elem)
    
    def _convert_horizontal_rule(self, elem: pf.HorizontalRule) -> Block:
        """Convert a horizontal rule element to a Notion divider block."""
        return self.filter.registry.get_manager_for_element(elem).convert(elem)

def markdown_to_notion(markdown_text: str) -> List[Block]:
    """
    Quick conversion of Markdown text to Notion blocks using default settings.
    
    Args:
        markdown_text: A string containing Markdown-formatted text
        
    Returns:
        A list of Notion block objects
    """
    converter = MarkdownConverter()
    return converter.convert_blocks(markdown_text)


def markdown_file_to_notion(file_path: Union[str, Path]) -> List[Block]:
    """
    Quick conversion of a Markdown file to Notion blocks.
    
    Args:
        file_path: Path to a Markdown file
        
    Returns:
        A list of Notion block objects
    """
    converter = MarkdownConverter()
    return converter.convert_file(file_path)


def markdown_to_notion_api(markdown_text: str) -> List[Dict[str, Any]]:
    """
    Quick conversion of Markdown text directly to Notion API format.
    
    Args:
        markdown_text: A string containing Markdown-formatted text
        
    Returns:
        A list of dictionaries in the format required by the Notion API
    """
    converter = MarkdownConverter()
    return converter.convert_to_dict(markdown_text)

