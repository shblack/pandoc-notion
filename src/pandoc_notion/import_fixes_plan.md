# Import Fixes Plan

## Critical Issues
1. Remove outdated debug imports:
   - Remove imports from `.debug` module
   - Remove try/except blocks attempting to import from debug module
   - Remove debug_trace decorator usage until proper debugging solution is implemented

2. Fix Critical Circular Import:
   - Resolve import cycle between:
     * pandoc_notion/filter.py
     * pandoc_notion/tools/markdown_converter.py
     * notion_pandoc/filter.py (appears to be a separate package?)

## File Review Status

### PROCESSED:
- [x] filter.py (partially - fixed debug_trace import but needs more work)

### NEEDS REVIEW:
- [ ] __init__.py
- [ ] managers/__init__.py
- [ ] managers/base.py
- [ ] managers/code_manager.py
- [ ] managers/heading_manager.py
- [ ] managers/list_manager.py
- [ ] managers/paragraph_manager.py
- [ ] managers/quote_manager.py
- [ ] managers/registry_mixin.py
- [ ] managers/text_manager.py
- [ ] managers/text_manager_inline.py
- [ ] models/__init__.py
- [ ] models/base.py
- [ ] models/code.py
- [ ] models/heading.py
- [ ] models/list.py
- [ ] models/paragraph.py
- [ ] models/quote.py
- [ ] models/text.py
- [ ] registry.py
- [ ] tools/markdown_converter.py

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
   b. Remove any debug-related imports and decorators
   c. Fix any circular dependencies
   d. Test changes after each file modification
   e. Document any breaking changes introduced

4. Testing Strategy:
   - Test each file after modifications
   - Run full test suite after completing each major section
   - Verify no new import errors are introduced

## Next Steps
1. Start with __init__.py files to understand package structure
2. Fix the critical circular import issue
3. Systematically review and update each file
4. Run comprehensive tests after all changes

