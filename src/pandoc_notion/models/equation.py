from typing import Dict, Any, Optional

from .base import Block
from .paragraph import Paragraph
from .text import Text


class Equation(Block):
    """
    Represents an equation block in Notion.
    
    Notion supports equations using KaTeX syntax.
    This class handles block equations (displayed on their own line).
    For inline equations, use TextManager with appropriate formatting.
    """
    
    def __init__(self, expression: str, equation_number: Optional[str] = None):
        """
        Initialize an equation block.
        
        Args:
            expression: The LaTeX/KaTeX expression for the equation
            equation_number: Optional equation number or identifier
        """
        super().__init__("equation")
        self.expression = expression
        self.equation_number = equation_number
        
        # Clean up the expression
        self.expression = self._sanitize_expression(self.expression)
    
    def _sanitize_expression(self, expr: str) -> str:
        """
        Clean up LaTeX expression for KaTeX rendering.
        
        Args:
            expr: Raw LaTeX expression
            
        Returns:
            Sanitized expression for KaTeX
        """
        # Remove common LaTeX environment delimiters if present
        expr = expr.strip()
        if expr.startswith(r'\begin{equation}') and expr.endswith(r'\end{equation}'):
            expr = expr[len(r'\begin{equation}'):-len(r'\end{equation}')].strip()
        elif expr.startswith(r'\begin{align}') and expr.endswith(r'\end{align}'):
            expr = expr[len(r'\begin{align}'):-len(r'\end{align}')].strip()
        elif expr.startswith(r'\begin{aligned}') and expr.endswith(r'\end{aligned}'):
            expr = expr[len(r'\begin{aligned}'):-len(r'\end{aligned}')].strip()
        elif expr.startswith(r'\begin{gather}') and expr.endswith(r'\end{gather}'):
            expr = expr[len(r'\begin{gather}'):-len(r'\end{gather}')].strip()
        
        # Remove \label{} commands as KaTeX doesn't support them
        # This is a simple approach - a more robust solution would use regex
        if r'\label{' in expr:
            parts = expr.split(r'\label{')
            expr = parts[0]
            for part in parts[1:]:
                if '}' in part:
                    expr += part.split('}', 1)[1]
        
        return expr
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the equation to a Notion API dictionary representation."""
        result = {
            "object": "block",
            "type": self.block_type,
            "equation": {
                "expression": self.expression
            }
        }
        
        # If equation number is present, it has to be handled differently
        # since Notion doesn't natively support equation numbers
        # We could add a paragraph after the equation with the number,
        # but that would be handled at a higher level during document assembly
        
        return result
    
    def create_numbered_blocks(self) -> list:
        """
        Create a list of blocks to represent a numbered equation.
        
        Since Notion doesn't natively support equation numbers, this method
        returns both the equation block and a paragraph block with the number.
        
        Returns:
            A list containing [equation_block, optional_number_block]
        """
        blocks = [self]
        
        # If we have an equation number, add a right-aligned paragraph with it
        if self.equation_number:
            # Create a paragraph with right-aligned text for the equation number
            number_text = Text(f"({self.equation_number})")
            number_para = Paragraph([number_text])
            # TODO: Add right alignment when Paragraph supports it
            # For now, the number will appear without special alignment
            blocks.append(number_para)
        
        return blocks
    
    def __str__(self) -> str:
        """String representation of the equation for debugging."""
        expr_preview = self.expression[:30]
        if len(expr_preview) < len(self.expression):
            expr_preview += "..."
        number_str = f", number={self.equation_number}" if self.equation_number else ""
        return f"Equation({expr_preview}{number_str})"


class InlineEquation:
    """
    Helper class for inline equations.
    
    Notion represents inline equations as rich_text objects with type 'equation'.
    This class helps create the appropriate dictionary structure for inline equations.
    """
    
    @staticmethod
    def create_text(expression: str) -> Dict[str, Any]:
        """
        Create a dictionary representing an inline equation for Notion.
        
        Args:
            expression: LaTeX/KaTeX expression
            
        Returns:
            A dictionary with the Notion API format for inline equations
        """
        # Clean the expression similar to block equations
        expression = expression.strip()
        
        # Remove surrounding $ symbols if present, as Notion doesn't need them
        if expression.startswith('$') and expression.endswith('$'):
            expression = expression[1:-1]
        
        # Create the proper equation dictionary structure
        return {
            "type": "equation",
            "equation": {
                "expression": expression
            },
            "annotations": {
                "bold": False,
                "italic": False,
                "strikethrough": False,
                "underline": False,
                "code": False,
                "color": "default"
            },
            "plain_text": expression
        }

