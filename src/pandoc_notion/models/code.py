from typing import List, Dict, Any, Optional

from .base import Block


class Code(Block):
    """
    Represents a code block in Notion.
    
    Notion code blocks support syntax highlighting for various languages and can have a caption.
    """
    
    def __init__(self, code: str, language: str = "plain text", caption: Optional[str] = None) -> None:
        """
        Initialize a code block.
        
        Args:
            code: The code content as a string
            language: Programming language for syntax highlighting (defaults to plain text)
            caption: Optional caption or filename for the code block
            
        Example:
            >>> code_block = Code("print('Hello')", "python", "example.py")
        """
        super().__init__("code")
        self.code = code
        self.language = language
        self.caption = caption
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the code block to a Notion API dictionary representation."""
        from .text import Text
        
        # Create code content as Text object
        code_text = Text(self.code)
        
        result = {
            "object": "block",
            "type": self.block_type,
            "code": {
                "caption": [],
                "rich_text": [code_text.to_dict()],
                "language": self.language
            }
        }
        
        # Add caption if provided using Text model
        if self.caption:
            caption_text = Text(self.caption)
            result["code"]["caption"] = [caption_text.to_dict()]
        
        return result
    
    def __str__(self) -> str:
        """String representation of the code block for debugging."""
        code_preview = self.code.split("\n")[0][:40]
        if len(code_preview) < len(self.code):
            code_preview += "..."
        caption_str = f", caption='{self.caption}'" if self.caption else ""
        return f"Code(language='{self.language}'{caption_str}, {code_preview})"

