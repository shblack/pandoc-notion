"""
Registry mixin for managers that need to find other managers.
Avoids circular dependencies by using a shared registry instance.
"""

from typing import Optional, Type, Any, List
import panflute as pf

from .base import Manager
from ..utils.debug import debug_decorator

# Shared registry instance
_registry = None

def set_registry(registry):
    """Set the shared registry instance."""
    global _registry
    _registry = registry

class RegistryMixin:
    """Mixin providing registry search functionality to managers."""
    
    @classmethod
    @debug_decorator
    def find_manager(cls, elem: pf.Element) -> Optional[Type[Manager]]:
        """Find a manager for the given element using the shared registry."""
        global _registry
        if _registry is not None:
            return _registry.find_manager(elem)
        return None
    
    @classmethod
    @debug_decorator
    def convert_with_manager(cls, elem: pf.Element) -> List[Any]:
        """
        Convert an element using an appropriate manager from the registry.
        
        Returns an empty list if no manager is found or conversion fails
        with an expected exception.
        
        Re-raises unexpected exceptions to aid in debugging.
        """
        manager = cls.find_manager(elem)
        if not manager:
            return []
        
        try:
            return manager.convert(elem)
        except (ValueError, TypeError) as e:
            # Expected exceptions during conversion - debug decorator will log them
            return []
        except Exception as e:
            # Re-raise unexpected exceptions for better debugging
            raise

