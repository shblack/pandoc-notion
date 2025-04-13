import os
import json
import argparse
from typing import Dict, Any, List, Optional, Union

import panflute as pf

from pandoc_notion.registry import ManagerRegistry
from pandoc_notion.models.base import Block


class NotionConfig:
    """Configuration options for the Notion filter."""
    
    def __init__(self, options: Optional[Dict[str, Any]] = None):
        """
        Initialize configuration options.
        
        Args:
            options: Dictionary of configuration options
        """
        self.options = options or {}
        self._set_defaults()
    
    def _set_defaults(self) -> None:
        """Set default configuration options."""
        # Whether to include YAML metadata as Notion properties
        self.options.setdefault('include_metadata', True)
        
        # Whether to add a title block at the top of the document
        self.options.setdefault('add_title_block', True)
        
        # Whether to convert inline math (default to code blocks for compatibility)
        self.options.setdefault('convert_inline_math', True)
        
        # Whether to number equations 
        self.options.setdefault('number_equations', True)
        
        # Output format (json, markdown, etc.)
        self.options.setdefault('output_format', 'json')
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration option.
        
        Args:
            key: Option name
            default: Default value if option not found
            
        Returns:
            Option value
        """
        return self.options.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration option.
        
        Args:
            key: Option name
            value: Option value
        """
        self.options[key] = value
    
    @classmethod
    def from_file(cls, filepath: str) -> 'NotionConfig':
        """
        Create a configuration from a JSON file.
        
        Args:
            filepath: Path to a JSON configuration file
            
        Returns:
            A NotionConfig object
        """
        if not os.path.exists(filepath):
            return cls()
        
        with open(filepath, 'r') as f:
            options = json.load(f)
        
        return cls(options)


class NotionFilter:
    """
    Main pandoc filter class for converting documents to Notion format.
    
    This class orchestrates the conversion process using the registered managers.
    """
    
    def __init__(self, config: Optional[NotionConfig] = None, registry: Optional[ManagerRegistry] = None):
        """
        Initialize the filter.
        
        Args:
            config: Configuration options
            registry: Manager registry
        """
        self.config = config or NotionConfig()
        self.registry = registry or ManagerRegistry()
        self.blocks = []
        self.metadata = {}
    
    def convert_doc(self, doc: pf.Doc) -> Dict[str, Any]:
        """
        Convert a panflute document to Notion format.
        
        Args:
            doc: Panflute document
            
        Returns:
            A dictionary representation of the Notion page
        """
        # Extract metadata
        self.metadata = self._extract_metadata(doc)
        
        # Process document elements
        self.blocks = []
        for elem in doc.content:
            try:
                converted = self.registry.convert_element(elem)
                if converted:
                    if isinstance(converted, list):
                        self.blocks.extend(converted)
                    else:
                        self.blocks.append(converted)
            except Exception as e:
                import logging
                logging.error(f"Error converting element {type(elem).__name__}: {str(e)}")
        
        # Create Notion document structure
        # Create Notion document structure
        result = {
            "children": self._serialize_blocks(),
        }
        # Add metadata if configured
        if self.config.get('include_metadata') and self.metadata:
            result["metadata"] = self.metadata
        
        return result
    
    def _extract_metadata(self, doc: pf.Doc) -> Dict[str, Any]:
        """
        Extract metadata from the document.
        
        Args:
            doc: Panflute document
            
        Returns:
            Dictionary of metadata
        """
        metadata = {}
        
        if hasattr(doc, 'metadata') and doc.metadata:
            # Extract common metadata fields
            if 'title' in doc.metadata:
                metadata['title'] = pf.stringify(doc.metadata['title'])
            
            if 'author' in doc.metadata:
                authors = doc.metadata['author']
                if isinstance(authors, list):
                    metadata['authors'] = [pf.stringify(author) for author in authors]
                else:
                    metadata['authors'] = [pf.stringify(authors)]
            
            if 'date' in doc.metadata:
                metadata['date'] = pf.stringify(doc.metadata['date'])
            
            # Extract other metadata fields
            for key, value in doc.metadata.items():
                if key not in ('title', 'author', 'date'):
                    metadata[key] = pf.stringify(value)
        
        return metadata
    
    def _serialize_blocks(self) -> List[Dict[str, Any]]:
        """
        Serialize blocks to Notion API format.
        
        Returns:
            List of serialized blocks
        """
        serialized = []
        
        # Add title block if configured
        if self.config.get('add_title_block') and 'title' in self.metadata:
            from pandoc_notion.managers.heading_manager import HeadingManager
            title_block = HeadingManager.convert_plain_text(self.metadata['title'], level=1)
            serialized.append(title_block.to_dict())
        
        # Serialize all blocks
        for block in self.blocks:
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
    
    def output_json(self) -> str:
        """
        Output the blocks as JSON.
        
        Returns:
            JSON string representation of the blocks
        """
        return json.dumps({"children": self._serialize_blocks()}, indent=2)


def prepare(doc):
    """
    Initialize document processing.
    
    Args:
        doc: The panflute document
    """
    doc.notion_blocks = []
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Convert documents to Notion format')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--output', help='Output file path')
    args, _ = parser.parse_known_args()
    
    # Store configuration in the doc for later use
    doc.notion_config = NotionConfig.from_file(args.config) if args.config else NotionConfig()
    doc.notion_output_file = args.output if hasattr(args, 'output') else None
    
    # Extract metadata
    if hasattr(doc, 'metadata') and doc.metadata:
        doc.notion_metadata = {}
        # Extract common metadata fields
        if 'title' in doc.metadata:
            doc.notion_metadata['title'] = pf.stringify(doc.metadata['title'])
        
        if 'author' in doc.metadata:
            authors = doc.metadata['author']
            if isinstance(authors, list):
                doc.notion_metadata['authors'] = [pf.stringify(author) for author in authors]
            else:
                doc.notion_metadata['authors'] = [pf.stringify(authors)]
        
        if 'date' in doc.metadata:
            doc.notion_metadata['date'] = pf.stringify(doc.metadata['date'])
        
        # Extract other metadata fields
        for key, value in doc.metadata.items():
            if key not in ('title', 'author', 'date'):
                doc.notion_metadata[key] = pf.stringify(value)
    else:
        doc.notion_metadata = {}

def finalize(doc):
    """
    Finalize document processing and output results.
    
    Args:
        doc: The panflute document with processed notion_blocks
    """
    # Process all blocks and convert them to dictionaries
    serialized_blocks = []
    
    # Add title block if configured
    if doc.notion_config.get('add_title_block') and 'title' in doc.notion_metadata:
        from pandoc_notion.managers.heading_manager import HeadingManager
        title_block = HeadingManager.convert_plain_text(doc.notion_metadata['title'], level=1)
        serialized_blocks.append(title_block.to_dict())
    
    # Add all blocks
    for block in doc.notion_blocks:
        if hasattr(block, 'to_dict'):
            # Single block objects
            block_dict = block.to_dict()
            if isinstance(block_dict, list):
                # Some blocks (like lists) return multiple block dicts
                serialized_blocks.extend(block_dict)
            else:
                serialized_blocks.append(block_dict)
        elif isinstance(block, list):
            # Lists of blocks
            for sub_block in block:
                if hasattr(sub_block, 'to_dict'):
                    block_dict = sub_block.to_dict()
                    if isinstance(block_dict, list):
                        serialized_blocks.extend(block_dict)
                    else:
                        serialized_blocks.append(block_dict)
    
    # Create Notion page structure
    result = {
        "object": "page",
        "id": "test-page",
        "created_time": "2023-01-01T00:00:00.000Z",
        "last_edited_time": "2023-01-01T00:00:00.000Z",
        "archived": False,
        "properties": {},
        "children": serialized_blocks
    }
    
    # Add metadata if configured
    if doc.notion_config.get('include_metadata') and doc.notion_metadata:
        for key, value in doc.notion_metadata.items():
            if key == "title":
                result["properties"]["title"] = {
                    "id": "title",
                    "type": "title",
                    "title": [
                        {
                            "type": "text",
                            "text": {"content": value},
                            "plain_text": value
                        }
                    ]
                }
            else:
                # Add other metadata as rich_text properties
                result["properties"][key] = {
                    "id": key,
                    "type": "rich_text",
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": str(value)},
                            "plain_text": str(value)
                        }
                    ]
                }
    
    # Output based on format
    output_format = doc.notion_config.get('output_format', 'json')
    
    if output_format == 'json':
        output = json.dumps(result, indent=2)
        
        # Write to file if specified
        if hasattr(doc, 'notion_output_file') and doc.notion_output_file:
            with open(doc.notion_output_file, 'w') as f:
                f.write(output)
        else:
            # Print output to stderr (easier to capture in tests)
            import sys
            print(output, file=sys.stderr)

def main(elem, doc):
    """
    Process individual elements as they're passed by panflute.
    
    Args:
        elem: The current element being processed
        doc: The full document
        
    Returns:
        The processed element or None
    """
    # Skip document elements - they're handled in prepare() and finalize()
    if isinstance(elem, pf.Doc):
        return None
        
    try:
        # Create registry if not already stored in doc
        if not hasattr(doc, 'notion_registry'):
            doc.notion_registry = ManagerRegistry()
        
        # Try to convert the element
        manager = doc.notion_registry.find_manager(elem)
        if manager:
            converted = manager.convert(elem)
            if converted:
                # Append to notion_blocks for later processing
                if isinstance(converted, list):
                    doc.notion_blocks.extend(converted)
                else:
                    doc.notion_blocks.append(converted)
        
        # Return None to keep the original element (we're just collecting, not transforming)
        return None
    except Exception as e:
        import logging
        logging.error(f"Error converting element {type(elem).__name__}: {str(e)}")
        return None


# When run directly with panflute
if __name__ == "__main__":
    pf.run_filter(main, prepare=prepare, finalize=finalize)


def filter_markdown_to_notion(text, **kwargs):
    """
    Filter markdown text to Notion format.
    
    This is a convenience function for use in Python scripts without pandoc.
    
    Args:
        text: Markdown text
        **kwargs: Configuration options
        
    Returns:
        Notion JSON
    """
    import io
    from panflute import convert_text
    
    # Create filter
    config = NotionConfig(kwargs)
    notion_filter = NotionFilter(config=config)
    
    # Convert text to panflute document
    doc = convert_text(text, standalone=True)
    
    # Process the document
    result = notion_filter.convert_doc(doc)
    
    # Return JSON result
    return json.dumps(result, indent=2)

