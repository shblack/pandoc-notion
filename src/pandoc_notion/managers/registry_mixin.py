"""
Registry mixin for managers that need to find other managers.
Avoids circular dependencies by using a shared registry instance.
"""

from typing import Optional, Type, Any, List
import panflute as pf

from pandoc_notion.managers.base import Manager
# Import debug_trace for detailed diagnostics
from python_debug import debug_trace

# Shared registry instance
_registry = None

def set_registry(registry):
    """Set the shared registry instance."""
    global _registry
    _registry = registry

class RegistryMixin:
    """Mixin providing registry search functionality to managers."""
    
    @classmethod
    @debug_trace()
    def find_manager(cls, elem: pf.Element) -> Optional[Type[Manager]]:
        """Find a manager for the given element using the shared registry."""
        global _registry
        if _registry is not None:
            return _registry.find_manager(elem)
        print("Warning: Registry not set in RegistryMixin")
        return None
    
    @classmethod
    @debug_trace()
    def convert_with_manager(cls, elem: pf.Element) -> List[Any]:
        """
        Convert an element using an appropriate manager from the registry.
        
        Returns an empty list if no manager is found or conversion fails
        with an expected exception.
        
        Re-raises unexpected exceptions to aid in debugging.
        """
        manager = cls.find_manager(elem)
        if not manager:
            print(f"Warning: No manager found for element type {type(elem).__name__}")
            return []
        
        try:
            # The found manager's convert method should handle its own tracing if needed
            return manager.convert(elem)
        except (ValueError, TypeError) as e:
            # Expected exceptions during conversion - debug decorator will log them if applied
            print(f"Handled conversion error for {type(elem).__name__} with {manager.__name__}: {e}")
            return []
        except Exception as e:
            # Re-raise unexpected exceptions for better debugging
            print(f"Unexpected error during conversion for {type(elem).__name__} with {manager.__name__}: {e}")
            raise

