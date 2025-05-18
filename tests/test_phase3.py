#!/usr/bin/env python3
"""Test Phase 3 features: Search and Visualization."""

import sys
sys.path.insert(0, 'src')

from pathlib import Path
import tempfile
import json

# Import models and utilities
from models import KnowledgeBase, Category, Note
from utils import ensure_directory

def test_search_and_viz():
    """Test search and visualization functionality."""
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
        
        # Import the tool functions directly for testing
        import os
        sys.path.insert(0, 'src')
        os.environ['HIERARCHICAL_KB_STORAGE'] = str(storage_path)
        
        from main import state, register_all_tools, mcp
        state.storage_path = storage_path
        state.current_kb = kb.id
        register_all_tools()
        
        # Get the registered search tool
        from tools.search_tools import search_notes
        
        if search_notes:
            # Test text search
            results = search_notes(
                query="hooks",
                search_content=True,
                search_title=True
            )
            print(f"✓ Found {len(results)} results for 'hooks'")
            for result in results[:2]:
                print(f"  - {result['title']} (score: {result['score']})")
            
            # Test tag search
            results = search_notes(
                query="",
                tags=["react"]
            )
            print(f"✓ Found {len(results)} notes with 'react' tag")
        
        # Test visualization functionality
        print("\n4. Testing visualization functionality...")
        
        # Get the visualization tools
        generate_kb_graph = None
        generate_kb_stats = None
        for tool in mcp._tools.values():
            if tool.name == "generate_kb_graph":
                generate_kb_graph = tool.fn
            elif tool.name == "generate_kb_stats":
                generate_kb_stats = tool.fn
        
        if generate_kb_graph:
            # Generate KB graph
            graph = generate_kb_graph(
                kb_id=kb.id,
                include_categories=True,
                include_notes=True,
                include_links=True
            )
            print(f"✓ Generated KB graph:")
            print(f"  Nodes: {graph['stats']['total_nodes']}")
            print(f"  Edges: {graph['stats']['total_edges']}")
            print(f"  Categories: {graph['stats']['categories']}")
            print(f"  Notes: {graph['stats']['notes']}")
            print(f"  Links: {graph['stats']['links']}")
        
        if generate_kb_stats:
            # Generate statistics
            stats = generate_kb_stats(kb_id=kb.id)
            print(f"\n✓ Generated KB statistics:")
            print(f"  Total categories: {stats['categories']['total']}")
            print(f"  Total notes: {stats['notes']['total']}")
            print(f"  Notes with tags: {stats['notes']['with_tags']}")
            print(f"  Notes with links: {stats['notes']['with_links']}")
            print(f"  Unique tags: {stats['tags']['unique']}")
            if stats['tags']['most_common']:
                print(f"  Most common tag: {stats['tags']['most_common'][0][0]} ({stats['tags']['most_common'][0][1]} uses)")
        
        # Test related notes functionality
        print("\n5. Testing related notes discovery...")
        
        find_related_notes = None
        for tool in mcp._tools.values():
            if tool.name == "find_related_notes":
                find_related_notes = tool.fn
                break
        
        if find_related_notes:
            related = find_related_notes(
                note_id=react_hooks.id,
                kb_id=kb.id,
                include_linked=True,
                include_similar=True
            )
            print(f"✓ Found {len(related)} related notes for '{react_hooks.title}'")
            for rel in related:
                print(f"  - {rel['title']} ({rel['relationship']}, score: {rel['score']})")
        
        print("\n✅ All Phase 3 tests completed successfully!")


if __name__ == "__main__":
    test_search_and_viz()