# Mathematical Equations: Pandoc AST to Notion API Conversion Analysis

## Overview

This document analyzes the differences between how mathematical equations are represented in Pandoc's Abstract Syntax Tree (AST) versus Notion's API format. The current implementation doesn't correctly convert inline equations from Pandoc's format to Notion's expected API structure.

## Current Codebase Structure

The current codebase includes several components for handling equations:

1. **Equation Model (`models/equation.py`)**: 
   - `Equation` class for block-level equations
   - `InlineEquation` helper class for inline equations

2. **EquationManager (`managers/equation_manager.py`)**: Converts Pandoc math elements to Notion format

3. **Text Model (`models/text.py`)**: Used for inline text including equation formatting

## Pandoc AST Representation

In Pandoc's AST (as seen in `panflute.yaml`), math elements are represented as:

```yaml
- t: Math
  c:
  - t: InlineMath  # or DisplayMath for block equations
  - a + b = c      # The actual equation content
```

For example, an inline equation like `$a + b = c$` appears in the AST as:

```yaml
- t: Math
  c:
  - t: InlineMath
  - a + b = c
```

## Notion API Representation

In Notion's API (as seen in `notion.json`), inline equations need to be separate `rich_text` objects with a specific structure:

```json
{
  "type": "equation",
  "equation": {
    "expression": "a\u2005+\u2005b\u2004=\u2004c"
  },
  "annotations": {
    "bold": false,
    "italic": false,
    "strikethrough": false,
    "underline": false,
    "code": false
  },
  "plain_text": "a\u2005+\u2005b\u2004=\u2004c"
}
```

Key observations:
1. Inline equations have `"type": "equation"` (not to be confused with block-level equations)
2. Mathematical spacing uses specific Unicode characters:
   - `\u2005` (four-per-em space) for operation spacing
   - `\u2004` (three-per-em space) for equality spacing
3. The same expression appears in both the `expression` field and the `plain_text` field
4. Standard annotation fields must be included and set to false

## Current Implementation Issues

The current implementation has several issues:

1. **InlineEquation Implementation**: The current `InlineEquation.create_text()` method creates a `Text` object with `code` formatting:

   ```python
   # Current implementation in InlineEquation
   text = Text(expression)
   text.annotations.code = True
   return text
   ```

   This creates a code-formatted text block instead of a proper Notion equation object.

2. **EquationManager Conversion**: The current convert method branches based on equation type:

   ```python
   # Current implementation in EquationManager
   if elem.format == 'DisplayMath':
       # Block equation (correct)
       return Equation(expression, equation_number)
   else:
       # Inline equation (incorrect)
       return InlineEquation.create_text(expression)
   ```

   For inline equations, it returns a code-formatted Text object instead of a proper equation object.

## Required Changes

The key changes needed are:

1. **Update InlineEquation Class**: Modify to create proper equation objects for inline math:

   ```python
   @staticmethod
   def create_text(expression: str) -> Dict[str, Any]:
       """Create a proper equation rich_text object."""
       expression = format_spacing(expression)  # Apply proper spacing
       
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
               "code": False
           },
           "plain_text": expression
       }
   ```

2. **Integrate with Rich Text Processing**: Ensure the equation objects are properly integrated into the rich_text array instead of being converted to plain text or code blocks.

## Detailed Implementation Strategy

1. **Identify the Specific Issues** in `EquationManager.convert()` and `InlineEquation.create_text()`:
   - Currently, inline equations are returned as Text objects with code formatting
   - Instead, they should be proper equation objects like block equations

2. **Implement a New Method** for creating inline equation objects, using the existing Annotations class:
   ```python
   def create_inline_equation_object(expression: str) -> Dict[str, Any]:
       """Create a proper Notion equation object for inline equations."""
       from ..models.text import Annotations
       
       
       # Use the existing Annotations class for consistent structure
       annotations = Annotations()  # All defaults are False, color="default"
       
       return {
           "type": "equation",
           "equation": {
               "expression": formatted_expr
           },
           "annotations": annotations.to_dict(),
           "plain_text": formatted_expr
       }
   ```

3. **Update the Conversion Method** in EquationManager:
   ```python
   @classmethod
   def convert(cls, elem: pf.Element) -> Union[Equation, Dict[str, Any]]:
       # Extract expression and process it
       expression = elem.text
       expression = cls._convert_latex_to_katex(expression)
       
       if elem.format == 'DisplayMath':
           # It's a display equation (block)
           equation_number = cls._extract_equation_number(expression)
           return Equation(expression, equation_number)
       else:
           # It's an inline equation
           return cls.create_inline_equation_object(expression)
   ```

4. **Handle Text Integration**: Ensure inline equation objects are properly integrated into paragraph rich_text arrays.

## Using Text and Annotations Classes

We can still utilize the existing Text and Annotations classes for consistency:

```python

class InlineEquation:
    """Helper class for inline equations in Notion format."""
    
    @staticmethod
    def create_equation_dict(expression: str) -> Dict[str, Any]:
        """
        Create a proper Notion equation object dictionary.
        
        Uses the existing Annotations class for consistency with the rest
        of the codebase.
        
        Args:
            expression: LaTeX/KaTeX expression
            
        Returns:
            Dictionary representing a Notion equation object
        """
        from ..models.text import Annotations
        
        # Format the expression with proper spacing
        formatted_expr = format_spacing(expression)
        
        # Create annotations with defaults
        annotations = Annotations()
        
        return {
            "type": "equation",
            "equation": {
                "expression": formatted_expr
            },
            "annotations": annotations.to_dict(),
            "plain_text": formatted_expr
        }
```

This approach uses the existing Annotations class to ensure consistency with how other text elements are handled, without requiring any modification to the Text class itself.
