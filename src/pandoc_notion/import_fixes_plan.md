# Import Fixes Plan

## Package Structure Analysis
1. Project contains two complementary packages:
   - `pandoc_notion`: Markdown → Notion conversion
   - `notion_pandoc`: Notion → Markdown conversion
   - Shared `debug` module via symlink to `../../common/debug`

2. Current Issues:
   - Circular dependency between packages
   - Import issues with shared debug module
   - Inconsistent import paths

## Critical Issues
1. Fix debug module imports:
   - Use proper absolute imports for debug module (not relative imports)
   - Replace try/except blocks with consistent import patterns
   - Keep shared debug module functionality but fix import statements

2. Fix Critical Circular Import:
   - ISSUE: markdown_converter.py shouldn't import from notion_pandoc
   - SOLUTION:
     a. Create a proper interface boundary between packages
     b. Move shared code to a common package
     c. Ensure each package can function independently

## Proposed Resolution Steps
1. Package Independence:
   - Separate the packages completely
   - Move shared code to a new package (e.g., `notion_commons`)
   - Maintain shared debug module but with proper imports

2. Immediate Fixes:
   a. In tools hierarchy:
      - Move markdown_converter.py to higher-level directory (DONE)
      - Create proper interface for cross-package functionality
   b. Debug module:
      - Keep the symlinked debug module (it's intentional)
      - Fix imports to use absolute paths, e.g., `from debug.debug_trace import debug_trace`
      - When running as script, ensure debug module is in PYTHONPATH
   c. Update class relationships:
      - Ensure no cross-package inheritance
      - Use composition over inheritance if needed
## File Review Status

### PROCESSED:
- [x] filter.py (partially - fixed debug_trace import but needs more work)
- [x] tools/markdown_converter.py (moved to higher-level directory)
- [x] __init__.py (fixed debug imports and removed markdown_converter imports)
- [x] managers/__init__.py (reviewed, no changes needed)
- [x] managers/base.py (updated to use absolute imports)
- [x] managers/code_manager.py (updated to use absolute imports and fixed debug import)
- [x] managers/heading_manager.py (updated to use absolute imports and fixed debug import)
- [x] managers/list_manager.py (updated to use absolute imports and fixed debug import)
- [x] managers/paragraph_manager.py (updated to use absolute imports and fixed debug import)
- [x] managers/quote_manager.py (fixed debug import)
- [x] managers/registry_mixin.py (fixed debug import)
- [x] managers/text_manager.py (updated to use absolute imports and fixed debug import)
- [x] managers/text_manager_inline.py (updated to use absolute imports and fixed duplicate method)
- [x] models/__init__.py (reviewed, no changes needed)
- [x] models/base.py (reviewed, no changes needed)
- [x] models/code.py (updated to use absolute imports)
- [x] models/heading.py (updated to use absolute imports)
- [x] models/list.py (updated to use absolute imports)
- [x] models/paragraph.py (updated to use absolute imports)
- [x] models/quote.py (updated to use absolute imports)
- [x] models/text.py (reviewed, no changes needed)

### NEEDS REVIEW:
- [ ] registry.py

## Guidelines for Fixes

1. Import Structure:
   - Use absolute imports for package-level imports
   - Use relative imports only for sibling modules
   - Ensure consistent import style across all files

2. Package Organization:
   - Verify package is properly installed in development mode
   - Ensure all __init__.py files properly expose their public interfaces

3. Process for Each File:
   a. Review current imports
   b. Fix debug imports to use correct absolute paths
   c. Fix any circular dependencies
   d. Test changes after each file modification
   e. Document any breaking changes introduced

4. Testing Strategy:
   - Test each file after modifications
   - Run full test suite after completing each major section
   - Verify no new import errors are introduced

## Current Status

1. Completed:
   - Moved markdown_converter.py to a higher-level directory (resolved circular import)
   - Fixed debug imports in __init__.py
   - Fixed all files in managers directory:
     * Updated imports to use absolute paths
     * Fixed debug imports to use shared debug module
     * Fixed other issues like duplicate methods
   - Completed review of models directory:
     * Updated imports to use absolute paths where needed
     * Some files already had correct imports

2. In Progress:
   - Ready to review final file: registry.py
   - Continuing to update import patterns across the codebase

3. Next Steps:
   - Review registry.py
   - Test filter.py after all changes to verify it runs correctly
   - Update filter.py with any additional fixes needed

## Next Steps
1. Start with __init__.py files to understand package structure (DONE)
2. Fix the critical circular import issue (DONE)
3. Systematically review and update each file (IN PROGRESS)
4. Run comprehensive tests after all changes

