from typing import Dict, Any, List, Optional

import panflute as pf

from pandoc_notion.models.code import Code
from pandoc_notion.managers.base import Manager

# Import debug_trace for detailed diagnostics
try:
    from debug import debug_trace
except ImportError:
    # Fallback decorator that does nothing if debug module not found
    def debug_trace(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if kwargs or not args else decorator(args[0])


class CodeManager(Manager):
    """
    Manager for handling code block elements and converting them to Notion Code blocks.
    
    Handles language mapping from pandoc to Notion's supported languages.
    """
    
    # Map from pandoc language identifiers to Notion language identifiers
    # Based on Notion's supported languages as of 2023
    LANGUAGE_MAP = {
        # Common languages with exact matches
        "abap": "abap",
        "arduino": "arduino",
        "bash": "bash",
        "basic": "basic",
        "c": "c",
        "clojure": "clojure",
        "coffeescript": "coffeescript",
        "cpp": "c++",
        "c++": "c++",
        "csharp": "c#",
        "c#": "c#",
        "css": "css",
        "dart": "dart",
        "diff": "diff",
        "docker": "docker",
        "elixir": "elixir",
        "elm": "elm",
        "erlang": "erlang",
        "flow": "flow",
        "fortran": "fortran",
        "fsharp": "f#",
        "f#": "f#",
        "gherkin": "gherkin",
        "glsl": "glsl",
        "go": "go",
        "graphql": "graphql",
        "groovy": "groovy",
        "haskell": "haskell",
        "html": "html",
        "java": "java",
        "javascript": "javascript",
        "js": "javascript",
        "json": "json",
        "julia": "julia",
        "kotlin": "kotlin",
        "latex": "latex",
        "less": "less",
        "lisp": "lisp",
        "livescript": "livescript",
        "lua": "lua",
        "makefile": "makefile",
        "markdown": "markdown",
        "markup": "markup",
        "matlab": "matlab",
        "mermaid": "mermaid",
        "nix": "nix",
        "objective-c": "objective-c",
        "ocaml": "ocaml",
        "pascal": "pascal",
        "perl": "perl",
        "php": "php",
        "powershell": "powershell",
        "prolog": "prolog",
        "protobuf": "protobuf",
        "python": "python",
        "py": "python",
        "r": "r",
        "reason": "reason",
        "ruby": "ruby",
        "rust": "rust",
        "sass": "sass",
        "scala": "scala",
        "scheme": "scheme",
        "scss": "scss",
        "shell": "shell",
        "sql": "sql",
        "swift": "swift",
        "typescript": "typescript",
        "ts": "typescript",
        "vb": "visual basic",
        "vbnet": "visual basic",
        "verilog": "verilog",
        "vhdl": "vhdl",
        "xml": "xml",
        "yaml": "yaml",
        
        # Common aliases or special cases
        "sh": "bash",
        "zsh": "bash",
        "console": "shell",
        "terminal": "shell",
        "jsx": "javascript",
        "tsx": "typescript",
        "yml": "yaml",
        "plaintext": "plain text",
        "text": "plain text",
        "txt": "plain text"
    }
    
    @classmethod
    # Removed @debug_decorator
    def can_convert(cls, elem: pf.Element) -> bool:
        """Check if the element is a code block that can be converted."""
        return isinstance(elem, pf.CodeBlock)
    
    @classmethod
    @debug_trace()
    def convert(cls, elem: pf.Element) -> List[Code]:
        """
        Convert a panflute code block element to a Notion Code object.
        
        Args:
            elem: A panflute CodeBlock element
            
        Returns:
            A list containing a single Notion Code object
        """
        if not isinstance(elem, pf.CodeBlock):
            raise ValueError(f"Expected CodeBlock element, got {type(elem).__name__}")
        
        # Get code content
        code_content = elem.text
        
        # Get language and map it to Notion's language identifier
        language = cls._map_language(elem.classes[0] if elem.classes else None)
        
        # Check for caption/filename in attributes
        caption = elem.attributes.get("caption") or elem.attributes.get("filename")
        
        # Create the Code object
        return [Code(code_content, language, caption)]
    
    @classmethod
    @debug_trace()
    def to_dict(cls, elem: pf.Element) -> List[Dict[str, Any]]:
        """
        Convert a panflute code block element to a Notion API dictionary.
        
        Args:
            elem: A panflute CodeBlock element
            
        Returns:
            A list containing a single Notion API code block dictionary
        """
        # Convert to Code objects, then convert each to dictionary
        code_blocks = cls.convert(elem)
        return [code_block.to_dict() for code_block in code_blocks]
        
        # Note: The lines below were duplicated/unreachable in the original file and have been removed
        # # Check for caption/filename in attributes
        # caption = elem.attributes.get("caption") or elem.attributes.get("filename")
        # # Create the internal Code object and immediately convert it to its API dictionary representation.
        # return [Code(code_content, language, caption).to_dict()]
    
    @classmethod
    def _map_language(cls, language: Optional[str]) -> str:
        """
        Map a pandoc language identifier to a Notion language identifier.
        
        Args:
            language: A pandoc language identifier (or None)
            
        Returns:
            A Notion language identifier, defaulting to "plain text" if not found
        """
        if not language:
            return "plain text"
        
        # Convert to lowercase for case-insensitive matching
        language_lower = language.lower()
        
        # Try to find a match in our language map
        return cls.LANGUAGE_MAP.get(language_lower, "plain text")
    
    @classmethod
    def create_code_block(cls, code: str, language: str = "plain text", caption: Optional[str] = None) -> Code:
        """
        Create a code block from code content and language.
        
        Args:
            code: The code content
            language: Programming language (will be mapped to Notion's supported languages)
            caption: Optional caption or filename
            
        Returns:
            A Notion Code object
        """
        mapped_language = cls._map_language(language)
        return Code(code, mapped_language, caption)

