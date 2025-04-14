from typing import List, Dict, Any, Optional

from .base import Block
from .text import Text, merge_consecutive_texts


class Quote(Block):
    """
    Represents a quote block in Notion.
    
    Notion quote blocks can contain rich text content and are typically used
    for block quotes or excerpts from other sources.
    """
    
    def __init__(self, text_content: List[Text] = None):
        """
        Initialize a quote block.
        
        Args:
            text_content: List of Text objects that make up the quote content
        """
        super().__init__("quote")
        self.text_content = text_content or []
        self.children = []  # For nested blocks (paragraphs, lists, etc.)
    
    def add_text(self, text: Text) -> None:
        """
        Add a text object to the quote.
        
        Args:
            text: Text object to add
        """
        self.text_content.append(text)
    
    def add_texts(self, texts: List[Text]) -> None:
        """
        Add multiple text objects to the quote.
        
        Args:
            texts: List of Text objects to add
        """
        self.text_content.extend(texts)
    
    def add_child(self, child: Block) -> None:
        """
        Add a child block to the quote.
        
        While Notion officially only supports rich text in quotes,
        we'll keep this for potential future support or workarounds.
        
        Args:
            child: A Block object to add as a child
        """
        self.children.append(child)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the quote to a Notion API dictionary representation."""
        # Optimize text content
        optimized_texts = merge_consecutive_texts(self.text_content)
        
        # Basic quote structure
        result = {
            "object": "block",
            "type": "quote",
            "quote": {
                "rich_text": [text.to_dict() for text in optimized_texts],
                "color": "default"
            }
        }
        
        # Include children if present
        if self.children:
            # Notion does support nested blocks within quotes as of the latest API
            result["has_children"] = True
            
            # Add serialized children under the "quote" key
            result["quote"]["children"] = [] 
            for child in self.children:
                # Assume child is always a Block object now
                child_dict = child.to_dict()
                
                # Handle managers that return lists (like ListManager)
                # Their to_dict() should return a list of block dicts
                if isinstance(child_dict, list):
                     result["quote"]["children"].extend(child_dict)
                else:
                     result["quote"]["children"].append(child_dict)
        
        return result

    def __str__(self) -> str:
        """String representation of the Quote."""
        # Create a summary of the text content
        content_str = " ".join(text.get_content() for text in self.text_content)
        if len(content_str) > 37:
            content_str = content_str[:37] + "..."
        
        # Add information about children if present
        child_str = f", {len(self.children)} children" if self.children else ""
        
        return f"Quote({content_str}{child_str})"

    def __repr__(self) -> str:
        """Detailed representation of the Quote."""
        return self.__str__()
