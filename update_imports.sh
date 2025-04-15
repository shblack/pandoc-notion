#!/bin/bash

# Script to update debug_trace imports to python_debug
# Usage: ./update_imports.sh

# List of files to process
files=(
    "src/pandoc_notion/filter.py"
    "src/pandoc_notion/managers/text_manager.py"
    "src/pandoc_notion/managers/registry_mixin.py"
    "src/pandoc_notion/managers/list_manager.py"
    "src/pandoc_notion/managers/quote_manager.py"
    "src/pandoc_notion/managers/paragraph_manager.py"
    "src/pandoc_notion/managers/code_manager.py"
    "src/pandoc_notion/managers/heading_manager.py"
)

# Function to process each file
process_file() {
    file="$1"
    echo "Processing $file..."
    
    # Create backup
    cp "$file" "${file}.bak"
    
    # Remove try/except block for debug imports
    perl -i -0pe 's/try:\s*\n\s*from debug import debug_trace\s*\nexcept ImportError:\s*\n\s*# Fallback decorator that does nothing if debug module not found\s*\n\s*def debug_trace\(\*args, \*\*kwargs\):\s*\n\s*def decorator\(func\):\s*\n\s*return func\s*\n\s*return decorator if kwargs or not args else decorator\(args\[0\]\)/from python_debug import debug_trace/gs' "$file"
    
    # Handle other variations of the import pattern if not caught by the above
    perl -i -pe 's/from debug import debug_trace/from python_debug import debug_trace/g' "$file"
}

# Process each file
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        process_file "$file"
        echo "Updated $file"
    else
        echo "Warning: $file not found"
    fi
done

echo "Done! Old files backed up with .bak extension"

