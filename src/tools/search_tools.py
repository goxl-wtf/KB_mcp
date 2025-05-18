"""Search and Discovery Tools

Tools for searching and discovering content within knowledge bases.
"""

import re
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Any, Set
from datetime import datetime

import fastmcp

from models import Note, Category, KnowledgeBase
from utils import get_content_preview
from utils.token_utils import TokenCounter, PaginatedResponse, ResponseBuilder


def register_search_tools(mcp: fastmcp.FastMCP, state):
    """Register all search and discovery tools with the MCP server."""
    
    @mcp.tool()
    def search_notes(
        query: str,
        kb_id: Optional[str] = None,
        category_path: Optional[str] = None,
        tags: Optional[List[str]] = None,
        search_content: bool = True,
        search_title: bool = True,
        case_sensitive: bool = False,
        regex: bool = False,
        max_results: int = 50,
        page: Optional[int] = None
    ) -> Dict[str, Any]:
        """Search for notes across knowledge bases.
        
        Args:
            query: Search query string
            kb_id: Optional KB to search in (uses current KB if not specified)
            category_path: Optional category to limit search to
            tags: Optional tags to filter by
            search_content: Whether to search in note content
            search_title: Whether to search in note titles
            case_sensitive: Whether search is case-sensitive
            regex: Whether to treat query as regex
            max_results: Maximum number of results to return
        
        Returns:
            Dictionary with search results and pagination info
        """
        results = []
        response_builder = ResponseBuilder()
        
        # Determine search scope
        if kb_id:
            kb_path = state.storage_path / kb_id
            if not kb_path.exists():
                return [{"error": f"Knowledge base '{kb_id}' not found"}]
        elif state.current_kb:
            kb_path = state.storage_path / state.current_kb
        else:
            # Search all KBs
            kb_path = state.storage_path
        
        # Determine category scope
        if category_path:
            search_path = kb_path / category_path
            if not search_path.exists():
                return [{"error": f"Category '{category_path}' not found"}]
        else:
            search_path = kb_path
        
        # Prepare search pattern
        if not regex:
            query = re.escape(query)
        
        if not case_sensitive:
            pattern = re.compile(query, re.IGNORECASE)
        else:
            pattern = re.compile(query)
        
        # Search for notes
        for note_path in search_path.rglob("*.md"):
            try:
                note = Note.load(note_path)
                
                # Filter by tags if specified
                if tags:
                    if not any(tag in note.tags for tag in tags):
                        continue
                
                # Calculate relevance score
                score = 0
                matches = []
                
                # Search in title
                if search_title:
                    title_matches = pattern.findall(note.title)
                    if title_matches:
                        score += len(title_matches) * 10  # Title matches weighted higher
                        matches.extend([f"Title: {m}" for m in title_matches[:3]])
                
                # Search in content
                if search_content:
                    content_matches = pattern.findall(note.content)
                    if content_matches:
                        score += len(content_matches)
                        # Extract context around matches
                        for match in content_matches[:3]:
                            context = _extract_context(note.content, match, 50)
                            matches.append(f"Content: ...{context}...")
                
                if score > 0:
                    # Get relative paths
                    kb_root = _find_kb_root(note_path)
                    rel_path = str(note_path.parent.relative_to(kb_root))
                    kb_id = kb_root.name
                    
                    # Create snippet with context
                    snippet = get_content_preview(note.content, max_length=1000)
                    
                    results.append({
                        "note_id": note.id,
                        "title": note.title,
                        "kb_id": kb_id,
                        "category_path": rel_path if rel_path != "." else "/",
                        "score": score,
                        "matches": matches,
                        "snippet": snippet,
                        "tags": note.tags,
                        "created_at": note.created_at.isoformat(),
                        "updated_at": note.updated_at.isoformat()
                    })
                
            except Exception as e:
                print(f"Error processing note {note_path}: {e}")
                continue
        
        # Sort by relevance score
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # Limit and paginate results
        limited_results = results[:max_results]
        
        # Use pagination
        paginated = PaginatedResponse(limited_results)
        return paginated.get_page(page or 1)
    
    @mcp.tool()
    def search_with_ripgrep(
        pattern: str,
        path: Optional[str] = None,
        file_type: str = "md",
        context_lines: int = 2,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """Advanced search using ripgrep for better performance.
        
        Args:
            pattern: Search pattern (supports regex)
            path: Path to search in (relative to current KB or absolute)
            file_type: File type to search (default: md)
            context_lines: Number of context lines to show
            max_results: Maximum number of results
        
        Returns:
            List of search results with file paths and contexts
        """
        results = []
        
        # Determine search path
        if state.current_kb:
            base_path = state.storage_path / state.current_kb
        else:
            base_path = state.storage_path
            
        if path:
            search_path = base_path / path
        else:
            search_path = base_path
        
        if not search_path.exists():
            return [{"error": f"Path '{search_path}' not found"}]
        
        # Build ripgrep command
        cmd = [
            "rg",  # Use ripgrep
            "-n",  # Show line numbers
            "--json",  # JSON output
            f"-C{context_lines}",  # Context lines
            f"-t{file_type}",  # File type
            "--max-count", str(max_results),
            pattern,
            str(search_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Parse JSON output
                for line in result.stdout.strip().split('\n'):
                    if line:
                        try:
                            match_data = eval(line)  # ripgrep outputs JSON-like but not valid JSON
                            if match_data.get("type") == "match":
                                data = match_data["data"]
                                file_path = Path(data["path"]["text"])
                                
                                # Get relative path and KB info
                                kb_root = _find_kb_root(file_path)
                                rel_path = str(file_path.relative_to(kb_root))
                                kb_id = kb_root.name
                                
                                results.append({
                                    "file": rel_path,
                                    "kb_id": kb_id,
                                    "line_number": data["line_number"],
                                    "match": data["lines"]["text"].strip(),
                                    "context": data.get("lines", {}).get("text", "")
                                })
                        except:
                            pass
            
            return results[:max_results]
            
        except FileNotFoundError:
            return [{"error": "ripgrep (rg) not found. Please install ripgrep for advanced search."}]
        except Exception as e:
            return [{"error": f"Search failed: {str(e)}"}]
    
    @mcp.tool()
    def find_related_notes(
        note_id: str,
        kb_id: Optional[str] = None,
        max_results: int = 10,
        include_linked: bool = True,
        include_similar: bool = True
    ) -> List[Dict[str, Any]]:
        """Find notes related to a given note.
        
        Args:
            note_id: ID of the reference note
            kb_id: Optional KB to search in
            max_results: Maximum number of results
            include_linked: Include directly linked notes
            include_similar: Include notes with similar content/tags
        
        Returns:
            List of related notes with relationship info
        """
        related = []
        seen = set()
        
        # Find the reference note
        if kb_id:
            kb_path = state.storage_path / kb_id
        elif state.current_kb:
            kb_path = state.storage_path / state.current_kb
        else:
            return [{"error": "No KB specified or selected"}]
        
        # Find the note
        note_path = None
        for md_file in kb_path.rglob(f"{note_id}.md"):
            note_path = md_file
            break
        
        if not note_path:
            return [{"error": f"Note '{note_id}' not found"}]
        
        ref_note = Note.load(note_path)
        
        # Add directly linked notes
        if include_linked:
            for linked_id in ref_note.linked_notes:
                if linked_id not in seen:
                    seen.add(linked_id)
                    # Find linked note
                    for md_file in kb_path.rglob(f"{linked_id}.md"):
                        try:
                            linked_note = Note.load(md_file)
                            related.append({
                                "note_id": linked_note.id,
                                "title": linked_note.title,
                                "relationship": "directly_linked",
                                "score": 100,
                                "tags": linked_note.tags,
                                "preview": get_content_preview(linked_note.content, 100)
                            })
                        except:
                            pass
                        break
        
        # Find notes that link to this note
        if include_linked:
            for md_file in kb_path.rglob("*.md"):
                try:
                    note = Note.load(md_file)
                    if note_id in note.linked_notes and note.id not in seen:
                        seen.add(note.id)
                        related.append({
                            "note_id": note.id,
                            "title": note.title,
                            "relationship": "links_to_this",
                            "score": 90,
                            "tags": note.tags,
                            "preview": get_content_preview(note.content, 100)
                        })
                except:
                    pass
        
        # Find similar notes by tags
        if include_similar and ref_note.tags:
            for md_file in kb_path.rglob("*.md"):
                try:
                    note = Note.load(md_file)
                    if note.id != note_id and note.id not in seen:
                        # Calculate tag similarity
                        common_tags = set(note.tags) & set(ref_note.tags)
                        if common_tags:
                            similarity_score = len(common_tags) * 20
                            seen.add(note.id)
                            related.append({
                                "note_id": note.id,
                                "title": note.title,
                                "relationship": "similar_tags",
                                "score": similarity_score,
                                "common_tags": list(common_tags),
                                "tags": note.tags,
                                "preview": get_content_preview(note.content, 100)
                            })
                except:
                    pass
        
        # Sort by score and limit results
        related.sort(key=lambda x: x["score"], reverse=True)
        return related[:max_results]
    
    @mcp.tool()
    def search_by_date(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        kb_id: Optional[str] = None,
        modified: bool = True,
        created: bool = False
    ) -> List[Dict[str, Any]]:
        """Search for notes by creation or modification date.
        
        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            kb_id: Optional KB to search in
            modified: Search by modification date
            created: Search by creation date
        
        Returns:
            List of notes within date range
        """
        results = []
        
        # Parse dates
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        # Determine search scope
        if kb_id:
            kb_path = state.storage_path / kb_id
        elif state.current_kb:
            kb_path = state.storage_path / state.current_kb
        else:
            kb_path = state.storage_path
        
        # Search notes
        for note_path in kb_path.rglob("*.md"):
            try:
                note = Note.load(note_path)
                
                # Check dates
                in_range = False
                
                if modified:
                    if start_dt and note.updated_at < start_dt:
                        continue
                    if end_dt and note.updated_at > end_dt:
                        continue
                    in_range = True
                
                if created:
                    if start_dt and note.created_at < start_dt:
                        continue
                    if end_dt and note.created_at > end_dt:
                        continue
                    in_range = True
                
                if in_range:
                    kb_root = _find_kb_root(note_path)
                    rel_path = str(note_path.parent.relative_to(kb_root))
                    
                    results.append({
                        "note_id": note.id,
                        "title": note.title,
                        "kb_id": kb_root.name,
                        "category_path": rel_path if rel_path != "." else "/",
                        "created_at": note.created_at.isoformat(),
                        "updated_at": note.updated_at.isoformat(),
                        "tags": note.tags,
                        "preview": get_content_preview(note.content, 100)
                    })
                    
            except Exception as e:
                print(f"Error processing note {note_path}: {e}")
                continue
        
        # Sort by date
        if modified:
            results.sort(key=lambda x: x["updated_at"], reverse=True)
        else:
            results.sort(key=lambda x: x["created_at"], reverse=True)
        
        return results
    
    @mcp.tool()
    def find_orphaned_notes() -> List[Dict[str, Any]]:
        """Find notes that have broken links or references.
        
        Returns:
            List of notes with broken links
        """
        orphaned = []
        
        # Search all KBs
        for kb_dir in state.storage_path.iterdir():
            if kb_dir.is_dir() and (kb_dir / "meta.json").exists():
                kb_id = kb_dir.name
                
                # Collect all note IDs in this KB
                note_ids = set()
                for note_path in kb_dir.rglob("*.md"):
                    note_ids.add(note_path.stem)
                
                # Check each note for broken links
                for note_path in kb_dir.rglob("*.md"):
                    try:
                        note = Note.load(note_path)
                        broken_links = []
                        
                        # Check linked notes
                        for linked_id in note.linked_notes:
                            if linked_id not in note_ids:
                                broken_links.append({
                                    "type": "note",
                                    "id": linked_id
                                })
                        
                        # Check links in content
                        content_links = note.extract_links_from_content()
                        for link in content_links:
                            if link not in note_ids:
                                broken_links.append({
                                    "type": "content_link",
                                    "id": link
                                })
                        
                        if broken_links:
                            rel_path = str(note_path.parent.relative_to(kb_dir))
                            orphaned.append({
                                "note_id": note.id,
                                "title": note.title,
                                "kb_id": kb_id,
                                "category_path": rel_path if rel_path != "." else "/",
                                "broken_links": broken_links,
                                "total_broken": len(broken_links)
                            })
                    
                    except Exception as e:
                        print(f"Error checking note {note_path}: {e}")
                        continue
        
        return orphaned


def _extract_context(content: str, match: str, context_size: int = 50) -> str:
    """Extract context around a match in content."""
    index = content.find(match)
    if index == -1:
        return match
    
    start = max(0, index - context_size)
    end = min(len(content), index + len(match) + context_size)
    
    context = content[start:end]
    if start > 0:
        context = "..." + context
    if end < len(content):
        context = context + "..."
    
    return context


def _find_kb_root(path: Path) -> Path:
    """Find the KB root directory for a given path."""
    current = path.parent
    while current != current.parent:
        if (current / "meta.json").exists():
            return current
        current = current.parent
    return path.parent  # Fallback