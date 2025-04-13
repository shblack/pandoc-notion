from typing import List, Optional, Union, Tuple, Dict, Any

import panflute as pf

from ..models.text import (
    NotionInlineElement, 
    Text,
    Annotations,
    InlineElementConverter,
    merge_consecutive_texts
)
from ..utils.debug import debug_decorator
from .base import Manager
from .equation_manager import EquationManager


class TextManager(Manager):
    """
    Manager for handling inline text elements and converting them to Notion inline elements.
    
    This implementation uses the NotionInlineElement abstraction to handle various inline 
    element types (text, inline equations, code, mentions) with a unified approach.
    """
    
    @classmethod
    @debug_decorator
    def can_convert(cls, elem: pf.Element) -> bool:
        """Check if the element is an inline element that can be converted."""
        # Explicitly avoid handling block-level elements
        if isinstance(elem, (pf.BlockQuote, pf.Para, pf.Header)):
            return False
        
        # Include basic text elements
        if isinstance(elem, (pf.Str, pf.SoftBreak, pf.LineBreak, pf.Space, pf.Link)):
            return True
            
        # Include formatting elements
        if isinstance(elem, (pf.Emph, pf.Strong)):
            return True
            
        # Include inline math elements
        if isinstance(elem, pf.Math) and elem.format == 'InlineMath':
            return True
            
        # Check if we have a registered handler for this element type
        if InlineElementConverter.convert(elem) is not None:
            return True
            
        return False
    
    @classmethod
    @debug_decorator
    def convert(cls, elem: Union[pf.Element, List[pf.Element]]) -> List[NotionInlineElement]:
        """
        Convert a panflute element or list of elements to Notion inline element objects.
        
        Args:
            elem: A panflute element or list of elements
            
        Returns:
            A list of Notion inline element objects
        """
        # If we got a list, process each element and collect results
        if isinstance(elem, list):
            # Create text elements using our internal model
            notion_elements = cls.create_text_elements(elem)
                
            # Merge consecutive text elements with same formatting
            merged_elements = cls.merge_consecutive_elements(notion_elements)
            
            return merged_elements
        else:
            # Single element conversion - return result as a list
            result = []
            cls._process_stream([elem], Annotations(), result)
            return result

    @classmethod
    def _is_content_token(cls, elem: pf.Element) -> bool:
        """
        Determine if an element is a content token (directly contains text).
        
        Content tokens: Str, Space, SoftBreak, LineBreak, Math(InlineMath)
        """
        return isinstance(elem, (pf.Str, pf.Space, pf.SoftBreak, pf.LineBreak)) or \
               (isinstance(elem, pf.Math) and elem.format == 'InlineMath')
    
    @classmethod
    def _is_formatting_token(cls, elem: pf.Element) -> bool:
        """
        Determine if an element is a formatting token (modifies text appearance).
        
        Formatting tokens: Emph, Strong
        """
        return isinstance(elem, (pf.Emph, pf.Strong))
    
    @classmethod
    def _get_content_for_token(cls, elem: pf.Element) -> str:
        """Extract the text content from a content token."""
        if isinstance(elem, pf.Str):
            return elem.text
        elif isinstance(elem, pf.Space):
            return " "
        elif isinstance(elem, (pf.SoftBreak, pf.LineBreak)):
            return "\n"
        elif isinstance(elem, pf.Math) and elem.format == 'InlineMath':
            # Use EquationManager's conversion logic for consistency
            return EquationManager._convert_latex_to_katex(elem.text)
        raise ValueError(f"Not a content token: {type(elem).__name__}")
    
    @classmethod
    def _apply_formatting(cls, elem: pf.Element, current_annotations: Annotations) -> Tuple[Annotations, bool]:
        """
        Apply formatting from a formatting token to the current annotations.
        
        Returns:
            Tuple of (updated annotations, formatting_changed)
        """
        new_annotations = current_annotations.copy()
        formatting_changed = False
        
        if isinstance(elem, pf.Emph):
            formatting_changed = new_annotations.set_italic(True)
        elif isinstance(elem, pf.Strong):
            formatting_changed = new_annotations.set_bold(True)
            
        return new_annotations, formatting_changed
    
    @classmethod
    @debug_decorator
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
        
        # Process all elements in a flattened stream
        cls._process_stream(elements, current_annotations, result_elements, current_text)
        
        return result_elements
    
    @classmethod
    def _process_stream(
        cls, 
        elements: List[pf.Element], 
        current_annotations: Annotations, 
        result_elements: List[NotionInlineElement], 
        current_text: str = ""
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
        """
        for elem in elements:
            if not cls.can_convert(elem):
                # Flush any accumulated text before skipping
                if current_text:
                    text_obj = Text(current_text, annotations=current_annotations.copy())
                    result_elements.append(text_obj)
                    current_text = ""
                continue
                
            # Try to convert using registered handlers
            element = InlineElementConverter.convert(elem, current_annotations.copy())
            if element:
                # Flush any accumulated text
                if current_text:
                    text_obj = Text(current_text, annotations=current_annotations.copy())
                    result_elements.append(text_obj)
                    current_text = ""
                
                # Add the converted element
                result_elements.append(element)
                continue
            
            # Handle inline math specially
            if isinstance(elem, pf.Math) and elem.format == 'InlineMath':
                # Flush any accumulated text
                if current_text:
                    text_obj = Text(current_text, annotations=current_annotations.copy())
                    result_elements.append(text_obj)
                    current_text = ""
                
                # Create equation text with equation annotation
                equation_content = cls._get_content_for_token(elem)
                equation_annotations = current_annotations.copy()
                equation_annotations.set_equation(True)
                result_elements.append(Text(equation_content, annotations=equation_annotations))
                continue
                
            # Handle content tokens (regular text)
            if cls._is_content_token(elem):
                current_text += cls._get_content_for_token(elem)
                
            # Handle formatting tokens (bold, italic, etc.)
            elif cls._is_formatting_token(elem):
                # Apply the formatting and check if it changed
                new_annotations, formatting_changed = cls._apply_formatting(elem, current_annotations)
                
                # Flush any accumulated text if formatting changed
                if formatting_changed and current_text:
                    text_obj = Text(current_text, annotations=current_annotations.copy())
                    result_elements.append(text_obj)
                    current_text = ""
                
                # Process children with the new formatting state
                cls._process_stream(
                    elem.content, 
                    new_annotations, 
                    result_elements, 
                    current_text if not formatting_changed else ""
                )
                
                # Reset current_text since it was either flushed or passed to recursive call
                current_text = ""
        
        # Flush any remaining accumulated text
        if current_text:
            text_obj = Text(current_text, annotations=current_annotations.copy())
            result_elements.append(text_obj)
    
    @classmethod
    @debug_decorator
    def _process_inline_element(cls, elem: pf.Element, 
               base_annotations: Optional[Annotations] = None) -> Union[NotionInlineElement, List[NotionInlineElement]]:
        """
        Process a single panflute inline element to a Notion inline element or list of elements.
        
        This is an internal method used by create_text_blocks for processing individual elements.
        
        Args:
            elem: The element to convert
            base_annotations: Annotations from parent elements to be inherited.
            
        Returns:
            Either a single NotionInlineElement or a list of NotionInlineElements
        """
        current_annotations = base_annotations.copy() if base_annotations else Annotations()
        
        # Try to convert using registered handlers
        element = InlineElementConverter.convert(elem, current_annotations.copy())
        if element:
            return element
        
        # Handle inline math elements
        elif isinstance(elem, pf.Math) and elem.format == 'InlineMath':
            equation_content = cls._get_content_for_token(elem)
            equation_annotations = current_annotations.copy()
            equation_annotations.set_equation(True)
            return Text(equation_content, annotations=equation_annotations)
            
        # Content tokens get a direct conversion
        elif cls._is_content_token(elem):
            content = cls._get_content_for_token(elem)
            return Text(content, annotations=current_annotations)
            
        # Formatting tokens process their children
        elif cls._is_formatting_token(elem):
            result_elements = []
            new_annotations, _ = cls._apply_formatting(elem, current_annotations)
            
            # Process children with new annotations
            cls._process_stream(elem.content, new_annotations, result_elements)
            return result_elements
            
        else:
            raise ValueError(f"TextManager cannot convert element of type {type(elem).__name__}")
    
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

