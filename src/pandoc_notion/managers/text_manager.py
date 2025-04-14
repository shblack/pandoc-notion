from typing import List, Optional, Union, Tuple, Dict, Any

import panflute as pf

from .text_manager_inline import (
    NotionInlineElement, 
    Text,
    Annotations,
    InlineElementConverter,
    merge_consecutive_texts
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
            # Handle math (both inline and display) with the registered converter
            if isinstance(elem, pf.Math):
                # Flush any accumulated text
                if current_text:
                    text_obj = Text(current_text, annotations=current_annotations.copy())
                    result_elements.append(text_obj)
                    current_text = ""
                
                # Get the math element from the converter registry
                math_element = InlineElementConverter.convert(elem, current_annotations)
                if math_element:
                    result_elements.append(math_element)
                continue
d_annotations) for child in elem.content]
            
            # Merge consecutive Text elements and return the first one
            # This assumes Strong only contains one piece of content
            merged = merge_consecutive_texts(child_elements)
            if merged and len(merged) == 1:
                return merged[0]
            
            # If we can't merge to single text, return the first child (best effort)
            return child_elements[0] if child_elements else Text("", current_annotations)
            
        elif isinstance(elem, pf.Emph):
            child_annotations = current_annotations.copy()
            child_annotations.set_italic(True)
            
            # Convert children with updated annotations
            child_elements = [cls.convert_element(child, child_annotations) for child in elem.content]
            
            # Merge consecutive Text elements and return the first one
            merged = merge_consecutive_texts(child_elements)
            if merged and len(merged) == 1:
                return merged[0]
            
            # If we can't merge to single text, return the first child (best effort)
            return child_elements[0] if child_elements else Text("", current_annotations)
        
        # Handle basic text elements directly
        elif isinstance(elem, pf.Str):
            return Text(elem.text, annotations=current_annotations.copy())
            
        elif isinstance(elem, pf.Space):
            return Text(" ", annotations=current_annotations.copy())
            
        elif isinstance(elem, (pf.SoftBreak, pf.LineBreak)):
            return Text("\n", annotations=current_annotations.copy())
            
        # Try using a registered converter for this element type
        converter_result = InlineElementConverter.convert(elem, current_annotations)
        if converter_result is not None:
            return converter_result
            
        # If we can't handle it, return empty text
        return Text("", annotations=current_annotations.copy())
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

