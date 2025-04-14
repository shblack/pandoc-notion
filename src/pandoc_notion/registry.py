from typing import List, Type, Optional, Dict, Any, Union

import panflute as pf

from pandoc_notion.managers.base import Manager
from pandoc_notion.managers.text_manager import TextManager
from pandoc_notion.managers.paragraph_manager import ParagraphManager
from pandoc_notion.managers.heading_manager import HeadingManager
from pandoc_notion.managers.code_manager import CodeManager
from pandoc_notion.managers.list_manager import ListManager
from pandoc_notion.managers.quote_manager import QuoteManager
from pandoc_notion.managers.registry_mixin import set_registry


class ManagerRegistry:
    """
    Registry for all element managers.
    
    This class provides a centralized registry for all managers,
    with methods to find the appropriate manager for a given element.
    """
    
    def __init__(self, managers: List[Type[Manager]] = None):
        """
        Initialize the registry with a list of manager classes.
        
        Args:
            managers: List of Manager classes to register
        """
        self.managers = managers or []
        
        # Register default managers if none provided
        # Register default managers if none provided
        if not self.managers:
            self.register_default_managers()
        
        # Set this registry instance for all managers to use via the mixin
        set_registry(self)
    def register_manager(self, manager_class: Type[Manager]) -> None:
        """
        Register a manager class with the registry.
        
        Args:
            manager_class: Manager class to register
        """
        if manager_class not in self.managers:
            self.managers.append(manager_class)
    
    def register_default_managers(self) -> None:
        """Register all default managers."""
        # Block elements - specialized blocks first
        self.register_manager(QuoteManager)  # Handle quotes before other elements
        self.register_manager(HeadingManager)
        self.register_manager(CodeManager)
        self.register_manager(ListManager)
        
        # Text and inline elements
        self.register_manager(TextManager)
        
        # Register ParagraphManager last as fallback
        self.register_manager(ParagraphManager)
        
        # Add more managers as they are implemented
    
    def find_manager(self, elem: pf.Element) -> Optional[Type[Manager]]:
        """
        Find the appropriate manager for a given element.
        
        If multiple managers can handle the element, the first one is returned
        based on the registration order.
        
        Args:
            elem: A panflute element
            
        Returns:
            A Manager class that can handle the element, or None if none found
        """
        for manager in self.managers:
            if manager.can_convert(elem):
                return manager
        return None
    
    def convert_element(self, elem: pf.Element) -> Any:
        """
        Convert a single element using the appropriate manager.
        
        Args:
            elem: A panflute element
            
        Returns:
            The converted Notion object, or None if no manager was found
            
        Raises:
            ValueError: If no manager can handle the element
        """
        manager = self.find_manager(elem)
        if not manager:
            raise ValueError(f"No manager found for element type: {type(elem).__name__}")
        
        return manager.convert(elem)
    
    def batch_convert(self, elements: List[pf.Element]) -> List[Any]:
        """
        Convert a list of elements using the appropriate managers.
        
        Elements that can't be converted are skipped.
        
        Args:
            elements: A list of panflute elements
            
        Returns:
            A list of converted Notion objects
        """
        result = []
        
        for elem in elements:
            try:
                manager = self.find_manager(elem)
                if manager:
                    converted = manager.convert(elem)
                    if isinstance(converted, list):
                        result.extend(converted)
                    else:
                        result.append(converted)
            except Exception as e:
                # Log the error but continue processing other elements
                import logging
                logging.error(f"Error converting element {type(elem).__name__}: {str(e)}")
        
        return result
    
    def dump_managers(self) -> List[str]:
        """
        Get a list of registered manager names for debugging.
        
        Returns:
            A list of manager class names
        """
        return [manager.__name__ for manager in self.managers]

