#!/usr/bin/env python3
"""Simple test of the hierarchical KB server functionality."""

import sys
sys.path.insert(0, 'src')

import os
from pathlib import Path
import tempfile

# Set up environment
from main import state, register_all_tools, mcp, initialize_storage
from models import KnowledgeBase, Category, Note

def test_simple():
    """Simple test using direct model operations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set up storage
        storage_path = Path(temp_dir)
        state.storage_path = storage_path
        initialize_storage()
        
        print("Simple Hierarchical KB Test\n")
        print(f"Storage: {storage_path}\n")
        
        # Create a KB directly
        kb = KnowledgeBase(
            title="Test Knowledge Base",
            description="A simple test KB",
            default_categories=["Notes", "Resources"],
            tags=["test"]
        )
        kb.save(storage_path)
        print(f"✓ Created KB: {kb.title} (ID: {kb.id})")
        
        # Create a category
        notes_path = kb.path / "Notes"
        dev_notes_path = notes_path / "Development"
        dev_notes_path.mkdir(parents=True, exist_ok=True)
        
        dev_category = Category(
            name="Development",
            description="Development notes",
            parent="Notes",
            path=dev_notes_path,
            relative_path="Notes/Development"
        )
        dev_category.save()
        print(f"✓ Created category: {dev_category.name}")
        
        # Create a note
        note = Note(
            title="Getting Started",
            content="""# Getting Started

This is a test note in the hierarchical KB system.

Features:
- Hierarchical organization
- Cross-references: [[other_note]]
- Tags and metadata
""",
            tags=["getting-started", "documentation"]
        )
        note.save(dev_notes_path)
        print(f"✓ Created note: {note.title}")
        
        # List all content
        print("\nContent Summary:")
        
        # List KBs
        kbs = KnowledgeBase.list_all(storage_path)
        print(f"Knowledge Bases: {len(kbs)}")
        for kb_item in kbs:
            print(f"  - {kb_item.title}")
        
        # List categories
        categories = Category.list_all(kb.path)
        print(f"\nCategories: {len(categories)}")
        for cat in categories:
            print(f"  - {cat.relative_path}")
        
        # List notes
        all_notes = []
        for md_file in kb.path.rglob("*.md"):
            try:
                loaded_note = Note.load(md_file)
                all_notes.append(loaded_note)
            except:
                pass
        
        print(f"\nNotes: {len(all_notes)}")
        for note_item in all_notes:
            print(f"  - {note_item.title} (tags: {', '.join(note_item.tags)})")
        
        # Test the MCP server registration
        print("\nMCP Server Status:")
        register_all_tools()
        
        # Check registered tools
        print(f"Registered tools: {len(mcp._tools) if hasattr(mcp, '_tools') else 'Unknown'}")
        
        # Test get_status tool
        from main import get_status
        status = get_status()
        print(f"Server status: Phase {status['phase']}")
        
        print("\n✅ Test completed successfully!")
        
        # Show final structure
        print("\nDirectory structure:")
        def show_tree(path, prefix=""):
            items = sorted(path.iterdir())
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                print(f"{prefix}{'└── ' if is_last else '├── '}{item.name}")
                if item.is_dir() and not item.name.startswith('.'):
                    show_tree(item, prefix + ("    " if is_last else "│   "))
        
        show_tree(storage_path)


if __name__ == "__main__":
    test_simple()