#!/usr/bin/env python3
"""
Test script to verify the hierarchical KB MCP server is working correctly.
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from models.kb import KnowledgeBase
from models.category import Category
from models.note import Note

# Create a simple state object similar to main.py
class GlobalState:
    storage_path: Path = None
    current_kb: str = None

state = GlobalState()

def initialize_storage():
    """Initialize the storage directory structure."""
    state.storage_path.mkdir(parents=True, exist_ok=True)
    print(f"Storage initialized at: {state.storage_path}")

def test_hierarchical_kb():
    """Test the hierarchical KB functionality directly."""
    # Initialize storage
    state.storage_path = Path("/tmp/test_hierarchical_kb")
    initialize_storage()
    
    print("Testing Hierarchical KB...")
    
    # Test 1: Create a KB
    kb = KnowledgeBase(title="Test KB", description="Test knowledge base")
    kb.save(state.storage_path)
    print(f"✓ Created KB: {kb.title} (ID: {kb.id})")
    
    # Test 2: Create a category
    category = Category(
        name="Test Category",
        description="Test category"
    )
    # Set the path for the category
    category.path = state.storage_path / kb.id / "test_category"
    category.save()
    print(f"✓ Created Category: {category.name} (Path: {category.path})")
    
    # Test 3: Create a note
    note = Note(
        title="Test Note",
        content="This is a test note."
    )
    note.save(category.path)
    print(f"✓ Created Note: {note.title} (ID: {note.id})")
    
    # Test 4: Verify files exist
    kb_path = state.storage_path / kb.id
    note_path = category.path / f"{note.id}.md"
    
    if kb_path.exists():
        print(f"✓ KB directory exists: {kb_path}")
    else:
        print(f"✗ KB directory missing: {kb_path}")
        
    if category.path.exists():
        print(f"✓ Category directory exists: {category.path}")
    else:
        print(f"✗ Category directory missing: {category.path}")
        
    if note_path.exists():
        print(f"✓ Note file exists: {note_path}")
    else:
        print(f"✗ Note file missing: {note_path}")
    
    # Test 5: List all KBs
    kbs = KnowledgeBase.list_all(state.storage_path)
    print(f"✓ Found {len(kbs)} KBs: {[kb.title for kb in kbs]}")
    
    # Test 6: Get KB by ID
    kb_path = state.storage_path / kb.id
    loaded_kb = KnowledgeBase.load(kb_path)
    if loaded_kb:
        print(f"✓ Loaded KB by ID: {loaded_kb.title}")
    else:
        print(f"✗ Failed to load KB by ID")
    
    # Test 7: Load category
    loaded_category = Category.load(category.path, kb_path)
    if loaded_category:
        print(f"✓ Loaded Category: {loaded_category.name}")
    else:
        print(f"✗ Failed to load Category")
    
    # Test 8: Load note
    loaded_note = Note.load(note_path)
    if loaded_note:
        print(f"✓ Loaded Note: {loaded_note.title}")
    else:
        print(f"✗ Failed to load Note")
    
    print("\nAll tests completed!")
    
    # Cleanup
    import shutil
    shutil.rmtree(state.storage_path)
    print("Test directory cleaned up.")

if __name__ == "__main__":
    test_hierarchical_kb()