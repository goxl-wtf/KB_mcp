# KB_mcp Project Structure

```
KB_mcp/
├── src/                        # Source code
│   ├── main.py                 # MCP server entry point
│   ├── models/                 # Data models
│   │   ├── __init__.py
│   │   ├── kb.py              # Knowledge Base model
│   │   ├── category.py        # Category model
│   │   └── note.py            # Note model
│   ├── tools/                  # MCP tool implementations
│   │   ├── __init__.py
│   │   ├── kb_tools.py        # KB management tools (10 tools)
│   │   ├── category_tools.py  # Category management tools (6 tools)
│   │   ├── note_tools.py      # Note management tools (8 tools)
│   │   ├── search_tools.py    # Search tools (5 tools)
│   │   ├── analysis_tools.py  # Codebase analysis tools (5 tools)
│   │   └── viz_tools.py       # Visualization tools (5 tools)
│   └── utils/                  # Utility modules
│       ├── __init__.py
│       ├── markdown_utils.py  # Markdown/YAML processing
│       ├── migration.py       # KB migration utilities
│       ├── path_utils.py      # Safe path operations
│       └── token_utils.py     # Token counting & pagination
│
├── docs/                       # Documentation
│   └── architecture.md        # System architecture
│
├── tests/                      # Test files
│   ├── test_basic.py          # Basic model tests
│   ├── test_direct.py         # Direct functionality tests
│   ├── test_integration.py    # Integration tests
│   ├── test_phase3.py         # Phase 3 feature tests
│   ├── test_codebase_analysis.py  # Analysis tests
│   ├── test_analysis_simple.py    # Simple analysis tests
│   ├── test_mcp_protocol.py   # MCP protocol tests
│   ├── test_mcp_server.py     # Server tests
│   ├── test_protocol.py       # Protocol tests
│   ├── test_token_aware.py    # Token system tests
│   └── test_token_aware_simple.py # Simple token tests
│
├── README.md                   # Project documentation
├── LICENSE                     # MIT License
├── requirements.txt            # Python dependencies
├── CLAUDE.md                   # Claude Code guidance
├── PROJECT_STRUCTURE.md        # This file
├── DEVELOPMENT_PLAN.md         # Original development plan
├── IMPLEMENTATION_STATUS.md    # Implementation progress
├── PHASE3_COMPLETION.md        # Phase 3 completion report
├── PHASE4_COMPLETION.md        # Phase 4 completion report
├── MCP_INSPECTOR_REPORT.md     # MCP inspection results
└── migrate.py                  # Migration script
```

## Storage Structure

The KB_mcp server stores data in the following structure:

```
~/.KB_mcp/storage/
├── Knowledge_Base_Name/
│   ├── meta.json              # KB metadata
│   ├── Category_Name/
│   │   ├── category.json      # Category metadata
│   │   ├── Note_Title.md      # Individual notes
│   │   └── Subcategory/
│   │       └── ...
│   └── Another_Category/
│       └── ...
└── Another_KB/
    └── ...
```

## Key Components

1. **Models** - Data structures for KBs, categories, and notes
2. **Tools** - MCP-compatible functions (39 total)
3. **Utilities** - Helper functions for common operations
4. **Tests** - Comprehensive test suite

## Dependencies

- `fastmcp` - FastMCP framework
- `pyyaml` - YAML processing
- `mistune` - Markdown processing

See `requirements.txt` for full dependencies.