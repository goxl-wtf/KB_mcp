#!/usr/bin/env python3
"""Test the MCP server functionality directly."""

import sys
sys.path.insert(0, 'src')

from main import mcp, register_all_tools, state, initialize_storage
from pathlib import Path
import tempfile
import json

def test_mcp_server():
    """Test the MCP server and verify it's working correctly."""
    
    # Initialize the server
    with tempfile.TemporaryDirectory() as temp_dir:
        state.storage_path = Path(temp_dir)
        initialize_storage()
        register_all_tools()
        
        print("=== MCP Server Test ===\n")
        
        # Test 1: Direct invocation of tools
        print("1. Testing Tool Functions Directly:")
        
        # Test get_status
        try:
            status = get_status()
            print(f"   ✓ get_status: {status}")
        except:
            print("   ✗ get_status not found")
        
        # Use dir() to explore MCP object
        print("\n2. MCP Object Attributes:")
        mcp_attrs = [attr for attr in dir(mcp) if not attr.startswith('_')]
        for attr in mcp_attrs[:10]:  # Show first 10 attributes
            print(f"   - {attr}: {type(getattr(mcp, attr))}")
        
        print("\n3. Server Info:")
        print(f"   Name: {mcp.name}")
        print(f"   Version: {mcp.version}")
        print(f"   Description: {mcp.description}")
        
        # Try to get tool list through tool decorator
        print("\n4. Looking for registered tools:")
        if hasattr(mcp, '_tool_manager'):
            print(f"   Found _tool_manager: {mcp._tool_manager}")
            if hasattr(mcp._tool_manager, 'tools'):
                tools = mcp._tool_manager.tools
                print(f"   Total tools: {len(tools)}")
                for tool_name in list(tools.keys())[:5]:  # Show first 5 tools
                    print(f"   - {tool_name}")
        
        print("\n🎉 MCP Server analysis complete!")

if __name__ == "__main__":
    test_mcp_server()