# Notion Markdown Tool

A utility for converting markdown to Notion blocks and interacting with the Notion API.

## Currently Supported Features

### Block Types
- Paragraphs
- Headings (H1, H2, H3)
- Code Blocks (with language syntax highlighting)
- Quotes
- Bulleted Lists
- Numbered Lists
- Equations (inline and block)

### Text Formatting
- Bold
- Italic
- Strikethrough
- Code inline
- Links

### Operations
- Convert markdown to Notion blocks
- Create pages from markdown
- Append markdown content to existing pages

## Planned Interface

```python
# Python API
notion = NotionMarkdown(auth_token)
page_id = notion.create_page("document.md", parent_id="parent_page_id")
notion.append_to_page(page_id, "more_content.md")

# Command Line
notion-md create document.md --parent parent_page_id
notion-md append page_id more_content.md
```

## Implementation Steps
1. Create the markdown to Notion block converter
2. Add Notion API integration
3. Build command-line interface
4. Add support for additional block types (images, tables, etc.)

