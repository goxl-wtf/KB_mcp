#!/usr/bin/env python3
"""Test the MCP server functionality."""

import sys
sys.path.insert(0, 'src')

# Create a minimal test environment
import os
os.environ['HIERARCHICAL_KB_STORAGE'] = '/tmp/test_hierarchical_kb'

from main import mcp, state, register_all_tools, initialize_storage
from pathlib import Path

def test_server():
    """Test basic server functionality."""
    print("Testing Hierarchical KB MCP Server...\n")
    
    # Initialize storage
    initialize_storage()
    print(f"✓ Storage initialized at: {state.storage_path}")
    
    # Register tools
    register_all_tools()
    print("✓ Tools registered")
    
    # Test the get_status tool
    print("\nTesting get_status tool:")
    import asyncio
    
    def test_status():
        # Use direct tool function calls since we're not running the full MCP server
        from main import get_status
        status = get_status()
        print(f"✓ Status: {status}")
        
        # Test KB creation
        print("\nTesting KB creation:")
        from tools.kb_tools import create_kb
        result = create_kb(
            title="Test Knowledge Base",
            description="A test KB for MCP server testing",
            default_categories=["Notes", "Tasks", "Documentation"],
            tags=["test", "development"]
        )
        print(f"✓ KB created: {result}")
        
        # Test KB listing
        print("\nTesting KB listing:")
        from tools.kb_tools import list_kbs
        kbs = list_kbs()
        print(f"✓ Found {len(kbs)} KB(s)")
        
        # Test KB selection
        print("\nTesting KB selection:")
        kb_id = result["id"]
        from tools.kb_tools import select_kb
        select_result = select_kb(kb_id=kb_id)
        print(f"✓ Selected KB: {select_result}")
        
        # Test category creation
        print("\nTesting category creation:")
        from tools.category_tools import create_category
        cat_result = create_category(
            name="Research",
            description="Research notes and findings"
        )
        print(f"✓ Category created: {cat_result}")
        
        # Test note creation
        print("\nTesting note creation:")
        from tools.note_tools import create_note
        note_result = create_note(
            title="First Research Note",
            content="# First Research Note\n\nThis is a test note created via MCP.",
            category_path="Research",
            tags=["test", "research"]
        )
        print(f"✓ Note created: {note_result}")
        
        # Test note reading
        print("\nTesting note reading:")
        from tools.note_tools import read_note
        read_result = read_note(note_id=note_result["id"])
        print(f"✓ Note read: {read_result['title']}")
        
        print("\n✅ All server tests passed!")
    
    # Run tests
    test_status()

if __name__ == "__main__":
    test_server()