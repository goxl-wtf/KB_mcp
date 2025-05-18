"""Note Management Tools

Tools for creating, editing, and managing notes within knowledge bases.
"""

from pathlib import Path
from typing import List, Dict, Optional, Any
import shutil

import fastmcp

from models import Note, Category
from utils import validate_id, get_safe_filename, get_content_preview


def register_note_tools(mcp: fastmcp.FastMCP, state):
    """Register all note management tools with the MCP server."""
    
    @mcp.tool()
    def create_note(
        title: str,
        content: str = "",
        category_path: Optional[str] = None,
        tags: Optional[List[str]] = None,
        linked_notes: Optional[List[str]] = None,
        linked_kbs: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a new note in the current knowledge base.
        
        Args:
            title: Title of the note
            content: Content of the note in Markdown
            category_path: Category to place the note in (None for root)
            tags: Optional list of tags
            linked_notes: Optional list of linked note IDs
            linked_kbs: Optional list of linked KB IDs
        
        Returns:
            Note details or error
        """
        if not state.current_kb:
            return {"error": "No knowledge base selected"}
        
        try:
            kb_path = state.storage_path / state.current_kb
            
            # Determine category path
            if category_path:
                cat_path = kb_path / category_path
                if not cat_path.exists():
                    return {"error": f"Category '{category_path}' not found"}
            else:
                cat_path = kb_path
            
            # Create note
            note = Note(
                title=title,
                content=content,
                tags=tags or [],
                linked_notes=linked_notes or [],
                linked_kbs=linked_kbs or []
            )
            
            # Extract links from content
            content_links = note.extract_links_from_content()
            for link in content_links:
                if link not in note.linked_notes:
                    note.linked_notes.append(link)
            
            # Save note
            note.save(cat_path)
            
            return {
                "id": note.id,
                "title": note.title,
                "path": str(note.path),
                "category_path": category_path or "/",
                "created_at": note.created_at.isoformat(),
                "tags": note.tags,
                "linked_notes": note.linked_notes,
                "linked_kbs": note.linked_kbs
            }
            
        except Exception as e:
            return {"error": f"Failed to create note: {str(e)}"}
    
    @mcp.tool()
    def read_note(note_id: str, category_path: Optional[str] = None) -> Dict[str, Any]:
        """Read a note by ID.
        
        Args:
            note_id: ID of the note to read
            category_path: Optional category path to search in
        
        Returns:
            Note content and metadata or error
        """
        if not state.current_kb:
            return {"error": "No knowledge base selected"}
        
        try:
            kb_path = state.storage_path / state.current_kb
            
            # Find the note
            if category_path:
                cat_path = kb_path / category_path
                note_path = cat_path / f"{note_id}.md"
            else:
                # Search all categories
                note_path = None
                for md_file in kb_path.rglob(f"{note_id}.md"):
                    note_path = md_file
                    break
                
                if not note_path:
                    return {"error": f"Note '{note_id}' not found"}
            
            if not note_path.exists():
                return {"error": f"Note '{note_id}' not found"}
            
            # Load note
            note = Note.load(note_path)
            
            # Get category path
            relative_cat_path = str(note_path.parent.relative_to(kb_path))
            if relative_cat_path == ".":
                relative_cat_path = "/"
            
            return {
                "id": note.id,
                "title": note.title,
                "content": note.content,
                "category_path": relative_cat_path,
                "created_at": note.created_at.isoformat(),
                "updated_at": note.updated_at.isoformat(),
                "tags": note.tags,
                "linked_notes": note.linked_notes,
                "linked_kbs": note.linked_kbs,
                "path": str(note.path)
            }
            
        except Exception as e:
            return {"error": f"Failed to read note: {str(e)}"}
    
    @mcp.tool()
    def update_note(
        note_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        linked_notes: Optional[List[str]] = None,
        linked_kbs: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Update an existing note.
        
        Args:
            note_id: ID of the note to update
            title: New title (optional)
            content: New content (optional)
            tags: New tags list (optional)
            linked_notes: New linked notes list (optional)
            linked_kbs: New linked KBs list (optional)
        
        Returns:
            Updated note details or error
        """
        if not state.current_kb:
            return {"error": "No knowledge base selected"}
        
        try:
            kb_path = state.storage_path / state.current_kb
            
            # Find the note
            note_path = None
            for md_file in kb_path.rglob(f"{note_id}.md"):
                note_path = md_file
                break
            
            if not note_path:
                return {"error": f"Note '{note_id}' not found"}
            
            # Load note
            note = Note.load(note_path)
            category_path = note_path.parent
            
            # Update fields if provided
            if title is not None:
                note.title = title
            
            if content is not None:
                note.content = content
                # Extract new links
                content_links = note.extract_links_from_content()
                note.linked_notes = list(set(note.linked_notes + content_links))
            
            if tags is not None:
                note.tags = tags
            
            if linked_notes is not None:
                note.linked_notes = linked_notes
            
            if linked_kbs is not None:
                note.linked_kbs = linked_kbs
            
            # Save updated note
            note.save(category_path)
            
            return {
                "id": note.id,
                "title": note.title,
                "updated_at": note.updated_at.isoformat(),
                "tags": note.tags,
                "linked_notes": note.linked_notes,
                "linked_kbs": note.linked_kbs
            }
            
        except Exception as e:
            return {"error": f"Failed to update note: {str(e)}"}
    
    @mcp.tool()
    def delete_note(note_id: str, confirm: bool = False) -> Dict[str, Any]:
        """Delete a note.
        
        Args:
            note_id: ID of the note to delete
            confirm: Must be True to confirm deletion
        
        Returns:
            Confirmation message or error
        """
        if not confirm:
            return {
                "error": "Deletion not confirmed. Set confirm=True to delete.",
                "warning": f"This will permanently delete note '{note_id}'"
            }
        
        if not state.current_kb:
            return {"error": "No knowledge base selected"}
        
        try:
            kb_path = state.storage_path / state.current_kb
            
            # Find the note
            note_path = None
            for md_file in kb_path.rglob(f"{note_id}.md"):
                note_path = md_file
                break
            
            if not note_path:
                return {"error": f"Note '{note_id}' not found"}
            
            # Load note to get title
            note = Note.load(note_path)
            title = note.title
            
            # Delete note
            note.delete()
            
            return {
                "message": f"Deleted note: {title}",
                "note_id": note_id
            }
            
        except Exception as e:
            return {"error": f"Failed to delete note: {str(e)}"}
    
    @mcp.tool()
    def move_note(
        note_id: str,
        new_category_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Move a note to a different category.
        
        Args:
            note_id: ID of the note to move
            new_category_path: New category path (None for root)
        
        Returns:
            Updated note location or error
        """
        if not state.current_kb:
            return {"error": "No knowledge base selected"}
        
        try:
            kb_path = state.storage_path / state.current_kb
            
            # Find the note
            note_path = None
            for md_file in kb_path.rglob(f"{note_id}.md"):
                note_path = md_file
                break
            
            if not note_path:
                return {"error": f"Note '{note_id}' not found"}
            
            # Determine new category
            if new_category_path:
                new_cat_path = kb_path / new_category_path
                if not new_cat_path.exists():
                    return {"error": f"Category '{new_category_path}' not found"}
            else:
                new_cat_path = kb_path
            
            # Load note
            note = Note.load(note_path)
            old_category = str(note_path.parent.relative_to(kb_path))
            
            # Move note
            note.move_to(new_cat_path)
            
            new_category = str(new_cat_path.relative_to(kb_path))
            if new_category == ".":
                new_category = "/"
            
            return {
                "message": f"Moved note '{note.title}'",
                "note_id": note_id,
                "old_category": old_category,
                "new_category": new_category,
                "new_path": str(note.path)
            }
            
        except Exception as e:
            return {"error": f"Failed to move note: {str(e)}"}
    
    @mcp.tool()
    def list_notes(
        category_path: Optional[str] = None,
        recursive: bool = False,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """List notes in the current knowledge base.
        
        Args:
            category_path: Optional category to list from
            recursive: Whether to include notes from subcategories
            tags: Optional tags to filter by
        
        Returns:
            List of note summaries
        """
        if not state.current_kb:
            return [{"error": "No knowledge base selected"}]
        
        try:
            kb_path = state.storage_path / state.current_kb
            notes = []
            
            # Determine search path
            if category_path:
                search_path = kb_path / category_path
                if not search_path.exists():
                    return [{"error": f"Category '{category_path}' not found"}]
            else:
                search_path = kb_path
            
            # Find notes
            if recursive:
                pattern = "**/*.md"
            else:
                pattern = "*.md"
            
            for note_path in search_path.glob(pattern):
                try:
                    note = Note.load(note_path)
                    
                    # Filter by tags if specified
                    if tags:
                        if not any(tag in note.tags for tag in tags):
                            continue
                    
                    # Get relative category path
                    cat_path = str(note_path.parent.relative_to(kb_path))
                    if cat_path == ".":
                        cat_path = "/"
                    
                    notes.append({
                        "id": note.id,
                        "title": note.title,
                        "category_path": cat_path,
                        "preview": get_content_preview(note.content, max_length=150),
                        "tags": note.tags,
                        "created_at": note.created_at.isoformat(),
                        "updated_at": note.updated_at.isoformat(),
                        "linked_notes": len(note.linked_notes),
                        "linked_kbs": len(note.linked_kbs)
                    })
                except Exception as e:
                    print(f"Error loading note {note_path}: {e}")
            
            return sorted(notes, key=lambda n: n["title"])
            
        except Exception as e:
            return [{"error": f"Failed to list notes: {str(e)}"}]
    
    @mcp.tool()
    def link_notes(
        source_note_id: str,
        target_note_id: str,
        bidirectional: bool = True
    ) -> Dict[str, Any]:
        """Create a link between two notes.
        
        Args:
            source_note_id: Source note ID
            target_note_id: Target note ID
            bidirectional: Whether to create a link in both directions
        
        Returns:
            Link details or error
        """
        if not state.current_kb:
            return {"error": "No knowledge base selected"}
        
        try:
            kb_path = state.storage_path / state.current_kb
            
            # Find source note
            source_path = None
            for md_file in kb_path.rglob(f"{source_note_id}.md"):
                source_path = md_file
                break
            
            if not source_path:
                return {"error": f"Source note '{source_note_id}' not found"}
            
            # Find target note
            target_path = None
            for md_file in kb_path.rglob(f"{target_note_id}.md"):
                target_path = md_file
                break
            
            if not target_path:
                return {"error": f"Target note '{target_note_id}' not found"}
            
            # Load notes
            source_note = Note.load(source_path)
            target_note = Note.load(target_path)
            
            # Create links
            source_note.add_link(target_note_id, "note")
            source_note.save(source_path.parent)
            
            if bidirectional:
                target_note.add_link(source_note_id, "note")
                target_note.save(target_path.parent)
            
            return {
                "message": f"Linked '{source_note.title}' to '{target_note.title}'",
                "source_id": source_note_id,
                "target_id": target_note_id,
                "bidirectional": bidirectional
            }
            
        except Exception as e:
            return {"error": f"Failed to link notes: {str(e)}"}
    
    @mcp.tool()
    def unlink_notes(
        source_note_id: str,
        target_note_id: str,
        bidirectional: bool = True
    ) -> Dict[str, Any]:
        """Remove a link between two notes.
        
        Args:
            source_note_id: Source note ID
            target_note_id: Target note ID
            bidirectional: Whether to remove links in both directions
        
        Returns:
            Unlink details or error
        """
        if not state.current_kb:
            return {"error": "No knowledge base selected"}
        
        try:
            kb_path = state.storage_path / state.current_kb
            
            # Find source note
            source_path = None
            for md_file in kb_path.rglob(f"{source_note_id}.md"):
                source_path = md_file
                break
            
            if not source_path:
                return {"error": f"Source note '{source_note_id}' not found"}
            
            # Find target note
            target_path = None
            for md_file in kb_path.rglob(f"{target_note_id}.md"):
                target_path = md_file
                break
            
            if not target_path:
                return {"error": f"Target note '{target_note_id}' not found"}
            
            # Load notes
            source_note = Note.load(source_path)
            target_note = Note.load(target_path)
            
            # Remove links
            source_note.remove_link(target_note_id, "note")
            source_note.save(source_path.parent)
            
            if bidirectional:
                target_note.remove_link(source_note_id, "note")
                target_note.save(target_path.parent)
            
            return {
                "message": f"Unlinked '{source_note.title}' from '{target_note.title}'",
                "source_id": source_note_id,
                "target_id": target_note_id,
                "bidirectional": bidirectional
            }
            
        except Exception as e:
            return {"error": f"Failed to unlink notes: {str(e)}"}