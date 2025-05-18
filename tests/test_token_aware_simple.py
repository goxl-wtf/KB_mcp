#!/usr/bin/env python3
"""Simple test for token-aware response system."""

import sys
sys.path.insert(0, 'src')

from pathlib import Path
import tempfile

from utils.token_utils import TokenCounter, PaginatedResponse, ResponseBuilder
from models import KnowledgeBase, Note
from main import state


def test_token_utils():
    """Test token utilities directly."""
    print("=== Token Utilities Test ===\n")
    
    # Test token counting
    text = "This is a test."
    counter = TokenCounter()
    estimate = counter.estimate_tokens(text)
    print(f"Text: '{text}'")
    print(f"Tokens: {estimate.estimated_tokens}")
    print(f"Within limit: {estimate.is_within_limit}\n")
    
    # Test pagination
    items = [{"id": i, "title": f"Note {i}"} for i in range(100)]
    paginated = PaginatedResponse(items, page_size=20)
    page1 = paginated.get_page(1)
    
    print(f"Pagination test:")
    print(f"  Total items: {page1['total_items']}")
    print(f"  Total pages: {page1['total_pages']}")
    print(f"  Current page: {page1['page']}")
    print(f"  Items on page: {len(page1['items'])}\n")
    
    # Test automatic pagination with large items
    large_items = []
    for i in range(10):
        content = f"This is item {i} with very long content. " * 1000
        large_items.append({
            "id": i, 
            "title": f"Large Item {i}",
            "content": content
        })
    
    auto_paged = PaginatedResponse(large_items)
    print(f"Auto-pagination with large items:")
    print(f"  Total items: {len(large_items)}")
    print(f"  Total pages: {auto_paged.total_pages}")
    print()


def test_with_models():
    """Test with actual models."""
    print("=== Model Integration Test ===\n")
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage_path = Path(tmp_dir)
        
        # Create a KB
        kb = KnowledgeBase(
            title="Test KB",
            description="Test knowledge base",
            parent_kb=None,
            default_categories=[],
            tags=["test"]
        )
        kb.save(storage_path)
        print(f"Created KB: {kb.title}")
        
        # Create a large note
        large_content = "# Test Note\n\n" + ("This is a test paragraph. " * 100 + "\n\n") * 100
        
        note = Note(
            title="Large Note",
            content=large_content,
            category_path="/",
            tags=["test"],
            linked_notes=[],
            linked_kbs=[]
        )
        
        # Save note
        kb_path = storage_path / kb.id
        note.save(kb_path)
        print(f"Created note: {note.title}")
        print(f"Content length: {len(note.content)} characters")
        
        # Test token estimation
        counter = TokenCounter()
        estimate = counter.estimate_tokens(note.content)
        print(f"Estimated tokens: {estimate.estimated_tokens}")
        print(f"Exceeds limit: {not estimate.is_within_limit}")
        
        # Test truncation
        if not estimate.is_within_limit:
            truncated, was_truncated = counter.truncate_to_fit(note.content)
            print(f"Content truncated: {was_truncated}")
            print(f"Truncated length: {len(truncated)} characters")
            print()


def test_response_builder():
    """Test response builder functionality."""
    print("=== Response Builder Test ===\n")
    
    builder = ResponseBuilder()
    
    # Create test items with metadata
    items = []
    for i in range(50):
        items.append({
            "id": f"note_{i}",
            "title": f"Note {i}",
            "content": f"This is the content of note {i}. " * 50,
            "tags": ["test", f"tag_{i}"],
            "created_at": "2025-05-18T00:00:00Z"
        })
    
    # Extract metadata only
    def metadata_extractor(item):
        return {
            "id": item["id"],
            "title": item["title"],
            "tags": item["tags"],
            "created_at": item["created_at"]
        }
    
    metadata_list = builder.add_metadata_only(items, metadata_extractor)
    print(f"Metadata extraction:")
    print(f"  Original items: {len(items)}")
    print(f"  Metadata items: {len(metadata_list)}")
    print(f"  Current token size: {builder.current_size}")
    
    # Test search results with snippets
    search_results = []
    for item in items[:10]:
        search_results.append({
            "id": item["id"],
            "title": item["title"],
            "content": item["content"],
            "score": 0.95
        })
    
    builder2 = ResponseBuilder()
    snippet_results = builder2.build_search_results(search_results, snippet_length=100)
    print(f"\nSearch results with snippets:")
    print(f"  Original results: {len(search_results)}")
    print(f"  Snippet results: {len(snippet_results)}")
    if snippet_results:
        print(f"  First snippet length: {len(snippet_results[0].get('content', ''))}")
        print(f"  Content truncated: {snippet_results[0].get('content_truncated', False)}")
    print()


if __name__ == "__main__":
    print("Token-Aware Response System Test\n")
    print("=" * 40 + "\n")
    
    test_token_utils()
    test_with_models()
    test_response_builder()
    
    print("✅ All tests completed!")