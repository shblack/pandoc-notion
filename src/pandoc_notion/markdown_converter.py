"""
Markdown to Notion converter module.

This module provides a simple interface for converting Markdown-formatted text to 
Notion blocks, leveraging the existing Pandoc-based conversion pipeline.
"""

import json
import os
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

import panflute as pf

from pandoc_notion.registry import ManagerRegistry
from pandoc_notion.filter import NotionFilter, NotionConfig
from pandoc_notion.models.base import Block


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
    
    def convert(self, markdown_text: str) -> List[Block]:
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
        
        return self.convert(markdown_text)
    
    def convert_to_dict(self, markdown_text: str) -> List[Dict[str, Any]]:
        """
        Convert Markdown text to a list of Notion API-compatible dictionaries.
        
        Args:
            markdown_text: A string containing Markdown-formatted text
            
        Returns:
            A list of dictionaries in the format required by the Notion API
        """
        blocks = self.convert(markdown_text)
        return self._to_api_format(blocks)
    
    def _parse_markdown(self, markdown_text: str) -> pf.Doc:
        """
        Parse markdown text to Pandoc AST.
        
        Args:
            markdown_text: Markdown-formatted text
            
        Returns:
            A panflute document
        """
        return pf.convert_text(markdown_text, standalone=True)
    
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


def markdown_to_notion(markdown_text: str) -> List[Block]:
    """
    Quick conversion of Markdown text to Notion blocks using default settings.
    
    Args:
        markdown_text: A string containing Markdown-formatted text
        
    Returns:
        A list of Notion block objects
    """
    converter = MarkdownConverter()
    return converter.convert(markdown_text)


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

