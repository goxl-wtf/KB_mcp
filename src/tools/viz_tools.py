"""Visualization Tools

Tools for generating visual representations of knowledge relationships.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Any, Set
from collections import defaultdict

import fastmcp

from models import Note, Category, KnowledgeBase
from utils import get_kb_hierarchy


def register_visualization_tools(mcp: fastmcp.FastMCP, state):
    """Register all visualization tools with the MCP server."""
    
    @mcp.tool()
    def generate_kb_graph(
        kb_id: Optional[str] = None,
        include_categories: bool = True,
        include_notes: bool = True,
        include_links: bool = True,
        max_depth: int = 5
    ) -> Dict[str, Any]:
        """Generate a graph representation of a knowledge base.
        
        Args:
            kb_id: KB to visualize (uses current if not specified)
            include_categories: Include category nodes
            include_notes: Include note nodes
            include_links: Include note-to-note links
            max_depth: Maximum depth for category hierarchy
        
        Returns:
            Graph data in JSON format suitable for visualization
        """
        # Determine KB
        if kb_id:
            kb_path = state.storage_path / kb_id
        elif state.current_kb:
            kb_path = state.storage_path / state.current_kb
            kb_id = state.current_kb
        else:
            return {"error": "No KB specified or selected"}
        
        if not kb_path.exists():
            return {"error": f"Knowledge base '{kb_id}' not found"}
        
        # Initialize graph data
        nodes = []
        edges = []
        
        # Add KB root node
        kb = KnowledgeBase.load(kb_path)
        nodes.append({
            "id": f"kb_{kb_id}",
            "label": kb.title,
            "type": "kb",
            "level": 0
        })
        
        # Add categories
        if include_categories:
            category_map = {}
            for cat_path, level in get_kb_hierarchy(kb_path):
                if level <= max_depth:
                    cat_id = f"cat_{cat_path.replace('/', '_')}"
                    category_map[cat_path] = cat_id
                    
                    nodes.append({
                        "id": cat_id,
                        "label": Path(cat_path).name,
                        "type": "category",
                        "level": level,
                        "path": cat_path
                    })
                    
                    # Add edge to parent
                    parent_path = str(Path(cat_path).parent)
                    if parent_path == ".":
                        parent_id = f"kb_{kb_id}"
                    else:
                        parent_id = category_map.get(parent_path, f"kb_{kb_id}")
                    
                    edges.append({
                        "source": parent_id,
                        "target": cat_id,
                        "type": "contains"
                    })
        
        # Add notes
        note_map = {}
        if include_notes:
            for note_path in kb_path.rglob("*.md"):
                try:
                    note = Note.load(note_path)
                    note_id = f"note_{note.id}"
                    note_map[note.id] = note_id
                    
                    # Determine category
                    cat_path = str(note_path.parent.relative_to(kb_path))
                    if cat_path == ".":
                        parent_id = f"kb_{kb_id}"
                    else:
                        parent_id = category_map.get(cat_path, f"kb_{kb_id}")
                    
                    nodes.append({
                        "id": note_id,
                        "label": note.title,
                        "type": "note",
                        "tags": note.tags,
                        "path": str(note_path.relative_to(kb_path))
                    })
                    
                    edges.append({
                        "source": parent_id,
                        "target": note_id,
                        "type": "contains"
                    })
                    
                except Exception as e:
                    print(f"Error processing note {note_path}: {e}")
                    continue
        
        # Add note links
        if include_links and include_notes:
            for note_path in kb_path.rglob("*.md"):
                try:
                    note = Note.load(note_path)
                    source_id = note_map.get(note.id)
                    
                    if source_id:
                        for linked_id in note.linked_notes:
                            target_id = note_map.get(linked_id)
                            if target_id:
                                edges.append({
                                    "source": source_id,
                                    "target": target_id,
                                    "type": "links_to"
                                })
                    
                except Exception as e:
                    print(f"Error processing links for {note_path}: {e}")
                    continue
        
        return {
            "kb_id": kb_id,
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "categories": len([n for n in nodes if n["type"] == "category"]),
                "notes": len([n for n in nodes if n["type"] == "note"]),
                "links": len([e for e in edges if e["type"] == "links_to"])
            }
        }
    
    @mcp.tool()
    def generate_link_graph(
        note_id: str,
        kb_id: Optional[str] = None,
        depth: int = 2,
        include_backlinks: bool = True
    ) -> Dict[str, Any]:
        """Generate a graph of links from/to a specific note.
        
        Args:
            note_id: Central note ID
            kb_id: KB to search in
            depth: How many levels of links to follow
            include_backlinks: Include notes that link to this note
        
        Returns:
            Graph data centered on the specified note
        """
        # Determine KB
        if kb_id:
            kb_path = state.storage_path / kb_id
        elif state.current_kb:
            kb_path = state.storage_path / state.current_kb
            kb_id = state.current_kb
        else:
            return {"error": "No KB specified or selected"}
        
        # Find the central note
        central_note_path = None
        for note_path in kb_path.rglob(f"{note_id}.md"):
            central_note_path = note_path
            break
        
        if not central_note_path:
            return {"error": f"Note '{note_id}' not found"}
        
        nodes = []
        edges = []
        visited = set()
        
        def add_note_and_links(note_path: Path, current_depth: int, parent_id: Optional[str] = None):
            """Recursively add notes and their links."""
            if current_depth > depth or str(note_path) in visited:
                return
            
            visited.add(str(note_path))
            
            try:
                note = Note.load(note_path)
                node_id = f"note_{note.id}"
                
                nodes.append({
                    "id": node_id,
                    "label": note.title,
                    "type": "note",
                    "depth": current_depth,
                    "central": note.id == note_id,
                    "tags": note.tags
                })
                
                if parent_id:
                    edges.append({
                        "source": parent_id,
                        "target": node_id,
                        "type": "links_to"
                    })
                
                # Add forward links
                for linked_id in note.linked_notes:
                    for linked_path in kb_path.rglob(f"{linked_id}.md"):
                        add_note_and_links(linked_path, current_depth + 1, node_id)
                        break
                
            except Exception as e:
                print(f"Error processing note {note_path}: {e}")
        
        # Start from central note
        add_note_and_links(central_note_path, 0)
        
        # Add backlinks if requested
        if include_backlinks:
            for note_path in kb_path.rglob("*.md"):
                if str(note_path) not in visited:
                    try:
                        note = Note.load(note_path)
                        if note_id in note.linked_notes:
                            add_note_and_links(note_path, 1, None)
                            
                            # Add edge from this note to central
                            source_id = f"note_{note.id}"
                            target_id = f"note_{note_id}"
                            edges.append({
                                "source": source_id,
                                "target": target_id,
                                "type": "links_to"
                            })
                            
                    except Exception as e:
                        print(f"Error processing backlink from {note_path}: {e}")
                        continue
        
        return {
            "central_note": note_id,
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "max_depth": max((n["depth"] for n in nodes), default=0)
            }
        }
    
    @mcp.tool()
    def generate_kb_hierarchy_tree(
        kb_id: Optional[str] = None,
        format: str = "text",
        include_notes: bool = True,
        max_depth: int = 10
    ) -> str | Dict[str, Any]:
        """Generate a hierarchical tree view of a knowledge base.
        
        Args:
            kb_id: KB to visualize
            format: Output format ('text' or 'json')
            include_notes: Include notes in the tree
            max_depth: Maximum depth to display
        
        Returns:
            Tree representation in specified format
        """
        # Determine KB
        if kb_id:
            kb_path = state.storage_path / kb_id
        elif state.current_kb:
            kb_path = state.storage_path / state.current_kb
            kb_id = state.current_kb
        else:
            return {"error": "No KB specified or selected"}
        
        if not kb_path.exists():
            return {"error": f"Knowledge base '{kb_id}' not found"}
        
        kb = KnowledgeBase.load(kb_path)
        
        if format == "json":
            # Build JSON tree
            def build_tree(path: Path, depth: int = 0) -> Dict[str, Any]:
                if depth > max_depth:
                    return None
                
                node = {
                    "name": path.name if path != kb_path else kb.title,
                    "type": "category" if path.is_dir() else "note",
                    "children": []
                }
                
                if path.is_dir():
                    # Add subcategories
                    for item in sorted(path.iterdir()):
                        if item.is_dir() and not item.name.startswith('.'):
                            child = build_tree(item, depth + 1)
                            if child:
                                node["children"].append(child)
                    
                    # Add notes if requested
                    if include_notes:
                        for note_path in sorted(path.glob("*.md")):
                            try:
                                note = Note.load(note_path)
                                node["children"].append({
                                    "name": note.title,
                                    "type": "note",
                                    "id": note.id,
                                    "tags": note.tags
                                })
                            except:
                                pass
                
                return node
            
            return build_tree(kb_path)
        
        else:
            # Build text tree
            lines = [f"{kb.title} ({kb_id})"]
            
            def add_tree_lines(path: Path, prefix: str = "", depth: int = 0):
                if depth > max_depth:
                    return
                
                items = sorted(path.iterdir())
                dirs = [item for item in items if item.is_dir() and not item.name.startswith('.')]
                files = [item for item in items if item.is_file() and item.suffix == '.md'] if include_notes else []
                
                all_items = dirs + files
                
                for i, item in enumerate(all_items):
                    is_last = i == len(all_items) - 1
                    current_prefix = "└── " if is_last else "├── "
                    next_prefix = "    " if is_last else "│   "
                    
                    if item.is_dir():
                        lines.append(f"{prefix}{current_prefix}{item.name}/")
                        add_tree_lines(item, prefix + next_prefix, depth + 1)
                    else:
                        try:
                            note = Note.load(item)
                            lines.append(f"{prefix}{current_prefix}{note.title} ({note.id})")
                        except:
                            lines.append(f"{prefix}{current_prefix}{item.name}")
            
            add_tree_lines(kb_path)
            return "\n".join(lines)
    
    @mcp.tool()
    def generate_tag_cloud(
        kb_id: Optional[str] = None,
        min_count: int = 1
    ) -> Dict[str, Any]:
        """Generate tag frequency data for a tag cloud visualization.
        
        Args:
            kb_id: KB to analyze (all KBs if not specified)
            min_count: Minimum occurrences to include tag
        
        Returns:
            Tag frequency data
        """
        tag_counts = defaultdict(int)
        tag_notes = defaultdict(list)
        
        # Determine scope
        if kb_id:
            search_paths = [state.storage_path / kb_id]
        else:
            search_paths = [
                kb_dir for kb_dir in state.storage_path.iterdir()
                if kb_dir.is_dir() and (kb_dir / "meta.json").exists()
            ]
        
        # Count tags
        for search_path in search_paths:
            kb_name = search_path.name
            
            for note_path in search_path.rglob("*.md"):
                try:
                    note = Note.load(note_path)
                    for tag in note.tags:
                        tag_counts[tag] += 1
                        tag_notes[tag].append({
                            "note_id": note.id,
                            "title": note.title,
                            "kb_id": kb_name
                        })
                except Exception as e:
                    print(f"Error processing note {note_path}: {e}")
                    continue
        
        # Filter by minimum count
        filtered_tags = []
        for tag, count in tag_counts.items():
            if count >= min_count:
                filtered_tags.append({
                    "tag": tag,
                    "count": count,
                    "notes": tag_notes[tag][:10],  # Limit to 10 example notes
                    "total_notes": len(tag_notes[tag])
                })
        
        # Sort by count
        filtered_tags.sort(key=lambda x: x["count"], reverse=True)
        
        return {
            "tags": filtered_tags,
            "total_tags": len(filtered_tags),
            "max_count": max(tag_counts.values()) if tag_counts else 0
        }
    
    @mcp.tool()
    def generate_kb_stats(
        kb_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate statistics about a knowledge base.
        
        Args:
            kb_id: KB to analyze (current KB if not specified)
        
        Returns:
            Comprehensive statistics about the KB
        """
        # Determine KB
        if kb_id:
            kb_path = state.storage_path / kb_id
        elif state.current_kb:
            kb_path = state.storage_path / state.current_kb
            kb_id = state.current_kb
        else:
            return {"error": "No KB specified or selected"}
        
        if not kb_path.exists():
            return {"error": f"Knowledge base '{kb_id}' not found"}
        
        kb = KnowledgeBase.load(kb_path)
        
        # Collect statistics
        stats = {
            "kb_id": kb_id,
            "title": kb.title,
            "created_at": kb.created_at.isoformat(),
            "updated_at": kb.updated_at.isoformat(),
            "categories": {
                "total": 0,
                "max_depth": 0,
                "by_level": defaultdict(int)
            },
            "notes": {
                "total": 0,
                "with_tags": 0,
                "with_links": 0,
                "orphaned": 0
            },
            "tags": {
                "unique": set(),
                "most_common": []
            },
            "links": {
                "total": 0,
                "unique_targets": set()
            }
        }
        
        # Count categories
        for cat_path, level in get_kb_hierarchy(kb_path):
            stats["categories"]["total"] += 1
            stats["categories"]["by_level"][level] += 1
            stats["categories"]["max_depth"] = max(stats["categories"]["max_depth"], level)
        
        # Analyze notes
        note_ids = set()
        tag_counts = defaultdict(int)
        
        for note_path in kb_path.rglob("*.md"):
            try:
                note = Note.load(note_path)
                note_ids.add(note.id)
                stats["notes"]["total"] += 1
                
                if note.tags:
                    stats["notes"]["with_tags"] += 1
                    for tag in note.tags:
                        stats["tags"]["unique"].add(tag)
                        tag_counts[tag] += 1
                
                if note.linked_notes:
                    stats["notes"]["with_links"] += 1
                    stats["links"]["total"] += len(note.linked_notes)
                    for linked_id in note.linked_notes:
                        stats["links"]["unique_targets"].add(linked_id)
                
            except Exception as e:
                print(f"Error processing note {note_path}: {e}")
                continue
        
        # Find orphaned links
        for target_id in stats["links"]["unique_targets"]:
            if target_id not in note_ids:
                stats["notes"]["orphaned"] += 1
        
        # Process tag statistics
        stats["tags"]["unique"] = len(stats["tags"]["unique"])
        stats["tags"]["most_common"] = sorted(
            [(tag, count) for tag, count in tag_counts.items()],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Convert sets to counts
        stats["links"]["unique_targets"] = len(stats["links"]["unique_targets"])
        
        return stats