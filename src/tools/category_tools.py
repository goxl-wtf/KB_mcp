"""Category Management Tools

Tools for creating and managing categories within knowledge bases.
"""

from pathlib import Path
from typing import List, Dict, Optional, Any
import shutil

import fastmcp

from models import Category, Note
from utils import ensure_directory, validate_id, get_safe_filename


def register_category_tools(mcp: fastmcp.FastMCP, state):
    """Register all category management tools with the MCP server."""
    
    @mcp.tool()
    def create_category(
        name: str,
        parent_path: Optional[str] = None,
        description: str = "",
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new category in the current knowledge base.
        
        Args:
            name: Name of the category
            parent_path: Parent category path (relative to KB root, None for root)
            description: Description of the category
            tags: Optional list of tags
        
        Returns:
            Category details or error
        """
        if not state.current_kb:
            return {"error": "No knowledge base selected"}
        
        try:
            kb_path = state.storage_path / state.current_kb
            
            # Determine parent path
            if parent_path:
                parent_full_path = kb_path / parent_path
                if not parent_full_path.exists():
                    return {"error": f"Parent category '{parent_path}' not found"}
            else:
                parent_full_path = kb_path
            
            # Create category path
            category_id = get_safe_filename(name)
            if not validate_id(category_id):
                return {"error": f"Invalid category name: {name}"}
            
            category_path = parent_full_path / category_id
            
            if category_path.exists():
                return {"error": f"Category '{name}' already exists in this location"}
            
            # Create category
            category = Category(
                name=name,
                description=description,
                parent=parent_path,
                tags=tags or []
            )
            
            category.path = category_path
            category.relative_path = str(category_path.relative_to(kb_path))
            
            # Save category
            category.save()
            
            return {
                "name": category.name,
                "relative_path": category.relative_path,
                "parent": category.parent,
                "created_at": category.created_at.isoformat()
            }
            
        except Exception as e:
            return {"error": f"Failed to create category: {str(e)}"}
    
    @mcp.tool()
    def list_categories(
        parent_path: Optional[str] = None,
        recursive: bool = False
    ) -> List[Dict[str, Any]]:
        """List categories in the current knowledge base.
        
        Args:
            parent_path: Optional parent category path to list from
            recursive: Whether to include subcategories recursively
        
        Returns:
            List of category details
        """
        if not state.current_kb:
            return [{"error": "No knowledge base selected"}]
        
        try:
            kb_path = state.storage_path / state.current_kb
            
            if recursive:
                # List all categories
                categories = Category.list_all(kb_path)
            else:
                # List only direct children
                if parent_path:
                    parent_full_path = kb_path / parent_path
                    if not parent_full_path.exists():
                        return [{"error": f"Parent category '{parent_path}' not found"}]
                    parent_category = Category.load(parent_full_path, kb_path)
                    categories = parent_category.get_subcategories(kb_path)
                else:
                    # List root-level categories
                    categories = []
                    for item in kb_path.iterdir():
                        if item.is_dir() and not item.name.startswith('.'):
                            try:
                                category = Category.load(item, kb_path)
                                if not category.parent:  # Root level
                                    categories.append(category)
                            except:
                                pass
            
            # Filter by parent if specified and recursive is True
            if parent_path and recursive:
                categories = [c for c in categories if c.parent == parent_path 
                             or (c.parent and c.parent.startswith(parent_path + "/"))]
            
            return [{
                "name": cat.name,
                "relative_path": cat.relative_path,
                "parent": cat.parent,
                "description": cat.description,
                "tags": cat.tags,
                "created_at": cat.created_at.isoformat(),
                "updated_at": cat.updated_at.isoformat(),
                "note_count": len(cat.get_notes()),
                "subcategory_count": len(cat.get_subcategories(kb_path))
            } for cat in categories]
            
        except Exception as e:
            return [{"error": f"Failed to list categories: {str(e)}"}]
    
    @mcp.tool()
    def rename_category(
        category_path: str,
        new_name: str
    ) -> Dict[str, Any]:
        """Rename a category.
        
        Args:
            category_path: Path to the category (relative to KB root)
            new_name: New name for the category
        
        Returns:
            Updated category details or error
        """
        if not state.current_kb:
            return {"error": "No knowledge base selected"}
        
        try:
            kb_path = state.storage_path / state.current_kb
            old_path = kb_path / category_path
            
            if not old_path.exists():
                return {"error": f"Category '{category_path}' not found"}
            
            # Load category
            category = Category.load(old_path, kb_path)
            
            # Validate new name
            new_id = get_safe_filename(new_name)
            if not validate_id(new_id):
                return {"error": f"Invalid category name: {new_name}"}
            
            # Determine new path
            parent_path = old_path.parent
            new_path = parent_path / new_id
            
            if new_path.exists() and new_path != old_path:
                return {"error": f"Category '{new_name}' already exists in this location"}
            
            # Rename directory
            old_path.rename(new_path)
            
            # Update category
            old_name = category.name
            category.name = new_name
            category.path = new_path
            category.relative_path = str(new_path.relative_to(kb_path))
            category.save()
            
            return {
                "message": f"Renamed category from '{old_name}' to '{new_name}'",
                "old_path": category_path,
                "new_path": category.relative_path,
                "name": category.name
            }
            
        except Exception as e:
            return {"error": f"Failed to rename category: {str(e)}"}
    
    @mcp.tool()
    def move_category(
        category_path: str,
        new_parent_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Move a category to a different parent.
        
        Args:
            category_path: Path to the category to move
            new_parent_path: New parent category path (None for root)
        
        Returns:
            Updated category details or error
        """
        if not state.current_kb:
            return {"error": "No knowledge base selected"}
        
        try:
            kb_path = state.storage_path / state.current_kb
            source_path = kb_path / category_path
            
            if not source_path.exists():
                return {"error": f"Category '{category_path}' not found"}
            
            # Determine new parent
            if new_parent_path:
                new_parent = kb_path / new_parent_path
                if not new_parent.exists():
                    return {"error": f"Parent category '{new_parent_path}' not found"}
                
                # Check for circular reference
                if str(new_parent).startswith(str(source_path)):
                    return {"error": "Cannot move category to its own subdirectory"}
            else:
                new_parent = kb_path
            
            # Load category
            category = Category.load(source_path, kb_path)
            
            # Move category
            category.move_to(new_parent, kb_path)
            
            return {
                "message": f"Moved category '{category.name}'",
                "old_path": category_path,
                "new_path": category.relative_path,
                "parent": category.parent
            }
            
        except Exception as e:
            return {"error": f"Failed to move category: {str(e)}"}
    
    @mcp.tool()
    def delete_category(
        category_path: str,
        confirm: bool = False,
        delete_contents: bool = False
    ) -> Dict[str, Any]:
        """Delete a category.
        
        Args:
            category_path: Path to the category to delete
            confirm: Must be True to confirm deletion
            delete_contents: If True, delete all contents; if False, only delete if empty
        
        Returns:
            Confirmation message or error
        """
        if not confirm:
            return {
                "error": "Deletion not confirmed. Set confirm=True to delete.",
                "warning": f"This will delete category '{category_path}'" + 
                          (" and all its contents" if delete_contents else " (only if empty)")
            }
        
        if not state.current_kb:
            return {"error": "No knowledge base selected"}
        
        try:
            kb_path = state.storage_path / state.current_kb
            cat_path = kb_path / category_path
            
            if not cat_path.exists():
                return {"error": f"Category '{category_path}' not found"}
            
            # Load category
            category = Category.load(cat_path, kb_path)
            
            # Check if category has contents
            notes = category.get_notes()
            subcategories = category.get_subcategories(kb_path)
            
            if (notes or subcategories) and not delete_contents:
                return {
                    "error": "Category is not empty. Set delete_contents=True to delete with contents.",
                    "contents": {
                        "notes": len(notes),
                        "subcategories": len(subcategories)
                    }
                }
            
            # Delete category
            category.delete()
            
            return {
                "message": f"Deleted category: {category.name}",
                "path": category_path,
                "deleted_contents": {
                    "notes": len(notes),
                    "subcategories": len(subcategories)
                } if delete_contents else None
            }
            
        except Exception as e:
            return {"error": f"Failed to delete category: {str(e)}"}
    
    @mcp.tool()
    def get_category_contents(
        category_path: Optional[str] = None,
        include_notes: bool = True,
        include_subcategories: bool = True
    ) -> Dict[str, Any]:
        """Get the contents of a category.
        
        Args:
            category_path: Path to the category (None for KB root)
            include_notes: Whether to include notes in the response
            include_subcategories: Whether to include subcategories
        
        Returns:
            Category contents or error
        """
        if not state.current_kb:
            return {"error": "No knowledge base selected"}
        
        try:
            kb_path = state.storage_path / state.current_kb
            
            if category_path:
                cat_path = kb_path / category_path
                if not cat_path.exists():
                    return {"error": f"Category '{category_path}' not found"}
                category = Category.load(cat_path, kb_path)
            else:
                # Root level
                category = None
                cat_path = kb_path
            
            result = {
                "path": category_path or "/",
                "name": category.name if category else state.current_kb,
                "description": category.description if category else "Knowledge base root"
            }
            
            # Get notes
            if include_notes:
                if category:
                    notes = Note.list_all(cat_path)
                else:
                    # Get notes in root
                    notes = []
                    for item in cat_path.glob("*.md"):
                        try:
                            note = Note.load(item)
                            notes.append(note)
                        except:
                            pass
                
                result["notes"] = [{
                    "id": note.id,
                    "title": note.title,
                    "tags": note.tags,
                    "created_at": note.created_at.isoformat(),
                    "updated_at": note.updated_at.isoformat()
                } for note in notes]
            
            # Get subcategories
            if include_subcategories:
                if category:
                    subcategories = category.get_subcategories(kb_path)
                else:
                    # Get root categories
                    subcategories = []
                    for item in cat_path.iterdir():
                        if item.is_dir() and not item.name.startswith('.'):
                            try:
                                subcat = Category.load(item, kb_path)
                                if not subcat.parent:  # Root level
                                    subcategories.append(subcat)
                            except:
                                pass
                
                result["subcategories"] = [{
                    "name": subcat.name,
                    "relative_path": subcat.relative_path,
                    "description": subcat.description,
                    "tags": subcat.tags
                } for subcat in subcategories]
            
            return result
            
        except Exception as e:
            return {"error": f"Failed to get category contents: {str(e)}"}