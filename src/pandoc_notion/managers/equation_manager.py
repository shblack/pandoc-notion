from typing import Any, Dict, List, Optional

import panflute as pf

from ..models.equation import Equation
from ..utils.debug import debug_decorator
from .base import Manager


class EquationManager(Manager):
    """
    Manager for handling block-level equation elements and converting them to Notion Equation blocks.
    
    Only handles display math equations (block-level). Inline equations are handled by TextManager.
    """
    
    # Map for LaTeX to KaTeX conversions if needed
    LATEX_TO_KATEX = {
        # LaTeX commands not supported in KaTeX or with different syntax
        # This is not an exhaustive list, but covers common cases
        r'\eqref': r'\ref',  # KaTeX doesn't support \eqref
    }
    
    @classmethod
    @debug_decorator
    def can_convert(cls, elem: pf.Element) -> bool:
        """Check if the element is a display math element that can be converted."""
        return isinstance(elem, pf.Math) and elem.format == 'DisplayMath'
    
    @classmethod
    @debug_decorator
    def convert(cls, elem: pf.Element) -> List[Equation]:
        """
        Convert a panflute display math element to a Notion Equation block object.

        Only handles display equations (block-level).

        Args:
            elem: A panflute Math element with format 'DisplayMath'

        Returns:
            A list containing a single Notion Equation object
        """
        if not isinstance(elem, pf.Math) or elem.format != 'DisplayMath':
            raise ValueError(f"Expected Math element with DisplayMath format, got {type(elem).__name__} with format {getattr(elem, 'format', 'unknown')}")

        # Extract the math expression
        expression = elem.text

        # Apply any necessary LaTeX to KaTeX conversions
        expression = cls._convert_latex_to_katex(expression)

        # Extract equation number if present
        equation_number = cls._extract_equation_number(expression)

        # Create and return the Equation object
        return [Equation(expression, equation_number)]
    
    @classmethod
    @debug_decorator
    def to_dict(cls, elem: pf.Element) -> List[Dict[str, Any]]:
        """
        Convert a panflute display math element to a Notion API-level block dictionary.

        Only handles display equations (block-level).

        Args:
            elem: A panflute Math element with format 'DisplayMath'

        Returns:
            A list containing a single dictionary representing the Notion API block for display math
        """
        # Convert to Equation objects, then convert each to dictionary
        equations = cls.convert(elem)
        return [equation.to_dict() for equation in equations]
    
    @classmethod
    def _convert_latex_to_katex(cls, expression: str) -> str:
        """
        Convert LaTeX expressions to KaTeX equivalent.
        
        Notion uses KaTeX for rendering equations, which has slightly different
        syntax than LaTeX in some cases. This method applies necessary conversions.
        
        Args:
            expression: LaTeX expression
            
        Returns:
            Converted expression compatible with KaTeX
        """
        result = expression
        
        # Replace LaTeX commands with KaTeX equivalents
        for latex_cmd, katex_cmd in cls.LATEX_TO_KATEX.items():
            result = result.replace(latex_cmd, katex_cmd)
        
        return result
    
    @classmethod
    def _extract_equation_number(cls, expression: str) -> Optional[str]:
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
    def create_block_equation(cls, expression: str, equation_number: Optional[str] = None) -> Equation:
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

