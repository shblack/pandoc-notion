from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class Block(ABC):
    """
    Base class for all Notion blocks.
    
    All specific block types (Paragraph, Heading, Code, etc.) should inherit from this class
    and implement the to_dict method to provide their specific Notion API representation.
    """
    
    def __init__(self, block_type: str):
        """
        Initialize a Block with a specific type.
        
        Args:
            block_type: The type of the block in Notion's API
        """
        self.block_type = block_type
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the block to a dictionary representation suitable for Notion API.
        
        Returns:
            A dictionary representation of the block
        """
        pass
    
    def __str__(self) -> str:
        """String representation of the block for debugging."""
        return f"{self.__class__.__name__}({self.block_type})"

