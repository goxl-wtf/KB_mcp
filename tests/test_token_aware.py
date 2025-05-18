#!/usr/bin/env python3
"""Test token-aware response system."""

import sys
sys.path.insert(0, 'src')

from pathlib import Path
import tempfile
import json

from utils.token_utils import TokenCounter, PaginatedResponse, ResponseBuilder
from main import mcp, state, initialize_storage, register_all_tools


def test_token_counter():
    """Test token counting functionality."""
    print("=== Token Counter Test ===\n")
    
    # Test text estimation
    text = "This is a test string for token counting."
    estimate = TokenCounter.estimate_tokens(text)
    print(f"Text: {text}")
    print(f"Characters: {estimate.text_length}")
    print(f"Estimated tokens: {estimate.estimated_tokens}")
    print(f"Within limit: {estimate.is_within_limit}\n")
    
    # Test code estimation
    code = """def hello_world():
    print("Hello, World!")
    return True"""
    code_estimate = TokenCounter.estimate_tokens(code, "code")
    print(f"Code length: {code_estimate.text_length}")
    print(f"Code tokens: {code_estimate.estimated_tokens}\n")
    
    # Test truncation
    long_text = "This is a very long text. " * 1000
    truncated, was_truncated = TokenCounter.truncate_to_fit(long_text, max_tokens=100)
    print(f"Long text truncated: {was_truncated}")
    print(f"Truncated length: {len(truncated)}\n")


def test_paginated_response():
    """Test pagination functionality."""
    print("=== Paginated Response Test ===\n")
    
    # Create test items
    items = [{"id": i, "content": f"Item {i}"} for i in range(100)]
    
    # Test fixed page size
    paginated = PaginatedResponse(items, page_size=10)
    page1 = paginated.get_page(1)
    print(f"Page 1 of {page1['total_pages']}")
    print(f"Items on page: {len(page1['items'])}")
    print(f"Total items: {page1['total_items']}")
    print(f"Has next: {page1['has_next']}\n")
    
    # Test automatic pagination
    large_items = [{"id": i, "content": f"This is a much longer content string for item {i} " * 50} 
                   for i in range(20)]
    auto_paginated = PaginatedResponse(large_items)
    auto_page1 = auto_paginated.get_page(1)
    print(f"Auto-paginated: {auto_page1['total_pages']} pages")
    print(f"First page items: {len(auto_page1['items'])}\n")


def test_mcp_tools_with_tokens():
    """Test MCP tools with token-aware responses."""
    print("=== MCP Tools Token Test ===\n")
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        state.storage_path = Path(tmp_dir)
        initialize_storage()
        register_all_tools()
        
        # Import the actual tool functions
        from tools.kb_tools import create_kb, list_kbs
        from tools.note_tools import create_note, list_notes, read_note
        
        # Create test KB
        kb_result = create_kb(
            title="Token Test KB",
            description="KB for testing token-aware responses"
        )
        print(f"Created KB: {kb_result['title']}\n")
        
        # Select KB
        state.current_kb = kb_result["id"]
        
        # Create a large note
        # Create content that exceeds token limit
        large_content = "# Large Note\n\n" + ("This is a paragraph of content. " * 100 + "\n\n") * 200
        
        note_result = create_note(
            title="Large Test Note",
            content=large_content,
            tags=["test", "large"]
        )
        print(f"Created large note: {note_result.get('title', 'Unknown')}")
        print(f"Content length: {len(large_content)} characters\n")
        
        # Test list_notes with pagination
        list_result = list_notes()
        print(f"List notes result:")
        print(f"  Total items: {list_result.get('total_items', 0)}")
        print(f"  Page: {list_result.get('page', 1)} of {list_result.get('total_pages', 1)}")
        print(f"  Items on page: {len(list_result.get('items', []))}\n")
        
        # Test read_note with pagination
        if 'id' in note_result:
            read_result = read_note(note_id=note_result['id'])
            print(f"Read note result:")
            print(f"  Content truncated: {read_result.get('content_truncated', False)}")
            print(f"  Total pages: {read_result.get('total_pages', 1)}")
            print(f"  Content length on page: {len(read_result.get('content', ''))}\n")
            
            # Test reading page 2 if available
            if read_result.get('total_pages', 1) > 1:
                page2_result = read_note(note_id=note_result['id'], page=2)
                print(f"Read note page 2:")
                print(f"  Page: {page2_result.get('page', 2)}")
                print(f"  Content length: {len(page2_result.get('content', ''))}\n")
        
        # Test list_kbs with pagination
        kb_list = list_kbs()
        print(f"List KBs result:")
        print(f"  Total items: {kb_list.get('total_items', 0)}")
        print(f"  Page info: Page {kb_list.get('page', 1)} of {kb_list.get('total_pages', 1)}")
        print(f"  Items: {len(kb_list.get('items', []))}\n")


if __name__ == "__main__":
    print("Token-Aware Response System Test\n")
    print("=" * 40 + "\n")
    
    test_token_counter()
    test_paginated_response()
    test_mcp_tools_with_tokens()
    
    print("✅ All tests completed!")