from typing import List, Dict, Any, Literal

from .base import Block
from .text import Text, merge_consecutive_texts


class Heading(Block):
    """
    Represents a heading block in Notion.
    
    Notion supports three heading levels: h1, h2, and h3.
    Each heading consists of rich text content.
    """
    
    # Type alias for heading levels
    HeadingLevel = Literal["heading_1", "heading_2", "heading_3"]
    
    def __init__(self, level: int, text_content: List[Text] = None):
        """
        Initialize a heading block.
        
        Args:
            level: Heading level (1, 2, or 3)
            text_content: List of Text objects that make up the heading content
        """
        # Convert level to Notion heading type ("heading_1", "heading_2", "heading_3")
        # Clamp level to range 1-3 since Notion only supports these levels
        clamped_level = min(max(level, 1), 3)
        heading_type = f"heading_{clamped_level}"
        
        super().__init__(heading_type)
        self.level = clamped_level
        self.text_content = text_content or []
    
    def add_text(self, text: Text) -> None:
        """
        Add a text object to the heading.
        
        Args:
            text: Text object to add
        """
        self.text_content.append(text)
    
    def add_texts(self, texts: List[Text]) -> None:
        """
        Add multiple text objects to the heading.
        
        Args:
            texts: List of Text objects to add
        """
        self.text_content.extend(texts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the heading to a Notion API dictionary representation."""
        # Optimize by merging consecutive text objects with the same formatting
        optimized_texts = merge_consecutive_texts(self.text_content)
        
        return {
            "object": "block",
            "type": self.block_type,
            self.block_type: {
                "rich_text": [text.to_dict() for text in optimized_texts],
                "color": "default"
            }
        }
    
    def __str__(self) -> str:
        """String representation of the heading for debugging."""
        content_str = " ".join(text.content for text in self.text_content)
        if len(content_str) > 50:
            content_str = content_str[:47] + "..."
        return f"Heading(level={self.level}, {content_str})"

