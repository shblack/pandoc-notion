# pandoc-notion

A Python library for converting between Markdown and Notion blocks with proper hierarchical structure handling.

## Features

- Convert Markdown content to Notion blocks
- Preserve nested structures like lists and sub-lists
- Handle rich text, headings, code blocks, and other Notion block types
- Full support for Notion's block hierarchies

## Installation

```bash
pip install pandoc-notion
```

## Basic Usage

### Converting Markdown to Notion Blocks

```python
from pandoc_notion import filter_markdown_to_notion

# Convert markdown to Notion blocks
markdown_content = """
# Heading 1

This is a paragraph with **bold** and *italic* text.

- List item 1
- List item 2
  - Nested list item
  - Another nested item
"""

notion_blocks = filter_markdown_to_notion(markdown_content)
print(notion_blocks)
```

### Command Line Usage

You can also use the library from the command line:

```bash
# Convert a markdown file to Notion blocks
pandoc-notion input.md -o output.json

# Or pipe content through stdin
cat input.md | pandoc-notion > output.json
```

## Advanced Usage

For more advanced usage including customization options, handling of complex block types, and integration with the Notion API, please refer to the documentation.

## Development

### Setting up the development environment

```bash
# Clone the repository
git clone https://github.com/yourusername/pandoc-notion.git
cd pandoc-notion

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
```

## License

MIT

