"""
Test utilities for Pandoc to Notion conversion.

This module contains the debug decorator and utilities for testing
Pandoc Markdown/AST to Notion JSON conversion.
"""

import functools
from typing import Any, Optional, List, Callable

from tests.conftest_utils import (
    DebugState, format_ast, format_json, format_markdown, is_debug_enabled
)


def debug_p2n(func=None, *, input_is_ast=False, output_is_ast=False):
    """Debug decorator for Pandoc to Notion conversion tests.
    
    Args:
        func: The function to decorate
        input_is_ast: When True, treats the input as AST instead of markdown
        output_is_ast: When True, treats the AST as the final output
    
    Example usage:
    
        @debug_p2n
        def test_pandoc_to_notion():
            markdown = "# Hello World"
            ast = PandocToNotion.parse(markdown)
            notion_json = ast.to_notion()
            debug_p2n.current.input = markdown
            debug_p2n.current.ast = ast
            debug_p2n.current.output = notion_json
            assert notion_json == expected_json

        # For tests that only convert to AST level:
        @debug_p2n(output_is_ast=True)
        def test_pandoc_to_ast():
            markdown = "# Hello World"
            ast = PandocToNotion.parse(markdown)
            debug_p2n.current.input = markdown
            debug_p2n.current.ast = ast
            # No need to set output, decorator will handle it
            assert ast == expected_ast
    """
    def decorator(f):
        # Store current debug state  
        debug_p2n.current = DebugState()
        
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            try:
                # Run test
                result = f(*args, **kwargs)
                
                # Show debug info if enabled
                if is_debug_enabled("DEBUG_TESTS_SHOW_INPUT") and debug_p2n.current.input is not None:
                    if input_is_ast:
                        print("\n=== Input (AST) ===")
                        print(format_ast(debug_p2n.current.input))
                    else:
                        print("\n=== Markdown Input ===")
                        print(format_markdown(debug_p2n.current.input))
                    
                # Only show intermediate AST if it's neither the input nor the output
                show_intermediate = not (input_is_ast or output_is_ast)
                if is_debug_enabled("DEBUG_TESTS_SHOW_AST") and debug_p2n.current.ast is not None and show_intermediate:
                    print("\n=== Intermediate AST ===")
                    print(format_ast(debug_p2n.current.ast))
                
                # If output_is_ast, use AST as output if none was specified
                if output_is_ast and debug_p2n.current.output is None and debug_p2n.current.ast is not None:
                    debug_p2n.current.output = debug_p2n.current.ast
                    
                if is_debug_enabled("DEBUG_TESTS_SHOW_OUTPUT") and debug_p2n.current.output is not None:
                    if output_is_ast:
                        print("\n=== Output (AST) ===")
                        print(format_ast(debug_p2n.current.output))
                    else:
                        print("\n=== Notion JSON Output ===")
                        print(format_json(debug_p2n.current.output))
                    
                return result
                
            except Exception as e:
                # Still show debug info on failure
                print(f"\nTest failed: {str(e)}")
                if is_debug_enabled("DEBUG_TESTS_SHOW_INPUT") and debug_p2n.current.input is not None:
                    if input_is_ast:
                        print("\n=== Input (AST) ===")
                        print(format_ast(debug_p2n.current.input))
                    else:
                        print("\n=== Markdown Input ===")
                        print(format_markdown(debug_p2n.current.input))
                
                # Only show intermediate AST if it's neither the input nor the output
                show_intermediate = not (input_is_ast or output_is_ast)
                if is_debug_enabled("DEBUG_TESTS_SHOW_AST") and debug_p2n.current.ast is not None and show_intermediate:
                    print("\n=== Intermediate AST ===")
                    print(format_ast(debug_p2n.current.ast))
                
                # If output_is_ast, use AST as output if none was specified
                if output_is_ast and debug_p2n.current.output is None and debug_p2n.current.ast is not None:
                    debug_p2n.current.output = debug_p2n.current.ast
                
                if is_debug_enabled("DEBUG_TESTS_SHOW_OUTPUT") and debug_p2n.current.output is not None:
                    if output_is_ast:
                        print("\n=== Output (AST) ===")
                        print(format_ast(debug_p2n.current.output))
                    else:
                        print("\n=== Notion JSON Output ===")
                        print(format_json(debug_p2n.current.output))
                raise
                
            finally:
                # Reset debug state
                debug_p2n.current = DebugState()
                
        return wrapper
    
    # Handle both @debug_p2n and @debug_p2n(input_is_ast=True) usage
    if func is None:
        return decorator
    return decorator(func)

