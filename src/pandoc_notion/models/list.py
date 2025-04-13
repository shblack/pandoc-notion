from typing import List as PyList, Dict, Any, Optional, Union, Literal

from .base import Block
from .text import Text, merge_consecutive_texts


class ListItem:
    """
    Represents a single item in a list.

    ListItems can contain rich text content and potentially other blocks
    for complex nested content. Lists can be bulleted, numbered, or todo lists.
    """

    def __init__(
        self,
        text_content: PyList[Text] = None,
        item_type: Literal["bulleted", "numbered", "todo"] = "bulleted",
        checked: bool = False
    ):
        """
        Initialize a list item.

        Args:
            text_content: List of Text objects that make up the list item content
            item_type: Type of list item ("bulleted", "numbered", or "todo")
            checked: Whether a todo list item is checked (only applies to todo items)
        """
        self.text_content = text_content or []
        self.children = []  # For nested lists or other content
        self.item_type = item_type
        self.checked = checked if item_type == "todo" else False

    def add_text(self, text: Text) -> None:
        """
        Add a text object to the list item.

        Args:
            text: Text object to add
        """
        self.text_content.append(text)

    def add_texts(self, texts: PyList[Text]) -> None:
        """
        Add multiple text objects to the list item.

        Args:
            texts: List of Text objects to add
        """
        self.text_content.extend(texts)

    def add_child(self, child: 'List') -> None:
        """
        Add a child list to this list item.

        Args:
            child: A List object to add as a child
        """
        self.children.append(child)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the list item to a dictionary containing its content.
        This is used by the parent List's to_dict method.
        It should return rich_text and children (if any).
        The 'checked' status is handled by the parent List.to_dict based on item_type.
        """
        # Optimize text content
        optimized_texts = merge_consecutive_texts(self.text_content)

        result = {
            "rich_text": [text.to_dict() for text in optimized_texts],
            # Recursively serialize children.
            # Child.to_dict() for a List returns a *list* of blocks.
            # Other block types return a single block dict.
            "children": [
                block_dict
                for child in self.children
                for block_dict in (child.to_dict() if isinstance(child, List) else [child.to_dict()])
                if block_dict # Ensure we don't add empty/None dicts if a child.to_dict somehow returns that
            ] if self.children else []
        }
        # No need to add "checked" here, the parent List.to_dict handles it.
        return result

    def __str__(self) -> str:
        """String representation of the list item for debugging."""
        content_str = " ".join(text.content for text in self.text_content)
        if len(content_str) > 40:
            content_str = content_str[:37] + "..."

        type_str = self.item_type
        if self.item_type == "todo":
            check_str = "✓" if self.checked else "☐"
            type_str = f"todo({check_str})"

        child_str = f", {len(self.children)} children" if self.children else ""
        return f"ListItem({type_str}, {content_str}{child_str})"


class List(Block):
    """
    Represents a logical collection of list items (bulleted, numbered, or todo).
    Note: This does not directly map to a single Notion block, but rather helps
    manage the conversion of Pandoc lists into sequences of Notion list item blocks.
    """

    # Type constants for Notion block types associated with list items
    BULLETED = "bulleted_list_item"
    NUMBERED = "numbered_list_item"
    TODO = "to_do"

    # Type alias for list item types
    ListItemTypeInternal = Literal["bulleted", "numbered", "todo"]
    NotionListItemType = Literal["bulleted_list_item", "numbered_list_item", "to_do"]

    def __init__(self, initial_list_item_type: NotionListItemType, items: PyList[ListItem] = None):
        """
        Initialize a list collection helper.

        Args:
            initial_list_item_type: The Notion block type corresponding to the list context
                                    (e.g., BULLETED for a bullet list). This might not apply
                                    to all contained items if types are mixed (like todos in a bullet list).
            items: List of ListItem objects
        """
        # The 'block_type' here represents the context/origin, not necessarily the type of every item.
        # We store it, but the serialization relies on individual item types.
        super().__init__(initial_list_item_type)
        self.items = items or []

    def add_item(self, item: ListItem) -> None:
        """
        Add an item to the list.

        Args:
            item: ListItem to add
        """
        self.items.append(item)

    # Helper methods like is_bulleted, is_numbered, is_todo based on initial_list_item_type
    # might be misleading if the list contains mixed items. They reflect the context of creation.
    def _context_is_bulleted(self) -> bool:
        """Check if the list context was originally bulleted."""
        return self.block_type == List.BULLETED

    def _context_is_numbered(self) -> bool:
        """Check if the list context was originally numbered."""
        return self.block_type == List.NUMBERED

    def _context_is_todo(self) -> bool:
        """Check if the list context was originally todo."""
        return self.block_type == List.TODO

    def to_dict(self) -> PyList[Dict[str, Any]]:
        """
        Convert the list to a Notion API dictionary representation.

        Note: Unlike most blocks, lists in Notion are represented as a series of
        individual list item blocks, not as a single container block. Therefore,
        this method returns a list of dictionaries, one for each list item,
        respecting the specific type of each item (bulleted, numbered, or todo).
        """
        result = []

        for item in self.items:
            # Map the internal item_type ('bulleted', 'numbered', 'todo') to Notion's block type names
            item_type_mapping = {
                "bulleted": List.BULLETED,
                "numbered": List.NUMBERED,
                "todo": List.TODO
            }
            # Use item.item_type (e.g., "todo") to look up the Notion block type (e.g., "to_do")
            # Default to BULLETED if item.item_type is somehow invalid or missing
            notion_item_type = item_type_mapping.get(item.item_type, List.BULLETED)

            # Get the dictionary representation of the item's content (rich_text, children)
            item_content = item.to_dict()

            # Basic structure for the Notion block
            item_dict = {
                "object": "block",
                "type": notion_item_type,  # Use the item's specific Notion type
                notion_item_type: {        # Use the item's specific type as the key
                    "rich_text": item_content.get("rich_text", []), # Safely get rich_text
                    "color": "default"
                }
            }

            # Add the 'checked' property specifically for 'to_do' items
            if notion_item_type == List.TODO:
                # Ensure 'checked' attribute exists on the item before accessing
                if hasattr(item, 'checked'):
                    item_dict[notion_item_type]["checked"] = item.checked
                else:
                    # Default or log error if 'checked' is missing unexpectedly
                    item_dict[notion_item_type]["checked"] = False # Default to unchecked

            # Handle children serialization from item_content
            child_blocks_data = item_content.get("children")
            if child_blocks_data:
                 # item.to_dict() should have already returned serialized children correctly
                 # The list should contain Notion block dictionaries
                item_dict["has_children"] = True
                # Move children inside the block type object instead of at root level
                item_dict[notion_item_type]["children"] = child_blocks_data # Use the already processed children list


            result.append(item_dict)

        return result

    def __str__(self) -> str:
        """String representation of the list collection for debugging."""
        # Use the stored block_type (initial context) for the string representation
        if self.block_type == List.BULLETED:
            type_str = "BulletedContext"
        elif self.block_type == List.NUMBERED:
            type_str = "NumberedContext"
        elif self.block_type == List.TODO:
            type_str = "TodoContext"
        else:
            type_str = "UnknownContext" # Should not happen based on __init__ validation
        items_str = f"{len(self.items)} items"
        return f"{type_str}List({items_str})"


# Helper functions

def create_bulleted_list(items: PyList[ListItem] = None) -> List:
    """
    Create a helper object representing a bulleted list context.

    Args:
        items: List of ListItem objects

    Returns:
        A List object initialized with bulleted type context
    """
    return List(List.BULLETED, items)


def create_numbered_list(items: PyList[ListItem] = None) -> List:
    """
    Create a helper object representing a numbered list context.

    Args:
        items: List of ListItem objects

    Returns:
        A List object initialized with numbered type context
    """
    return List(List.NUMBERED, items)


def create_todo_list(items: PyList[ListItem] = None) -> List:
    """
    Create a helper object representing a todo list context.
    Note that individual items must have item_type='todo'.

    Args:
        items: List of ListItem objects (should have item_type='todo')

    Returns:
        A List object initialized with todo type context
    """
    return List(List.TODO, items)


def create_list_item_from_text(
    text: str,
    item_type: Literal["bulleted", "numbered", "todo"] = "bulleted",
    checked: bool = False
) -> ListItem:
    """
    Create a list item from plain text.

    Args:
        text: Plain text content
        item_type: Type of list item ("bulleted", "numbered", or "todo")
        checked: Whether a todo list item is checked (only applies to todo items)

    Returns:
        A ListItem object
    """
    from .text import Text

    item = ListItem(item_type=item_type, checked=checked)
    item.add_text(Text(text))
    return item


def create_todo_item(text: str, checked: bool = False) -> ListItem:
    """
    Create a todo list item from plain text.

    Args:
        text: Plain text content
        checked: Whether the todo item is checked

    Returns:
        A ListItem object configured as a todo item
    """
    return create_list_item_from_text(text, item_type="todo", checked=checked)

