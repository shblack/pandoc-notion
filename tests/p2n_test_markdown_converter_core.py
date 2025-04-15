"""
Core functionality tests for the Filter and convert_markdown_to_notion functions.

These tests focus on the basic conversion methods, error handling,
and basic workflow validation without testing specific block types.
"""

import os
import tempfile
from pathlib import Path

import pytest

from pandoc_notion.filter import Filter, convert_markdown_to_notion
from pandoc_notion.models.base import Block


def test_convert_blocks_returns_list_of_blocks():
    """Test that convert_markdown_to_notion returns blocks objects."""
    markdown = "Simple paragraph for testing."
    result = convert_markdown_to_notion(markdown)
    blocks = result["children"]
    
    assert isinstance(blocks, list)
    assert len(blocks) > 0
    assert all(isinstance(block, dict) and "type" in block for block in blocks)


def test_convert_blocks_handles_empty_string():
    """Test that convert_markdown_to_notion handles empty input gracefully."""
    result = convert_markdown_to_notion("")
    blocks = result["children"]
    
    assert isinstance(blocks, list)
    # An empty markdown string should result in at least an empty paragraph
    assert len(blocks) > 0


def test_convert_file_reads_and_converts_file():
    """Test that Filter can correctly read a file and convert its content."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("File content for testing.")
        temp_file_path = f.name
    
    try:
        filter_obj = Filter()
        result = filter_obj.process_file(temp_file_path)
        blocks = result["children"]
        
        assert isinstance(blocks, list)
        assert len(blocks) > 0
        assert all(isinstance(block, dict) and "type" in block for block in blocks)
    finally:
        os.unlink(temp_file_path)


def test_convert_file_accepts_path_object():
    """Test that Filter accepts a Path object as well as a string."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("Testing with Path object.")
        temp_file_path = f.name
    
    try:
        filter_obj = Filter()
        # Use a Path object instead of a string
        result = filter_obj.process_file(Path(temp_file_path))
        blocks = result["children"]
        
        assert isinstance(blocks, list)
        assert len(blocks) > 0
    finally:
        os.unlink(temp_file_path)


def test_convert_file_raises_error_for_nonexistent_file():
    """Test that process_file raises FileNotFoundError for non-existent files."""
    filter_obj = Filter()
    non_existent_path = "/tmp/this_file_does_not_exist_12345.md"
    
    with pytest.raises(FileNotFoundError):
        filter_obj.process_file(non_existent_path)


def test_convert_returns_api_format():
    """Test that convert_markdown_to_notion returns dictionaries in the Notion API format."""
    markdown = "Testing API format."
    result = convert_markdown_to_notion(markdown)
    blocks = result["children"]
    
    assert isinstance(blocks, list)
    assert len(blocks) > 0
    
    # Check that output matches expected Notion API format
    for item in blocks:
        assert isinstance(item, dict)
        assert 'type' in item
        block_type = item['type']
        assert block_type in item  # Each block has its type as a key


def test_helper_function_convert_markdown_to_notion():
    """Test that the function convert_markdown_to_notion works correctly."""
    markdown = "Helper function test."
    result = convert_markdown_to_notion(markdown)
    blocks = result["children"]
    
    assert isinstance(blocks, list)
    assert len(blocks) > 0
    assert all(isinstance(block, dict) and "type" in block for block in blocks)

