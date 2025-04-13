from typing import List as PyList, Union, Dict, Any, Optional, Type

import panflute as pf

from ..models.list import List, ListItem, create_bulleted_list, create_numbered_list, create_todo_list, create_todo_item
from ..models.text import Text
from ..utils.debug import debug_decorator
from .base import Manager
from .text_manager import TextManager
from .paragraph_manager import ParagraphManager


class ListManager(Manager):
    """
    Manager for handling list elements and converting them to Notion List blocks.
    
    Handles bulleted (unordered), numbered (ordered), and todo lists,
    preserving nesting and hierarchy. Also supports mixed list types where
    todo items can appear alongside regular list items.
    """
    
    @classmethod
    @debug_decorator
    def can_convert(cls, elem: pf.Element) -> bool:
        """Check if the element is a list that can be converted."""
        return isinstance(elem, (pf.BulletList, pf.OrderedList))
    
    @classmethod
    @debug_decorator
    def convert(cls, elem: pf.Element) -> PyList[List]:
        """
        Convert a panflute list element to Notion List objects.
        
        In Notion's data model, each list item is represented as a separate block.
        This method returns a list of List objects, one for each list item.
        
        Args:
            elem: A panflute BulletList or OrderedList element
            
        Returns:
            A list of Notion List objects
        """
        if isinstance(elem, pf.BulletList):
            return cls._convert_bullet_list(elem)
        elif isinstance(elem, pf.OrderedList):
            return cls._convert_ordered_list(elem)
        else:
            raise ValueError(f"Expected BulletList or OrderedList element, got {type(elem).__name__}")
    
    @classmethod
    @debug_decorator
    def to_dict(cls, elem: pf.Element) -> PyList[Dict[str, Any]]:
        """
        Convert a panflute list element to Notion API-level blocks.
        In the Notion API, each list item is a separate block. This method
        returns a list of API-level dictionaries representing list items.
        
        Args:
            elem: A panflute BulletList or OrderedList element
            
        Returns:
            A list of Notion API-level blocks
        """
        # Get List objects using convert
        list_objects = cls.convert(elem)
            
        # Convert List objects to API-level dictionaries
        api_blocks = []
        for list_obj in list_objects:
            api_blocks.extend(list_obj.to_dict())
        return api_blocks

    @classmethod
    def _convert_bullet_list(cls, elem: pf.BulletList) -> PyList[List]:
        """
        Convert a panflute BulletList to a list of Notion bulleted list blocks.
        
        Note: Individual items in the list may be identified as todo items
        if they contain checkbox characters.
        
        Args:
            elem: A panflute BulletList element
            
        Returns:
            A list of Notion List objects, one for each list item
        """
        api_blocks = []
        
        for item in elem.content:
            # Convert the list item
            bullet_item = cls._convert_list_item(item, "bulleted")
            
            # Create a List with just this item
            single_item_list = create_bulleted_list([bullet_item])
            api_blocks.append(single_item_list)
        
        return api_blocks

    @classmethod
    def _convert_ordered_list(cls, elem: pf.OrderedList) -> PyList[List]:
        """
        Convert a panflute OrderedList to a list of Notion numbered list blocks.
        
        Args:
            elem: A panflute OrderedList element
            
        Returns:
            A list of Notion List objects, one for each list item
        """
        api_blocks = []
        
        # Handle list attributes if needed (start number, etc.)
        # As of now, Notion doesn't support custom numbering for lists
        # so we ignore start, style, and delimiter attributes
        
        for item in elem.content:
            # Convert the list item
            numbered_item = cls._convert_list_item(item, "numbered")
            
            # Create a List with just this item
            single_item_list = create_numbered_list([numbered_item])
            api_blocks.append(single_item_list)
        
        return api_blocks

    @classmethod
    def _is_checkbox(cls, text: str) -> bool:
        """
        Check if the text starts with a checkbox character.
        
        Args:
            text: Text to check
            
        Returns:
            True if the text starts with a checkbox character, False otherwise
        """
        # Unicode characters for checked and unchecked boxes
        return text.startswith("☐") or text.startswith("☒")
    
    @classmethod
    def _is_checked_checkbox(cls, text: str) -> bool:
        """
        Check if the text starts with a checked checkbox character.
        
        Args:
            text: Text to check
            
        Returns:
            True if the text starts with a checked checkbox character, False otherwise
        """
        # Only the checked box character
        return text.startswith("☒")
    
    @classmethod
    def _strip_checkbox(cls, text: str) -> str:
        """
        Remove checkbox character from the beginning of text.
        
        Args:
            text: Text with possible checkbox prefix
            
        Returns:
            Text with checkbox removed if present
        """
        if cls._is_checkbox(text):
            # Remove checkbox and optional space after it
            return text[1:].lstrip()
        return text
    
    @classmethod
    def _convert_list_item(cls, elem: pf.ListItem, parent_type: str = "bulleted") -> ListItem:
        """
        Convert a panflute ListItem to a Notion ListItem.
        
        In the Pandoc AST, a list item typically contains:
        1. A single Plain element that wraps all text content
        2. Occasionally, nested BulletList or OrderedList elements
        
        This method also detects todo list items by looking for checkbox characters
        at the beginning of the first text element.
        
        Args:
            elem: A panflute ListItem element
            parent_type: The type of the parent list ("bulleted" or "numbered")
            
        Returns:
            A Notion ListItem object with appropriate type and checked status
        """
        is_todo_item = False
        is_checked = False
        
        # Check if the first element is a Plain with a checkbox
        if elem.content and isinstance(elem.content[0], pf.Plain):
            first_plain = elem.content[0]
            # Check if the first element in the Plain is a Str with a checkbox
            if first_plain.content and isinstance(first_plain.content[0], pf.Str):
                first_str = first_plain.content[0]
                if cls._is_checkbox(first_str.text):
                    is_todo_item = True
                    is_checked = cls._is_checked_checkbox(first_str.text)
                    # Modify the first Str to remove the checkbox
                    first_str.text = cls._strip_checkbox(first_str.text)
                    # Remove the Space element that follows the checkbox character
                    first_plain.content.pop(1)
        # Create list item with the appropriate type
        item_type = "todo" if is_todo_item else parent_type
        list_item = ListItem(item_type=item_type, checked=is_checked)
        
        # Process the content of the list item
        for child in elem.content:
            # Handle Plain elements - these are the standard containers for text in list items in the panflute AST
            if isinstance(child, pf.Plain):
                # Extract text content from the Plain element, preserving all formatting
                texts = TextManager.create_text_elements(child.content)
                list_item.add_texts(texts)
            # Handle nested bullet lists
            elif isinstance(child, pf.BulletList):
                # Process nested bullet list
                nested_lists = cls._convert_bullet_list(child)
                for nested_list in nested_lists:
                    list_item.add_child(nested_list)
            # Handle nested ordered lists
            elif isinstance(child, pf.OrderedList):
                # Process nested ordered list
                nested_lists = cls._convert_ordered_list(child)
                for nested_list in nested_lists:
                    list_item.add_child(nested_list)
                                
        return list_item

    @classmethod
    def create_bulleted_list_from_texts(cls, texts: PyList[str]) -> List:
        """
        Create a bulleted list from a list of plain text strings.
        
        Args:
            texts: List of plain text strings, one per list item
            
        Returns:
            A Notion bulleted List object
        """
        bullet_list = create_bulleted_list()
        
        for text_str in texts:
            item = ListItem()
            item.add_text(Text(text_str))
            bullet_list.add_item(item)
        
        return bullet_list
    
    @classmethod
    def create_numbered_list_from_texts(cls, texts: PyList[str]) -> List:
        """
        Create a numbered list from a list of plain text strings.
        
        Args:
            texts: List of plain text strings, one per list item
            
        Returns:
            A Notion numbered List object
        """
        numbered_list = create_numbered_list()
        
        for text_str in texts:
            item = ListItem()
            item.add_text(Text(text_str))
            numbered_list.add_item(item)
        
        return numbered_list
    
    @classmethod
    def create_todo_list_from_texts(cls, texts: PyList[str], checked_indices: PyList[int] = None) -> List:
        """
        Create a todo list from a list of plain text strings.
        
        Args:
            texts: List of plain text strings, one per list item
            checked_indices: List of indices of items that should be checked
            
        Returns:
            A Notion todo List object
        """
        todo_list = create_todo_list()
        checked_indices = checked_indices or []
        
        for i, text_str in enumerate(texts):
            checked = i in checked_indices
            item = create_todo_item(text_str, checked)
            todo_list.add_item(item)
        
        return todo_list

