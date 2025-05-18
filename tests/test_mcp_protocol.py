#!/usr/bin/env python3
"""
Test the MCP server protocol directly.
"""

import json
import subprocess
import time
from pathlib import Path
import os

def test_mcp_server():
    """Test the MCP server with direct protocol commands."""
    
    # Use the virtual environment Python
    venv_python = str(Path(__file__).parent / ".venv" / "bin" / "python3")
    
    # Start the server as a subprocess
    server_proc = subprocess.Popen(
        [venv_python, "src/main.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, "HIERARCHICAL_KB_STORAGE": "/tmp/test_hierarchical_kb"}
    )
    
    # Wait for server to start
    time.sleep(2)
    
    # Check if server is still running
    if server_proc.poll() is not None:
        print("Server terminated early")
        stderr_output = server_proc.stderr.read()
        print("STDERR:", stderr_output)
        return
    
    # Test initialize request
    initialize_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "1.0",
            "clientInfo": {"name": "test-client", "version": "1.0"}
        }
    }
    
    try:
        # Send request
        server_proc.stdin.write(json.dumps(initialize_request) + "\n")
        server_proc.stdin.flush()
        
        # Read response with timeout
        import select
        ready = select.select([server_proc.stdout], [], [], 5.0)
        if ready[0]:
            response_line = server_proc.stdout.readline()
            print("Initialize response:", response_line)
        else:
            print("No response received within timeout")
            
    except BrokenPipeError:
        print("BrokenPipeError - server may have terminated")
        stderr_output = server_proc.stderr.read()
        print("STDERR:", stderr_output)
    
    # Clean up
    server_proc.terminate()
    server_proc.wait()

if __name__ == "__main__":
    test_mcp_server()