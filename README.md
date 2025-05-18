# KB_mcp - Knowledge Base MCP Server

A Model Context Protocol (MCP) server for managing hierarchical knowledge bases with advanced features including categories, cross-references, and codebase analysis.

## Overview

This MCP server provides a hierarchical knowledge management system that addresses limitations in traditional flat knowledge bases:

- **Hierarchical Organization**: Knowledge bases contain categories and subcategories
- **Filesystem-Based Storage**: Notes are stored as individual Markdown files with YAML frontmatter
- **No Token Limits**: Each note is a separate file, eliminating size constraints
- **Knowledge Relationships**: Support for linking between notes and knowledge bases
- **Derived Knowledge Bases**: Create specialized KBs derived from existing ones
- **Migration Support**: Tools to migrate from JSON-based KBs to the new structure

## Architecture

```
storage/
├── Knowledge_Base_1/
│   ├── meta.json                 # KB metadata
│   ├── Category_1/
│   │   ├── category.json         # Category metadata
│   │   ├── Note_1.md             # Individual note
│   │   └── Subcategory/
│   │       ├── category.json
│   │       └── Note_2.md
│   └── Category_2/
│       └── ...
└── Knowledge_Base_2/
    └── ...
```

## Features

### Phase 1: Core Infrastructure ✅
- [x] Filesystem-based storage models
- [x] Knowledge Base, Category, and Note models
- [x] Markdown utilities with YAML frontmatter
- [x] Path management utilities

### Phase 2: Basic KB Management ✅
- [x] KB CRUD operations (create, read, update, delete)
- [x] Category management with hierarchical structure
- [x] Note management with cross-references
- [x] Basic import/export functionality

### Phase 3: Advanced Features ✅
- [x] Full-text search across KBs
- [x] Knowledge relationship management  
- [x] Basic visualization tools
- [x] Tag-based search and filtering
- [x] Related notes discovery
- [x] Graph generation for KB structure
- [x] Statistics and analytics

### Phase 4: Codebase Analysis ✅
- [x] Analyze codebases to create knowledge bases
- [x] Extract patterns and best practices
- [x] Sync with code changes
- [x] Multi-language support (Python, JavaScript, etc.)
- [x] Dependency analysis
- [x] Documentation generation
- [x] Self-analysis capability

### Phase 5: Migration and Integration (Planned)
- [ ] Migrate existing JSON-based KBs
- [ ] Claude Desktop integration
- [ ] Performance optimization

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python src/main.py
```

## Usage

### Creating a Knowledge Base

```python
create_kb(
    title="My Development Guide",
    description="A comprehensive guide for developers",
    default_categories=["Getting Started", "API Reference", "Examples"],
    tags=["development", "documentation"]
)
```

### Creating Categories

```python
create_category(
    name="REST API",
    parent_path="API_Reference",
    description="REST API documentation"
)
```

### Creating Notes

```python
create_note(
    title="Authentication Guide",
    content="# Authentication Guide\n\n## Overview...",
    category_path="API_Reference/REST_API",
    tags=["auth", "security"],
    linked_notes=["oauth_guide", "jwt_guide"]
)
```

### Cross-References

Notes can reference other notes using wiki-style links:
- `[[note_id]]` - Link to another note
- `[[kb:kb_id]]` - Link to another knowledge base

## Configuration

The server uses the following default paths:
- Storage: `~/.hierarchical-kb/storage`
- Configuration: Environment variable `HIERARCHICAL_KB_STORAGE`

## Development

### Running Tests

```bash
# Test basic models
python test_basic.py

# Test full functionality
python test_direct.py
```

### Project Structure

```
src/
├── main.py              # MCP server entry point
├── models/              # Data models
│   ├── kb.py           # Knowledge Base model
│   ├── category.py     # Category model
│   └── note.py         # Note model
├── tools/              # MCP tools
│   ├── kb_tools.py     # KB management
│   ├── category_tools.py # Category management
│   └── note_tools.py   # Note management
└── utils/              # Utilities
    ├── path_utils.py   # Path operations
    └── markdown_utils.py # Markdown processing
```

## Contributing

This project is part of the MCP ecosystem. Contributions are welcome following the development plan outlined in DEVELOPMENT_PLAN.md.

## License

MIT License