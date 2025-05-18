# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

KB_mcp is a hierarchical knowledge base MCP (Model Context Protocol) server that manages knowledge bases with a filesystem-based hierarchical structure. It replaces the traditional JSON-based flat knowledge base with a more scalable and organized approach.

## Commands

### Running the Server
```bash
python src/main.py
```

### Running Tests
```bash
# Test basic models
python test_basic.py

# Test direct functionality
python test_direct.py

# Test integration
python test_integration.py

# Test Phase 3 features
python test_phase3.py

# Test Phase 4 codebase analysis
python test_codebase_analysis.py

# Test MCP server and protocol
python test_mcp_server.py
python test_mcp_protocol.py
```

### Migration from JSON KBs
```bash
python migrate.py <source_dir> <target_dir>
python migrate.py --single-file <json_file> <target_dir>
python migrate.py --dry-run <source_dir> <target_dir>
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

## Code Architecture

### Tool Registration Pattern
The server uses FastMCP and registers tools through specific registration functions:
- Each tool group (kb, category, note, search, analysis, viz) has a `register_*_tools()` function
- Tools receive the MCP instance and global state object
- The global state contains `storage_path` and `current_kb`

### Storage Architecture
```
storage/
├── Knowledge_Base_Name/
│   ├── meta.json              # KB metadata
│   ├── Category_Name/
│   │   ├── category.json      # Category metadata
│   │   ├── Note_1.md          # Note with YAML frontmatter
│   │   └── Subcategory/
│   │       └── Note_2.md
```

### Note Format
Notes are Markdown files with YAML frontmatter containing metadata:
- title, created_at, updated_at
- tags, linked_notes, linked_kbs
- Cross-references use wiki-style links: `[[note_id]]` or `[[kb:kb_id]]`

### Global State Management
The server maintains global state in `main.py`:
- `storage_path`: Path to the storage directory (default: `~/.hierarchical-kb/storage`)
- `current_kb`: Currently selected knowledge base ID

### Model Layer
- `models/kb.py`: Knowledge base operations (create, read, update, delete)
- `models/category.py`: Category management with parent-child relationships
- `models/note.py`: Note CRUD operations with cross-reference support

### Tool Groups
1. **KB Tools**: Knowledge base CRUD operations, derive KBs, import/export
2. **Category Tools**: Category management, hierarchical operations
3. **Note Tools**: Note CRUD, move between categories, linking
4. **Search Tools**: Full-text search, tag filtering, related notes
5. **Analysis Tools**: Codebase analysis, pattern extraction
6. **Visualization Tools**: Graph generation, structure visualization

## Core Development Patterns

### Error Handling
Tools should return structured error responses with descriptive messages for common issues like:
- KB/category/note not found
- Invalid paths or IDs
- Permission errors

### Path Management
Use the utilities in `utils/path_utils.py` for safe path operations within the storage directory.

### Markdown Processing
Use `utils/markdown_utils.py` for parsing and generating Markdown with YAML frontmatter.

### Migration Support
The migration utility in `utils/migration.py` handles conversion from JSON-based KBs to the hierarchical structure.

## Environment Variables

- `HIERARCHICAL_KB_STORAGE`: Override default storage path

## Development Phases

The project follows a phased development plan:
- Phase 1: Core infrastructure ✅
- Phase 2: Basic KB management ✅
- Phase 3: Advanced features (search, relationships, visualization) ✅
- Phase 4: Codebase analysis ✅
- Phase 5: Migration and integration (in progress)