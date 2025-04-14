"""
Manage conversion of text elements to Notion format.

This module provides the TextManager class for converting Pandoc inline elements
to Notion's rich text format, handling formatting, links, and special elements.
"""

from typing import List, Optional, Tuple, Dict, Any, Set

import panflute as pf

from .text_manager_inline import (
    NotionInlineElement, 
    Text,
    Annotations,
    InlineElementConverter,
    merge_consecutive_texts,
    convert_code_element,
    convert_math_element
)
from ..utils.debug import debug_decorator
from .base import Manager


class TextManager(Manager):
    """
    Manager for handling inline text elements and converting them to Notion inline elements.
    
    This implementation uses the NotionInlineElement abstraction to handle various inline 
    element types (text, inline equations, code, mentions) with a unified approach.
    """
    
    @classmethod
    def _is_content_token(cls, elem: pf.Element) -> bool:
        """
        Determine if an element is a content token (directly contains text).
        
        Content tokens are elements that can be directly converted to text without
        processing their children.
        
        Args:
            elem: The element to check
            
        Returns:
            True if the element is a content token, False otherwise
        """
        return isinstance(elem, (pf.Str, pf.Space, pf.SoftBreak, pf.LineBreak))
    
    @classmethod
    def _is_formatting_token(cls, elem: pf.Element) -> bool:
        """
        Determine if an element is a formatting token (applies formatting to its content).
        
        Formatting tokens are elements that apply formatting to their children but don't
        directly contain text themselves.
        
        Args:
            elem: The element to check
            
        Returns:
            True if the element is a formatting token, False otherwise
        """
        return isinstance(elem, (pf.Emph, pf.Strong, pf.Strikeout, pf.Link))
    
    @classmethod
    def _get_content_for_token(cls, elem: pf.Element) -> str:
        """
        Extract the plain text content from a content token.
        
        Args:
            elem: The element to extract content from (must be a content token)
            
        Returns:
            The plain text content of the element
            
        Raises:
            ValueError: If the element is not a content token
        """
        if isinstance(elem, pf.Str):
            return elem.text
        elif isinstance(elem, pf.Space):
            return " "
        elif isinstance(elem, (pf.SoftBreak, pf.LineBreak)):
            return "\n"
        
        raise ValueError(f"Not a content token: {type(elem).__name__}")
    
    @classmethod
    def _apply_formatting(cls, elem: pf.Element, current_annotations: Annotations) -> Tuple[Annotations, Optional[str]]:
        """
        Apply formatting from a formatting token to the current annotations.
        
        Args:
            elem: The formatting element to apply
            current_annotations: The current state of annotations
            
        Returns:
            Tuple of (updated annotations, link_url or None)
        """
        new_annotations = current_annotations.copy()
        link_url = None
        
        if isinstance(elem, pf.Emph):
            new_annotations.set_italic(True)
        elif isinstance(elem, pf.Strong):
            new_annotations.set_bold(True)
        elif isinstance(elem, pf.Strikeout):
            new_annotations.set_strikethrough(True)
        elif isinstance(elem, pf.Link):
            # For links, just capture the URL - they're treated as formatting
            link_url = elem.url
            
        return new_annotations, link_url
    
    @classmethod
    def can_convert(cls, elem: pf.Element) -> bool:
        """
        Check if this manager can convert the given element.
        
        Args:
            elem: The element to check
            
        Returns:
            True if this manager can convert the element, False otherwise
        """
        # Can convert content tokens, formatting tokens, and elements with registered converters
        return (
            cls._is_content_token(elem) or 
            cls._is_formatting_token(elem) or
            type(elem) in InlineElementConverter._handlers
        )
    
    @classmethod
    @debug_decorator
    def convert(cls, elements: List[pf.Element]) -> List[NotionInlineElement]:
        """
        Convert a list of panflute elements to Notion inline elements.
        
        This is the main public API method for converting elements.
        
        Args:
            elements: A list of panflute elements to convert
            
        Returns:
            A list of NotionInlineElement objects
        """
        # Convert the elements to Notion inline elements
        result_elements = cls.create_text_elements(elements)
        
        # Merge consecutive text elements with identical formatting
        return cls.merge_consecutive_elements(result_elements)
    
    @classmethod
    def create_text_elements(cls, elements: List[pf.Element], 
                   base_annotations: Optional[Annotations] = None) -> List[NotionInlineElement]:
        """
        Create Notion text elements from a list of panflute elements using stream processing.
        
        This method processes elements as a continuous stream, only creating new elements
        when necessary (formatting changes or specialized element types).
        
        Args:
            elements: A list of panflute elements
            base_annotations: Optional initial annotations to apply to all elements.
                             If None, default annotations will be used.
            
        Returns:
            A list of NotionInlineElement objects with properly inherited annotations
        """
        current_annotations = base_annotations.copy() if base_annotations else Annotations()
        
        # Setup for stream processing
        result_elements = []
        current_text = ""
        current_link = None
        
        # Process all elements in a flattened stream
        cls._process_stream(elements, current_annotations, result_elements, current_text, current_link)
        
        return result_elements
    
    @classmethod
    def _process_stream(
        cls, 
        elements: List[pf.Element], 
        current_annotations: Annotations, 
        result_elements: List[NotionInlineElement], 
        current_text: str = "",
        current_link: Optional[str] = None
    ) -> None:
        """
        Process a stream of elements, accumulating text with the same formatting
        and converting specialized elements as needed.
        
        This method modifies result_elements in place.
        
        Args:
            elements: List of elements to process
            current_annotations: Current formatting state
            result_elements: List to store resulting NotionInlineElement objects (modified in-place)
            current_text: Accumulated text with current formatting
            current_link: URL if processing link content, None otherwise
        """
        for elem in elements:
            if not cls.can_convert(elem):
                # Flush any accumulated text before skipping
                if current_text:
                    text_obj = Text(current_text, annotations=current_annotations.copy(), link=current_link)
                    result_elements.append(text_obj)
                    current_text = ""
                continue
                
            # Try to convert using registered handlers from InlineElementConverter
            element = InlineElementConverter.convert(elem, current_annotations.copy())
            if element:
                # Flush any accumulated text
                if current_text:
                    text_obj = Text(current_text, annotations=current_annotations.copy(), link=current_link)
                    result_elements.append(text_obj)
                    current_text = ""
                
                # Add the converted element
                result_elements.append(element)
                continue
            
            # Handle content tokens (regular text)
            if cls._is_content_token(elem):
                current_text += cls._get_content_for_token(elem)
                
            # Handle formatting tokens (bold, italic, link, etc.)
            elif cls._is_formatting_token(elem):
                # Apply the formatting
                new_annotations, link_url = cls._apply_formatting(elem, current_annotations)
                
                # Use the current link if no new link is provided (we're in a nested formatting)
                if link_url is None:
                    link_url = current_link
                    
                # Determine if formatting changed
                formatting_changed = (
                    new_annotations.bold != current_annotations.bold or
                    new_annotations.italic != current_annotations.italic or
                    new_annotations.strikethrough != current_annotations.strikethrough or
                    new_annotations.code != current_annotations.code or
                    link_url != current_link
                )
                
                # Flush any accumulated text if formatting changed
                if formatting_changed and current_text:
                    text_obj = Text(current_text, annotations=current_annotations.copy(), link=current_link)
                    result_elements.append(text_obj)
                    current_text = ""
                
                # Process children with the new formatting state
                cls._process_stream(
                    elem.content, 
                    new_annotations, 
                    result_elements, 
                    current_text if not formatting_changed else "",
                    link_url
                )
                
                # Reset current_text since it was either flushed or passed to recursive call
                current_text = ""
        
        # Flush any remaining accumulated text
        if current_text:
            text_obj = Text(current_text, annotations=current_annotations.copy(), link=current_link)
            result_elements.append(text_obj)
    
    @classmethod
    def merge_consecutive_elements(cls, elements: List[NotionInlineElement]) -> List[NotionInlineElement]:
        """
        Merge consecutive text elements with identical annotations and link status.
        
        Args:
            elements: A list of NotionInlineElement objects
            
        Returns:
            A list of NotionInlineElement objects with consecutive similar Text objects merged
        """
        return merge_consecutive_texts(elements)

    @classmethod
    @debug_decorator
    def to_dict(cls, elements: List[pf.Element]) -> List[Dict[str, Any]]:
        """
        Convert a list of panflute elements to Notion API-compatible rich_text blocks.
        
        This method implements the public API contract for TextManager, ensuring all
        text elements are returned in the format expected by the Notion API.
        
        Args:
            elements: A list of panflute elements to convert
            
        Returns:
            A list of dictionaries in Notion API format representing rich_text blocks
        """
        # Get NotionInlineElement objects using convert
        inline_elements = cls.convert(elements)
        
        # Convert the internal NotionInlineElement objects to Notion API format
        api_blocks = []
        for element in inline_elements:
            api_blocks.append(element.to_dict())
            
        return api_blocks

