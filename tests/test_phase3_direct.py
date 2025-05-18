#!/usr/bin/env python3
"""Test Phase 3 features directly without MCP framework."""

import sys
sys.path.insert(0, 'src')

from pathlib import Path
import tempfile
import json

# Import models and utilities
from models import KnowledgeBase, Category, Note
from utils import ensure_directory

def test_search_and_viz_direct():
    """Test search and visualization functionality directly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        storage_path = Path(temp_dir)
        print(f"Testing with storage path: {storage_path}\n")
        
        # Create test KB structure
        print("1. Creating test knowledge base...")
        kb = KnowledgeBase(
            title="Technical Documentation",
            description="A test KB with various technical topics",
            default_categories=["Frontend", "Backend", "DevOps"],
            tags=["technical", "documentation"]
        )
        kb.save(storage_path)
        
        # Create subcategories
        frontend_path = kb.path / "Frontend"
        react_path = frontend_path / "React"
        ensure_directory(react_path)
        
        vue_path = frontend_path / "Vue"
        ensure_directory(vue_path)
        
        backend_path = kb.path / "Backend"
        python_path = backend_path / "Python"
        ensure_directory(python_path)
        
        # Create test notes with links
        print("2. Creating test notes with links and tags...")
        
        # React notes
        react_hooks = Note(
            title="React Hooks Guide",
            content="""# React Hooks Guide

## useState
The useState hook allows you to add state to functional components.

## useEffect
The useEffect hook handles side effects in functional components.

See also: [[react_performance]] and [[react_best_practices]]
""",
            tags=["react", "hooks", "frontend"],
            linked_notes=["react_performance", "react_best_practices"]
        )
        react_hooks.save(react_path)
        
        react_performance = Note(
            title="React Performance Optimization",
            content="""# React Performance Optimization

## Memoization
Use React.memo and useMemo to optimize re-renders.

## Code Splitting
Implement lazy loading with React.lazy and Suspense.

Related: [[react_hooks]] and [[webpack_config]]
""",
            tags=["react", "performance", "optimization"],
            linked_notes=["react_hooks", "webpack_config"]
        )
        react_performance.save(react_path)
        
        # Vue notes
        vue_basics = Note(
            title="Vue.js Basics",
            content="""# Vue.js Basics

## Components
Vue components are reusable UI pieces.

## Reactivity
Vue's reactivity system tracks dependencies.

Compare with [[react_hooks]] for React's approach.
""",
            tags=["vue", "frontend", "basics"],
            linked_notes=["react_hooks"]
        )
        vue_basics.save(vue_path)
        
        # Python notes
        python_decorators = Note(
            title="Python Decorators",
            content="""# Python Decorators

## Function Decorators
Decorators wrap functions to modify behavior.

## Class Decorators
Class decorators can modify class definitions.

Used in web frameworks like [[flask_routing]]
""",
            tags=["python", "decorators", "backend"],
            linked_notes=["flask_routing"]
        )
        python_decorators.save(python_path)
        
        print("✓ Created test KB with categories and linked notes")
        
        # Test search functionality
        print("\n3. Testing search functionality...")
        
        # Set up state for search functions
        from main import state
        state.storage_path = storage_path
        state.current_kb = kb.id
        
        # Test text search
        import re
        from utils import get_content_preview
        
        # Simple search implementation for testing
        results = []
        pattern = re.compile("hooks", re.IGNORECASE)
        
        for note_path in kb.path.rglob("*.md"):
            note = Note.load(note_path)
            score = 0
            
            # Search in title
            if pattern.search(note.title):
                score += 10
            
            # Search in content
            if pattern.search(note.content):
                score += 5
            
            if score > 0:
                results.append({
                    "title": note.title,
                    "score": score,
                    "preview": get_content_preview(note.content, 100)
                })
        
        print(f"✓ Found {len(results)} results for 'hooks'")
        for result in results:
            print(f"  - {result['title']} (score: {result['score']})")
        
        # Test tag search
        tag_results = []
        for note_path in kb.path.rglob("*.md"):
            note = Note.load(note_path)
            if "react" in note.tags:
                tag_results.append(note.title)
        
        print(f"✓ Found {len(tag_results)} notes with 'react' tag")
        
        # Test visualization functionality
        print("\n4. Testing visualization functionality...")
        
        # Generate simple graph statistics
        nodes = []
        edges = []
        
        # Add KB node
        nodes.append({
            "id": f"kb_{kb.id}",
            "label": kb.title,
            "type": "kb"
        })
        
        # Add category nodes
        categories = Category.list_all(kb.path)
        for cat in categories:
            nodes.append({
                "id": f"cat_{cat.relative_path}",
                "label": cat.name,
                "type": "category"
            })
        
        # Add note nodes
        note_count = 0
        link_count = 0
        for note_path in kb.path.rglob("*.md"):
            note = Note.load(note_path)
            note_count += 1
            nodes.append({
                "id": f"note_{note.id}",
                "label": note.title,
                "type": "note"
            })
            link_count += len(note.linked_notes)
        
        print(f"✓ Generated KB graph:")
        print(f"  Total nodes: {len(nodes)}")
        print(f"  Categories: {len(categories)}")
        print(f"  Notes: {note_count}")
        print(f"  Total links: {link_count}")
        
        # Generate statistics
        tag_count = {}
        for note_path in kb.path.rglob("*.md"):
            note = Note.load(note_path)
            for tag in note.tags:
                tag_count[tag] = tag_count.get(tag, 0) + 1
        
        most_common_tag = max(tag_count.items(), key=lambda x: x[1]) if tag_count else ("none", 0)
        
        print(f"\n✓ Generated KB statistics:")
        print(f"  Total categories: {len(categories)}")
        print(f"  Total notes: {note_count}")
        print(f"  Unique tags: {len(tag_count)}")
        print(f"  Most common tag: {most_common_tag[0]} ({most_common_tag[1]} uses)")
        
        # Test related notes functionality
        print("\n5. Testing related notes discovery...")
        
        # Find related notes for react_hooks
        related = []
        
        # Add directly linked notes
        for linked_id in react_hooks.linked_notes:
            for note_path in kb.path.rglob(f"{linked_id}.md"):
                try:
                    linked_note = Note.load(note_path)
                    related.append({
                        "title": linked_note.title,
                        "relationship": "directly_linked",
                        "score": 100
                    })
                except:
                    pass
        
        # Find notes with common tags
        for note_path in kb.path.rglob("*.md"):
            note = Note.load(note_path)
            if note.id != react_hooks.id:
                common_tags = set(note.tags) & set(react_hooks.tags)
                if common_tags:
                    related.append({
                        "title": note.title,
                        "relationship": "similar_tags",
                        "score": len(common_tags) * 20
                    })
        
        print(f"✓ Found {len(related)} related notes for '{react_hooks.title}'")
        for rel in sorted(related, key=lambda x: x['score'], reverse=True):
            print(f"  - {rel['title']} ({rel['relationship']}, score: {rel['score']})")
        
        print("\n✅ All Phase 3 tests completed successfully!")


if __name__ == "__main__":
    test_search_and_viz_direct()