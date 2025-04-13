from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar

import panflute as pf

T = TypeVar('T')


class Manager(ABC):
    """
    Base class for all element managers.
    
    Managers are responsible for converting panflute elements to Notion blocks or components.
    Each specific element type (paragraph, heading, code, etc.) should have its own manager.
    """
    
    @classmethod
    @abstractmethod
    def can_convert(cls, elem: pf.Element) -> bool:
        """
        Check if this manager can convert the given panflute element.
        
        Args:
            elem: A panflute element
            
        Returns:
            True if this manager can convert the element, False otherwise
        """
        pass
    
    @classmethod
    @abstractmethod
    def to_dict(cls, elem: pf.Element) -> List[Dict[str, Any]]:
        """
        Convert a panflute element to Notion API-level blocks.
        
        This public method must return objects at the Notion API abstraction level,
        where each block (including list items) is represented at the API level.
        Always returns a list, even if it contains only a single block.
        
        Args:
            elem: A panflute element
            
        Returns:
            A list of Notion API blocks (List[Dict[str, Any]])
        """
        pass
    
    @classmethod
    def find_converter(cls, elem: pf.Element, managers: List[Type['Manager']]) -> Optional[Type['Manager']]:
        """
        Find the appropriate manager to convert a given element.
        
        Args:
            elem: A panflute element
            managers: A list of manager classes to search through
            
        Returns:
            The first manager class that can convert the element, or None if none can
        """
        for manager in managers:
            if manager.can_convert(elem):
                return manager
        return None

