#!/usr/bin/env python3
"""Basic test script to verify the hierarchical KB server is working."""

import sys
sys.path.insert(0, 'src')

from models import KnowledgeBase, Category, Note
from pathlib import Path
import tempfile
import shutil

def test_models():
    """Test the basic model functionality."""
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        storage_path = Path(temp_dir)
        
        print("Testing Knowledge Base model...")
        
        # Test KB creation
        kb = KnowledgeBase(
            title="Test Knowledge Base",
            description="A test KB for development",
            default_categories=["Notes", "Tasks", "References"],
            tags=["test", "development"]
        )
        
        # Save KB
        kb.save(storage_path)
        print(f"✓ Created KB: {kb.title} at {kb.path}")
        
        # List KBs
        kbs = KnowledgeBase.list_all(storage_path)
        print(f"✓ Found {len(kbs)} knowledge base(s)")
        
        # Test Category creation
        print("\nTesting Category model...")
        
        notes_category = Category(
            name="Notes",
            description="General notes"
        )
        notes_category.path = kb.path / "Notes"
        notes_category.relative_path = "Notes"
        notes_category.save()
        print(f"✓ Created category: {notes_category.name}")
        
        # Test Note creation
        print("\nTesting Note model...")
        
        note = Note(
            title="First Note",
            content="# First Note\n\nThis is my first note in the hierarchical KB.",
            tags=["test", "example"]
        )
        note.save(notes_category.path)
        print(f"✓ Created note: {note.title}")
        
        # Test loading
        loaded_kb = KnowledgeBase.load(kb.path)
        print(f"✓ Loaded KB: {loaded_kb.title}")
        
        loaded_note = Note.load(note.path)
        print(f"✓ Loaded note: {loaded_note.title}")
        
        print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_models()