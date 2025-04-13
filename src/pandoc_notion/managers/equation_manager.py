from typing import Any, Union, Dict, List

import panflute as pf

from ..models.equation import Equation, InlineEquation
from ..models.text import Text
from .base import Manager


class EquationManager(Manager):
    """
    Manager for handling equation elements and converting them to Notion Equation blocks.
    
    Handles both display equations (block-level) and inline equations.
    """
    
    # Map for LaTeX to KaTeX conversions if needed
    LATEX_TO_KATEX = {
        # LaTeX commands not supported in KaTeX or with different syntax
        # This is not an exhaustive list, but covers common cases
        r'\eqref': r'\ref',  # KaTeX doesn't support \eqref
    }
    
    @classmethod
    def can_convert(cls, elem: pf.Element) -> bool:
        """Check if the element is a math element that can be converted."""
        return isinstance(elem, pf.Math)
    
    @classmethod
    def convert(cls, elem: pf.Element) -> Union[Equation, Dict[str, Any]]:
        """
        Convert a panflute math element to a Notion Equation object or equation dictionary.
        
        Args:
            elem: A panflute Math element
            
        Returns:
            A Notion Equation object for display math or equation dictionary for inline math
        """
        if not isinstance(elem, pf.Math):
            raise ValueError(f"Expected Math element, got {type(elem).__name__}")
        
        # Extract the math expression
        expression = elem.text
        
        # Apply any necessary LaTeX to KaTeX conversions
        expression = cls._convert_latex_to_katex(expression)
        
        # Extract equation number if present
        equation_number = cls._extract_equation_number(expression)
        
        # Check if it's a display equation or an inline equation
        if elem.format == 'DisplayMath':
            # It's a display equation (block)
            return Equation(expression, equation_number)
        else:
            # It's an inline equation
            return InlineEquation.create_text(expression)
    
    @classmethod
    def _convert_latex_to_katex(cls, expression: str) -> str:
        """
        Convert LaTeX expression to KaTeX syntax where needed.
        
        Args:
            expression: LaTeX expression
            
        Returns:
            Equivalent KaTeX expression
        """
        result = expression
        
        # Replace LaTeX commands with KaTeX equivalents
        for latex_cmd, katex_cmd in cls.LATEX_TO_KATEX.items():
            result = result.replace(latex_cmd, katex_cmd)
        
        return result
    
    @classmethod
    def _extract_equation_number(cls, expression: str) -> Union[str, None]:
        """
        Extract equation number from LaTeX expression if present.
        
        Looks for \\tag{} or \\label{} commands to determine equation number.
        
        Args:
            expression: LaTeX expression
            
        Returns:
            Equation number as string, or None if not found
        """
        # Look for explicit \tag{} which sets the equation number
        tag_start = expression.find(r'\tag{')
        if tag_start >= 0:
            tag_end = expression.find('}', tag_start)
            if tag_end > tag_start:
                return expression[tag_start + 6:tag_end]  # +6 to skip \tag{
        
        # Look for \label{} which may be used for equation referencing
        label_start = expression.find(r'\label{')
        if label_start >= 0:
            label_end = expression.find('}', label_start)
            if label_end > label_start:
                return expression[label_start + 7:label_end]  # +7 to skip \label{
        
        # No explicit number found
        return None
    
    @classmethod
    def create_block_equation(cls, expression: str, equation_number: str = None) -> Equation:
        """
        Create a block equation from a LaTeX expression.
        
        Args:
            expression: LaTeX expression
            equation_number: Optional equation number or identifier
            
        Returns:
            A Notion Equation block
        """
        # Apply any LaTeX to KaTeX conversions
        expression = cls._convert_latex_to_katex(expression)
        return Equation(expression, equation_number)
    
    @classmethod
    def create_inline_equation(cls, expression: str) -> Dict[str, Any]:
        """
        Create an inline equation from a LaTeX expression.
        
        Args:
            expression: LaTeX expression
            
        Returns:
            A dictionary with the Notion API format for inline equations
        """
        # Apply any LaTeX to KaTeX conversions
        expression = cls._convert_latex_to_katex(expression)
        return InlineEquation.create_text(expression)
