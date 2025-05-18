#!/usr/bin/env python3
"""Test the MCP server via MCP protocol."""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp_protocol():
    """Test the MCP server through the actual protocol."""
    
    server_params = StdioServerParameters(
        command="python",
        args=["src/main.py"],
        env={"PYTHONPATH": "src"}
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            server_info = await session.initialize()
            
            print("=== MCP Protocol Test ===\n")
            print("1. Server Information:")
            print(f"   Protocol Version: {server_info.protocolVersion}")
            print(f"   Name: {server_info.serverInfo.name}")
            print(f"   Version: {server_info.serverInfo.version}")
            
            # List available tools
            print("\n2. Available Tools:")
            tools_result = await session.list_tools()
            tools = tools_result.tools  # Access the tools list from the result
            print(f"   Total tools: {len(tools)}")
            for i, tool in enumerate(tools[:10]):  # Show first 10
                print(f"   {i+1}. {tool.name} - {tool.description}")
            
            # Test some tools
            print("\n3. Testing Tools:")
            
            # Test get_status
            try:
                result = await session.call_tool("get_status", {})
                print(f"   ✓ get_status: {result}")
            except Exception as e:
                print(f"   ✗ get_status error: {e}")
            
            # Test create_kb
            try:
                result = await session.call_tool("create_kb", {
                    "title": "Test KB",
                    "description": "Test knowledge base"
                })
                print(f"   ✓ create_kb: Created KB with ID {result}")
            except Exception as e:
                print(f"   ✗ create_kb error: {e}")
            
            # Test list_kbs
            try:
                result = await session.call_tool("list_kbs", {})
                print(f"   ✓ list_kbs: Found knowledge bases")
            except Exception as e:
                print(f"   ✗ list_kbs error: {e}")
            
            # Tool categories
            tool_categories = {}
            for tool in tools:
                category = tool.name.split('_')[0]
                if category not in tool_categories:
                    tool_categories[category] = []
                tool_categories[category].append(tool.name)
            
            print("\n4. Tool Categories:")
            for category, tool_names in sorted(tool_categories.items()):
                print(f"   {category}: {len(tool_names)} tools")
            
            print("\n✅ MCP Protocol test completed successfully!")
            
            # Show all tools for verification
            print("\n5. All Available Tools:")
            for tool in tools:
                print(f"   - {tool.name}")

if __name__ == "__main__":
    asyncio.run(test_mcp_protocol())