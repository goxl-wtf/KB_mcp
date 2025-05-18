"""Knowledge Base Management Tools

Tools for creating, managing, and interacting with knowledge bases.
"""

from pathlib import Path
from typing import List, Dict, Optional, Any
import json
import shutil

import fastmcp

from models import KnowledgeBase, Category, Note
from utils import ensure_directory, validate_id, get_safe_filename


def register_kb_tools(mcp: fastmcp.FastMCP, state):
    """Register all KB management tools with the MCP server."""
    
    @mcp.tool()
    def create_kb(
        title: str,
        description: str = "",
        parent_kb: Optional[str] = None,
        default_categories: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new knowledge base.
        
        Args:
            title: Title of the knowledge base
            description: Description of the knowledge base
            parent_kb: Optional parent KB ID for derived knowledge bases
            default_categories: List of default categories to create
            tags: List of tags for the KB
        
        Returns:
            Dictionary with KB details
        """
        try:
            # Create KB instance
            kb = KnowledgeBase(
                title=title,
                description=description,
                parent_kb=parent_kb,
                default_categories=default_categories or [],
                tags=tags or []
            )
            
            # Validate KB ID
            if not validate_id(kb.id):
                return {"error": f"Invalid KB ID generated: {kb.id}"}
            
            # Check if KB already exists
            kb_path = state.storage_path / kb.id
            if kb_path.exists():
                return {"error": f"Knowledge base '{title}' already exists"}
            
            # Save KB (creates directory and metadata)
            kb.save(state.storage_path)
            
            return {
                "id": kb.id,
                "title": kb.title,
                "path": str(kb.path),
                "created_at": kb.created_at.isoformat(),
                "default_categories": kb.default_categories
            }
            
        except Exception as e:
            return {"error": f"Failed to create knowledge base: {str(e)}"}
    
    @mcp.tool()
    def list_kbs() -> List[Dict[str, Any]]:
        """List all available knowledge bases.
        
        Returns:
            List of KB summaries
        """
        try:
            kbs = KnowledgeBase.list_all(state.storage_path)
            
            return [{
                "id": kb.id,
                "title": kb.title,
                "description": kb.description,
                "created_at": kb.created_at.isoformat(),
                "updated_at": kb.updated_at.isoformat(),
                "parent_kb": kb.parent_kb,
                "tags": kb.tags,
                "is_selected": kb.id == state.current_kb
            } for kb in kbs]
            
        except Exception as e:
            return [{"error": f"Failed to list knowledge bases: {str(e)}"}]
    
    @mcp.tool()
    def select_kb(kb_id: str) -> Dict[str, Any]:
        """Select a knowledge base for current operations.
        
        Args:
            kb_id: ID of the knowledge base to select
        
        Returns:
            Confirmation message or error
        """
        try:
            kb_path = state.storage_path / kb_id
            
            if not kb_path.exists():
                return {"error": f"Knowledge base '{kb_id}' not found"}
            
            # Load KB to verify it's valid
            kb = KnowledgeBase.load(kb_path)
            
            # Update state
            state.current_kb = kb_id
            
            return {
                "message": f"Selected knowledge base: {kb.title}",
                "kb_id": kb_id,
                "title": kb.title,
                "path": str(kb_path)
            }
            
        except Exception as e:
            return {"error": f"Failed to select knowledge base: {str(e)}"}
    
    @mcp.tool()
    def get_current_kb() -> Dict[str, Any]:
        """Get information about the currently selected knowledge base.
        
        Returns:
            Current KB details or error
        """
        if not state.current_kb:
            return {"error": "No knowledge base selected"}
        
        try:
            kb_path = state.storage_path / state.current_kb
            kb = KnowledgeBase.load(kb_path)
            
            return {
                "id": kb.id,
                "title": kb.title,
                "description": kb.description,
                "created_at": kb.created_at.isoformat(),
                "updated_at": kb.updated_at.isoformat(),
                "parent_kb": kb.parent_kb,
                "relationships": kb.relationships,
                "tags": kb.tags,
                "path": str(kb.path)
            }
            
        except Exception as e:
            return {"error": f"Failed to get current KB: {str(e)}"}
    
    @mcp.tool()
    def rename_kb(kb_id: str, new_title: str) -> Dict[str, Any]:
        """Rename a knowledge base.
        
        Args:
            kb_id: ID of the knowledge base to rename
            new_title: New title for the KB
        
        Returns:
            Updated KB details or error
        """
        try:
            kb_path = state.storage_path / kb_id
            
            if not kb_path.exists():
                return {"error": f"Knowledge base '{kb_id}' not found"}
            
            # Load KB
            kb = KnowledgeBase.load(kb_path)
            
            # Update title
            old_title = kb.title
            kb.title = new_title
            
            # Save updated metadata
            kb.save(state.storage_path)
            
            return {
                "message": f"Renamed KB from '{old_title}' to '{new_title}'",
                "id": kb.id,
                "title": kb.title,
                "old_title": old_title
            }
            
        except Exception as e:
            return {"error": f"Failed to rename knowledge base: {str(e)}"}
    
    @mcp.tool()
    def delete_kb(kb_id: str, confirm: bool = False) -> Dict[str, Any]:
        """Delete a knowledge base.
        
        Args:
            kb_id: ID of the knowledge base to delete
            confirm: Must be True to confirm deletion
        
        Returns:
            Confirmation message or error
        """
        if not confirm:
            return {
                "error": "Deletion not confirmed. Set confirm=True to delete.",
                "warning": f"This will permanently delete KB '{kb_id}' and all its contents."
            }
        
        try:
            kb_path = state.storage_path / kb_id
            
            if not kb_path.exists():
                return {"error": f"Knowledge base '{kb_id}' not found"}
            
            # Load KB to get title
            kb = KnowledgeBase.load(kb_path)
            title = kb.title
            
            # Delete KB
            kb.delete()
            
            # Clear selection if this was the current KB
            if state.current_kb == kb_id:
                state.current_kb = None
            
            return {
                "message": f"Deleted knowledge base: {title}",
                "kb_id": kb_id
            }
            
        except Exception as e:
            return {"error": f"Failed to delete knowledge base: {str(e)}"}
    
    @mcp.tool()
    def derive_kb(
        source_kb_id: str,
        title: str,
        description: str = "",
        categories_to_copy: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a derived knowledge base from an existing one.
        
        Args:
            source_kb_id: ID of the source knowledge base
            title: Title for the new derived KB
            description: Description for the new KB
            categories_to_copy: Optional list of categories to copy (copies all if None)
            tags: Tags for the new KB
        
        Returns:
            New KB details or error
        """
        try:
            source_path = state.storage_path / source_kb_id
            
            if not source_path.exists():
                return {"error": f"Source knowledge base '{source_kb_id}' not found"}
            
            # Load source KB
            source_kb = KnowledgeBase.load(source_path)
            
            # Create derived KB
            derived_kb = KnowledgeBase(
                title=title,
                description=description or f"Derived from {source_kb.title}",
                parent_kb=source_kb_id,
                tags=tags or ["derived"]
            )
            
            # Add relationship to source
            derived_kb.relationships.append(source_kb_id)
            
            # Save derived KB
            derived_kb.save(state.storage_path)
            
            # Copy categories if specified
            if categories_to_copy:
                for category_name in categories_to_copy:
                    source_category = source_path / category_name
                    if source_category.exists() and source_category.is_dir():
                        dest_category = derived_kb.path / category_name
                        shutil.copytree(source_category, dest_category)
            elif categories_to_copy is None:
                # Copy all categories
                for item in source_path.iterdir():
                    if item.is_dir() and not item.name.startswith('.'):
                        dest_item = derived_kb.path / item.name
                        shutil.copytree(item, dest_item)
            
            return {
                "id": derived_kb.id,
                "title": derived_kb.title,
                "parent_kb": derived_kb.parent_kb,
                "source_title": source_kb.title,
                "path": str(derived_kb.path)
            }
            
        except Exception as e:
            return {"error": f"Failed to derive knowledge base: {str(e)}"}
    
    @mcp.tool()
    def export_kb(kb_id: str, export_path: Optional[str] = None) -> Dict[str, Any]:
        """Export a knowledge base to a JSON file.
        
        Args:
            kb_id: ID of the knowledge base to export
            export_path: Optional path for the export file
        
        Returns:
            Export details or error
        """
        try:
            kb_path = state.storage_path / kb_id
            
            if not kb_path.exists():
                return {"error": f"Knowledge base '{kb_id}' not found"}
            
            # Load KB
            kb = KnowledgeBase.load(kb_path)
            
            # Collect all data
            export_data = {
                "metadata": kb.to_dict(),
                "categories": [],
                "notes": []
            }
            
            # Export categories
            categories = Category.list_all(kb_path)
            for category in categories:
                export_data["categories"].append(category.to_dict())
                
                # Export notes in this category
                notes = Note.list_all(category.path)
                for note in notes:
                    note_data = note.to_dict()
                    note_data["category"] = category.relative_path
                    export_data["notes"].append(note_data)
            
            # Determine export path
            if not export_path:
                export_path = str(state.storage_path / f"{kb_id}_export.json")
            
            # Save export
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            return {
                "message": f"Exported KB '{kb.title}' successfully",
                "export_path": export_path,
                "stats": {
                    "categories": len(export_data["categories"]),
                    "notes": len(export_data["notes"])
                }
            }
            
        except Exception as e:
            return {"error": f"Failed to export knowledge base: {str(e)}"}
    
    @mcp.tool()
    def import_kb(import_path: str, new_title: Optional[str] = None) -> Dict[str, Any]:
        """Import a knowledge base from a JSON file.
        
        Args:
            import_path: Path to the import file
            new_title: Optional new title for the imported KB
        
        Returns:
            Import details or error
        """
        try:
            # Load import data
            with open(import_path, 'r') as f:
                import_data = json.load(f)
            
            # Create KB from metadata
            metadata = import_data.get("metadata", {})
            kb = KnowledgeBase(
                title=new_title or metadata.get("title", "Imported KB"),
                description=metadata.get("description", ""),
                tags=metadata.get("tags", ["imported"])
            )
            
            # Save KB
            kb.save(state.storage_path)
            
            # Import categories
            for category_data in import_data.get("categories", []):
                category_path = kb.path / category_data["relative_path"]
                ensure_directory(category_path)
                
                category = Category(
                    name=category_data["name"],
                    description=category_data.get("description", ""),
                    parent=category_data.get("parent"),
                    tags=category_data.get("tags", [])
                )
                category.path = category_path
                category.relative_path = category_data["relative_path"]
                category.save()
            
            # Import notes
            for note_data in import_data.get("notes", []):
                category_path = kb.path / note_data["category"]
                
                note = Note(
                    title=note_data["title"],
                    content=note_data.get("content", ""),
                    tags=note_data.get("tags", []),
                    linked_notes=note_data.get("linked_notes", []),
                    linked_kbs=note_data.get("linked_kbs", [])
                )
                note.save(category_path)
            
            return {
                "message": f"Imported KB '{kb.title}' successfully",
                "id": kb.id,
                "path": str(kb.path),
                "stats": {
                    "categories": len(import_data.get("categories", [])),
                    "notes": len(import_data.get("notes", []))
                }
            }
            
        except Exception as e:
            return {"error": f"Failed to import knowledge base: {str(e)}"}