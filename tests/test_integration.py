#!/usr/bin/env python3
"""Integration test for the complete hierarchical KB system."""

import sys
sys.path.insert(0, 'src')

import os
from pathlib import Path
import tempfile
import json

# Set up environment
from main import state, register_all_tools, mcp, initialize_storage

def test_full_system():
    """Test the complete hierarchical KB system."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set up storage
        storage_path = Path(temp_dir)
        state.storage_path = storage_path
        initialize_storage()
        register_all_tools()
        
        print("Hierarchical KB System Integration Test\n")
        print(f"Storage: {storage_path}\n")
        
        # Phase 1: Test KB Management
        print("=== Phase 1: KB Management ===")
        
        # Create KB using the registered tool
        kb_title = "Integration Test KB"
        kb_desc = "A comprehensive test of all features"
        
        # Find the create_kb tool
        create_kb_tool = next((t for t in mcp.tools if t.name == "create_kb"), None)
        if create_kb_tool:
            kb_result = create_kb_tool.fn(
                title=kb_title,
                description=kb_desc,
                default_categories=["Documentation", "Code Examples", "Architecture"],
                tags=["test", "integration"]
            )
            print(f"✓ Created KB: {kb_result['title']} (ID: {kb_result['id']})")
            kb_id = kb_result['id']
            
            # Select the KB
            select_kb_tool = next((t for t in mcp.tools if t.name == "select_kb"), None)
            if select_kb_tool:
                select_result = select_kb_tool.fn(kb_id=kb_id)
                print(f"✓ Selected KB: {select_result['kb_id']}")
        
        # Phase 2: Test Category Management
        print("\n=== Phase 2: Category Management ===")
        
        create_category_tool = next((t for t in mcp.tools if t.name == "create_category"), None)
        if create_category_tool:
            # Create nested categories
            react_cat = create_category_tool.fn(
                name="React",
                parent_path="Code Examples",
                description="React code examples and patterns"
            )
            print(f"✓ Created category: {react_cat['name']} at {react_cat['relative_path']}")
            
            hooks_cat = create_category_tool.fn(
                name="Hooks",
                parent_path="Code Examples/React",
                description="React hooks examples"
            )
            print(f"✓ Created nested category: {hooks_cat['name']} at {hooks_cat['relative_path']}")
        
        # Phase 3: Test Note Management
        print("\n=== Phase 3: Note Management ===")
        
        create_note_tool = next((t for t in mcp.tools if t.name == "create_note"), None)
        if create_note_tool:
            # Create notes with links
            note1 = create_note_tool.fn(
                title="React useState Hook",
                content="""# React useState Hook

The useState hook is fundamental for managing state in functional components.

```javascript
const [count, setCount] = useState(0);
```

See also: [[useEffect_guide]] for side effects.
""",
                category_path="Code Examples/React/Hooks",
                tags=["react", "hooks", "state"],
                linked_notes=["useEffect_guide"]
            )
            print(f"✓ Created note: {note1['title']} (ID: {note1['id']})")
            
            note2 = create_note_tool.fn(
                title="React useEffect Guide",
                content="""# React useEffect Guide

The useEffect hook handles side effects in React components.

```javascript
useEffect(() => {
    // Effect logic here
    return () => {
        // Cleanup logic
    };
}, [dependencies]);
```

Related: [[React useState Hook]] for state management.
""",
                category_path="Code Examples/React/Hooks",
                tags=["react", "hooks", "effects"],
                linked_notes=["React_useState_Hook"]
            )
            print(f"✓ Created note: {note2['title']} (ID: {note2['id']})")
        
        # Phase 4: Test Search
        print("\n=== Phase 4: Search Functionality ===")
        
        search_notes_tool = next((t for t in mcp.tools if t.name == "search_notes"), None)
        if search_notes_tool:
            # Search by content
            search_results = search_notes_tool.fn(
                query="useState",
                search_content=True,
                search_title=True
            )
            print(f"✓ Search for 'useState': Found {len(search_results)} results")
            for result in search_results[:2]:
                print(f"  - {result['title']} (score: {result['score']})")
            
            # Search by tags
            tag_results = search_notes_tool.fn(
                query="",
                tags=["hooks"]
            )
            print(f"✓ Search by tag 'hooks': Found {len(tag_results)} results")
        
        # Phase 5: Test Visualization
        print("\n=== Phase 5: Visualization ===")
        
        generate_kb_graph_tool = next((t for t in mcp.tools if t.name == "generate_kb_graph"), None)
        if generate_kb_graph_tool:
            graph = generate_kb_graph_tool.fn(
                kb_id=kb_id,
                include_categories=True,
                include_notes=True,
                include_links=True
            )
            print(f"✓ Generated KB graph:")
            print(f"  - Total nodes: {graph['stats']['total_nodes']}")
            print(f"  - Categories: {graph['stats']['categories']}")
            print(f"  - Notes: {graph['stats']['notes']}")
            print(f"  - Links: {graph['stats']['links']}")
        
        generate_kb_stats_tool = next((t for t in mcp.tools if t.name == "generate_kb_stats"), None)
        if generate_kb_stats_tool:
            stats = generate_kb_stats_tool.fn(kb_id=kb_id)
            print(f"\n✓ KB Statistics:")
            print(f"  - Categories: {stats['categories']['total']}")
            print(f"  - Notes: {stats['notes']['total']}")
            print(f"  - Unique tags: {stats['tags']['unique']}")
            print(f"  - Total links: {stats['links']['total']}")
        
        # Phase 6: Test Export/Import
        print("\n=== Phase 6: Export/Import ===")
        
        export_kb_tool = next((t for t in mcp.tools if t.name == "export_kb"), None)
        if export_kb_tool:
            export_path = str(storage_path / f"{kb_id}_export.json")
            export_result = export_kb_tool.fn(
                kb_id=kb_id,
                export_path=export_path
            )
            print(f"✓ Exported KB to: {export_result['export_path']}")
            print(f"  - Categories: {export_result['stats']['categories']}")
            print(f"  - Notes: {export_result['stats']['notes']}")
        
        # Test Relationships
        print("\n=== Phase 7: Knowledge Relationships ===")
        
        find_related_notes_tool = next((t for t in mcp.tools if t.name == "find_related_notes"), None)
        if find_related_notes_tool and 'note1' in locals():
            related = find_related_notes_tool.fn(
                note_id=note1['id'],
                kb_id=kb_id,
                include_linked=True,
                include_similar=True
            )
            print(f"✓ Found {len(related)} related notes for '{note1['title']}'")
            for rel in related:
                print(f"  - {rel['title']} ({rel['relationship']})")
        
        print("\n✅ Integration test completed successfully!")
        print(f"\nFinal structure at: {storage_path}")


if __name__ == "__main__":
    test_full_system()