#!/usr/bin/env python3
"""Hierarchical Knowledge Base MCP Server

A Model Context Protocol server for managing knowledge bases with a hierarchical structure.
This server stores knowledge bases as directories and notes as Markdown files with YAML frontmatter.
"""

import os
import sys
import logging
from typing import Optional
from pathlib import Path

import fastmcp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import tools
from tools.kb_tools import register_kb_tools
from tools.category_tools import register_category_tools
from tools.note_tools import register_note_tools
from tools.search_tools import register_search_tools
from tools.analysis_tools import register_analysis_tools
from tools.viz_tools import register_visualization_tools

# Initialize FastMCP server
mcp = fastmcp.FastMCP(
    name="KB_mcp",
    version="1.0.0",
    description="A hierarchical knowledge base management system with MCP"
)

# Default storage path
DEFAULT_STORAGE_PATH = Path.home() / ".hierarchical-kb" / "storage"

# Global state
class GlobalState:
    storage_path: Path = DEFAULT_STORAGE_PATH
    current_kb: Optional[str] = None

state = GlobalState()

def initialize_storage():
    """Initialize the storage directory structure."""
    state.storage_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Storage initialized at: {state.storage_path}")

@mcp.tool()
def get_status() -> dict:
    """Get current server status and configuration."""
    return {
        "storage_path": str(state.storage_path),
        "current_kb": state.current_kb,
        "version": "1.0.0",
        "phase": "Phase 4 - Codebase Analysis"
    }

# Register all tool groups
def register_all_tools():
    """Register all tools with the MCP server."""
    register_kb_tools(mcp, state)
    register_category_tools(mcp, state)
    register_note_tools(mcp, state)
    register_search_tools(mcp, state)
    register_analysis_tools(mcp, state)
    register_visualization_tools(mcp, state)

if __name__ == "__main__":
    # Handle storage path from environment
    storage_path = os.environ.get("HIERARCHICAL_KB_STORAGE", str(DEFAULT_STORAGE_PATH))
    
    state.storage_path = Path(storage_path)
    initialize_storage()
    
    # Register all tools
    register_all_tools()
    
    # Run the server
    mcp.run()