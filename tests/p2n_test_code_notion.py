"""
Integration tests for code block conversions in pandoc-notion.

Tests proper conversion of Markdown code blocks to Notion code blocks,
including different languages, syntax highlighting, and formatting.
"""
import time
import pytest
from typing import Dict, Any, List, Optional

# Markdown content with various code block types
TEST_CODE_MARKDOWN = '''# Code Block Conversion Tests

## Basic Code Blocks

Plain code block without language:

```
function helloWorld() {
  console.log("Hello, world!");
}
```

Python code block:

```python
def hello_world():
    print("Hello, world!")
    return True
```

JavaScript code block:

```javascript
function calculateTotal(items) {
  return items
    .map(item => item.price * item.quantity)
    .reduce((total, value) => total + value, 0);
}
```

## Multi-line and Special Characters

SQL with special characters:

```sql
SELECT u.name, p.title
FROM users u
JOIN posts p ON u.id = p.user_id
WHERE u.email LIKE '%@example.com'
  AND p.created_at > '2023-01-01';
```

HTML with attributes:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Example Page</title>
</head>
<body>
    <h1 class="title">Hello, World!</h1>
    <p data-test="true">This is a paragraph.</p>
</body>
</html>
```

## Code with Indentation and Line Numbers

Rust with indentation:

```rust
fn main() {
    let mut count = 0;
    
    // Define a closure that increments count
    let mut increment = || {
        count += 1;
        println!("Count is now: {}", count);
    };
    
    // Call the closure
    increment();
    increment();
    
    assert_eq!(count, 2);
}
```

## Formatting and Symbols

Shell/Bash script:

```bash
#!/bin/bash
# This is a comment

echo "Starting backup process..."

# Define backup directory
BACKUP_DIR="/var/backups/$(date '+%Y-%m-%d')"

# Create if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Copy files
cp -r ~/important_files "$BACKUP_DIR"

echo "Backup completed successfully!"
exit 0
```

C++ with templates:

```cpp
#include <iostream>
#include <vector>
#include <string>

template<typename T>
void printVector(const std::vector<T>& vec) {
    std::cout << "Vector contents: ";
    for (const auto& item : vec) {
        std::cout << item << " ";
    }
    std::cout << std::endl;
}

int main() {
    std::vector<int> numbers = {1, 2, 3, 4, 5};
    std::vector<std::string> names = {"Alice", "Bob", "Charlie"};
    
    printVector(numbers);
    printVector(names);
    
    return 0;
}
```

## Code with Special Formatting

JSON data:

```json
{
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "preferences": {
      "theme": "dark",
      "notifications": true
    },
    "roles": ["admin", "editor"]
  },
  "settings": {
    "apiKey": "abc123def456",
    "maxRetries": 3,
    "timeout": 5000
  }
}
```

YAML configuration:

```yaml
version: '3.8'
services:
  webapp:
    image: my-webapp:latest
    ports:
      - "8080:80"
    environment:
      - NODE_ENV=production
      - LOG_LEVEL=info
    volumes:
      - ./data:/app/data
    depends_on:
      - database
  
  database:
    image: postgres:13
    environment:
      - POSTGRES_PASSWORD=secret
      - POSTGRES_USER=admin
      - POSTGRES_DB=myapp
    volumes:
      - db-data:/var/lib/postgresql/data

volumes:
  db-data:
```
'''


@pytest.mark.notion_integration
def test_code_block_conversion(notion_test):
    """
    Test conversion of code blocks with proper rendering and syntax highlighting in Notion.
    
    This test:
    1. Creates a Notion page with various code blocks
    2. Retrieves the page content and extracts code blocks
    3. Verifies all expected code blocks are properly rendered with correct language
    """
    print("[DEBUG] === Test code_block_conversion starting ===")

    # ===== STEP 1: Create a single test page =====
    page_id = notion_test.create_page(
        markdown_content=TEST_CODE_MARKDOWN,
        title=f"Code Block Test Page - {notion_test.test_name}"
    )
    
    # Verify page exists
    page = notion_test.client.client.pages.retrieve(page_id)
    assert page["id"] == page_id, "Page creation failed"
    
    # ===== STEP 2: Retrieve blocks and extract code blocks =====
    # Allow Notion API time to process blocks
    print("[DEBUG] Waiting 1 second before retrieving blocks...")
    time.sleep(1)
    
    # Get all blocks from the page
    blocks_response = notion_test.client.client.blocks.children.list(page_id)
    results = blocks_response["results"]
    
    # Initialize collections for storing code blocks
    code_blocks = []
    heading_texts = []
    
    # ===== STEP 3: Process blocks and extract code blocks =====
    print("[DEBUG] Extracting code blocks from retrieved blocks...")
    for block in results:
        block_type = block.get("type")
        
        # Extract heading texts for context verification
        if block_type == "heading_2" or block_type == "heading_3":
            heading_text = block[block_type].get("rich_text", [])[0].get("plain_text", "")
            if heading_text:
                heading_texts.append(heading_text)
                print(f"[DEBUG] Found heading: {heading_text}")
        
        # Extract code blocks
        if block_type == "code":
            code_content = "".join([rt.get("plain_text", "") for rt in block["code"].get("rich_text", [])])
            language = block["code"].get("language", "plain text")
            
            code_blocks.append({
                "content": code_content,
                "language": language,
                "block_id": block["id"]
            })
            
            print(f"[DEBUG] Found code block with language '{language}' and length {len(code_content)}")
            if len(code_content) < 50:  # Only print short snippets to keep logs clean
                print(f"[DEBUG] Code: {code_content.strip()}")
    
    # ===== STEP 4: Verify code blocks =====
    print(f"\n--- Found {len(code_blocks)} code blocks ---")
    
    # 1. Check total count
    assert len(code_blocks) > 0, "No code blocks found"
    assert len(code_blocks) >= 10, f"Expected at least 10 code blocks, found {len(code_blocks)}"
    
    # 2. Check for expected languages
    languages = [block["language"] for block in code_blocks]
    print(f"Languages found: {languages}")
    
    expected_languages = [
        "plain_text", 
        "python", 
        "javascript", 
        "sql", 
        "html", 
        "rust", 
        "bash", 
        "c++", 
        "json", 
        "yaml"
    ]
    
    for lang in expected_languages:
        # Notion might normalize some language names
        normalized_lang = normalize_language(lang)
        matching_langs = [normalize_language(l) for l in languages]
        
        assert normalized_lang in matching_langs, f"Missing code block for language: {lang}"
    
    # 3. Check for specific code content markers
    expected_code_markers = {
        "python": ["def hello_world", "print("],
        "javascript": ["function calculateTotal", "reduce("],
        "sql": ["SELECT", "FROM users", "JOIN"],
        "html": ["<!DOCTYPE html>", "<html", "<body>"],
        "rust": ["fn main()", "let mut count", "closure"],
        "bash": ["#!/bin/bash", "BACKUP_DIR", "mkdir -p"],
        "c++": ["#include", "template", "std::vector"],
        "json": ["user", "preferences", "roles"],
        "yaml": ["version", "services", "volumes"]
    }
    
    for lang, markers in expected_code_markers.items():
        # Find code block for this language
        norm_lang = normalize_language(lang)
        matching_blocks = [b for b in code_blocks if normalize_language(b["language"]) == norm_lang]
        
        if not matching_blocks:
            assert False, f"No code block found for language {lang}"
            continue
            
        code_content = matching_blocks[0]["content"]
        
        # Check for expected markers in code content
        for marker in markers:
            assert marker in code_content, f"Missing expected code marker '{marker}' in {lang} block"
    
    # 4. Verify context headings
    expected_headings = [
        "Basic Code Blocks",
        "Multi-line and Special Characters",
        "Code with Indentation and Line Numbers",
        "Formatting and Symbols",
        "Code with Special Formatting"
    ]
    
    for heading in expected_headings:
        matching = [h for h in heading_texts if heading in h]
        assert len(matching) > 0, f"Missing expected heading: '{heading}'"
    
    print("[DEBUG] === Test code_block_conversion completed successfully ===")
    
    # Return detailed data for debugging
    return {
        "code_blocks": code_blocks,
        "heading_texts": heading_texts,
        "languages": languages,
        "block_count": len(results),
        "code_block_count": len(code_blocks)
    }


def normalize_language(language: str) -> str:
    """Normalize language name for comparison (Notion may use different forms)."""
    # Convert to lowercase and remove special chars
    normalized = language.lower().replace("+", "plus").replace("#", "sharp")
    
    # Handle common aliases
    aliases = {
        "plain_text": ["plain", "text", "plaintext", "plain text"],
        "javascript": ["js"],
        "python": ["py"],
        "cplus": ["cpp", "c++"],
        "cplusplus": ["cpp", "c++"],
        "bash": ["shell", "sh"],
        "yaml": ["yml"]
    }
    
    # Check if this is an alias
    for main, alias_list in aliases.items():
        if normalized in alias_list:
            return main
    
    return normalized

