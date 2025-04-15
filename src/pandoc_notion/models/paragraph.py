from typing import List, Dict, Any

from pandoc_notion.models.base import Block
from pandoc_notion.models.text import Text, merge_consecutive_texts


class Paragraph(Block):
    """
    Represents a paragraph block in Notion.
    
    A paragraph is one of the basic building blocks in Notion documents,
    consisting of rich text content.
    """
    
    def __init__(self, text_content: List[Text] = None):
        """
        Initialize a paragraph block.
        
        Args:
            text_content: List of Text objects that make up the paragraph content
        """
        super().__init__("paragraph")
        self.text_content = text_content or []
    
    def add_text(self, text: Text) -> None:
        """
        Add a text object to the paragraph.
        
        Args:
            text: Text object to add
        """
        self.text_content.append(text)
    
    def add_texts(self, texts: List[Text]) -> None:
        """
        Add multiple text objects to the paragraph.
        
        Args:
            texts: List of Text objects to add
        """
        self.text_content.extend(texts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the paragraph to a Notion API dictionary representation."""
        # Optimize by merging consecutive text objects with the same formatting
        optimized_texts = merge_consecutive_texts(self.text_content)
        
        return {
            "object": "block",
            "type": self.block_type,
            "paragraph": {
                "rich_text": [text.to_dict() for text in optimized_texts],
                "color": "default"
            }
        }
    
    def __str__(self) -> str:
        """String representation of the paragraph for debugging."""
        content_str = " ".join(text.content for text in self.text_content)
        if len(content_str) > 50:
            content_str = content_str[:47] + "..."
        return f"Paragraph({content_str})"

