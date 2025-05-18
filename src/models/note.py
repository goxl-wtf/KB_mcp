"""Note Model

Represents a note within a knowledge base.
Notes are stored as Markdown files with YAML frontmatter for metadata.
"""

import yaml
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict
import re


@dataclass
class Note:
    """Represents a note with content and metadata."""
    
    title: str
    content: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    linked_notes: List[str] = field(default_factory=list)  # Note IDs
    linked_kbs: List[str] = field(default_factory=list)    # KB IDs
    
    # Path information
    id: str = ""  # Filename without extension (derived from title)
    path: Optional[Path] = None
    category_path: str = ""  # Path relative to KB root
    
    def __post_init__(self):
        """Initialize ID from title if not provided."""
        if not self.id:
            self.id = self._title_to_id(self.title)
    
    @staticmethod
    def _title_to_id(title: str) -> str:
        """Convert a title to a valid filename."""
        # Replace spaces with underscores and remove special characters
        id_str = title.replace(" ", "_")
        # Keep only alphanumeric, underscore, and hyphen
        id_str = "".join(c for c in id_str if c.isalnum() or c in "_-")
        return id_str
    
    def save(self, category_path: Path):
        """Save note to disk as Markdown with YAML frontmatter."""
        if not self.id:
            self.id = self._title_to_id(self.title)
        
        # Determine file path
        filename = f"{self.id}.md"
        self.path = category_path / filename
        
        # Update timestamp
        self.updated_at = datetime.now()
        
        # Prepare frontmatter
        frontmatter = {
            'title': self.title,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'tags': self.tags,
            'linked_notes': self.linked_notes,
            'linked_kbs': self.linked_kbs,
        }
        
        # Combine frontmatter and content
        frontmatter_str = yaml.dump(frontmatter, default_flow_style=False)
        file_content = f"---\n{frontmatter_str}---\n\n{self.content}"
        
        # Write to file
        with open(self.path, 'w', encoding='utf-8') as f:
            f.write(file_content)
    
    @classmethod
    def load(cls, file_path: Path) -> "Note":
        """Load note from a Markdown file with YAML frontmatter."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract frontmatter and content
        frontmatter, body = cls._parse_frontmatter(content)
        
        # Convert datetime strings if present
        for date_field in ['created_at', 'updated_at']:
            if date_field in frontmatter:
                try:
                    frontmatter[date_field] = datetime.fromisoformat(frontmatter[date_field])
                except:
                    # If parsing fails, use current time
                    frontmatter[date_field] = datetime.now()
        
        # Create note instance
        note = cls(
            title=frontmatter.get('title', file_path.stem),
            content=body,
            created_at=frontmatter.get('created_at', datetime.now()),
            updated_at=frontmatter.get('updated_at', datetime.now()),
            tags=frontmatter.get('tags', []),
            linked_notes=frontmatter.get('linked_notes', []),
            linked_kbs=frontmatter.get('linked_kbs', []),
            id=file_path.stem,
            path=file_path
        )
        
        return note
    
    @staticmethod
    def _parse_frontmatter(content: str) -> tuple[Dict[str, Any], str]:
        """Parse YAML frontmatter from Markdown content."""
        # Check if content starts with frontmatter
        if not content.startswith('---'):
            return {}, content
        
        # Find the end of frontmatter
        pattern = r'^---\s*\n(.*?)\n---\s*\n'
        match = re.match(pattern, content, re.DOTALL)
        
        if not match:
            return {}, content
        
        # Parse YAML frontmatter
        try:
            frontmatter = yaml.safe_load(match.group(1))
            if frontmatter is None:
                frontmatter = {}
        except yaml.YAMLError:
            frontmatter = {}
        
        # Extract body content (everything after frontmatter)
        body = content[match.end():]
        
        return frontmatter, body
    
    @classmethod
    def list_all(cls, category_path: Path) -> List["Note"]:
        """List all notes in a category."""
        notes = []
        
        for file_path in category_path.glob("*.md"):
            try:
                note = cls.load(file_path)
                notes.append(note)
            except Exception as e:
                print(f"Error loading note at {file_path}: {e}")
        
        return sorted(notes, key=lambda n: n.title)
    
    def move_to(self, new_category_path: Path):
        """Move this note to a different category."""
        if not self.path:
            raise ValueError("Note path not set")
        
        new_path = new_category_path / self.path.name
        
        # Move the file
        import shutil
        shutil.move(str(self.path), str(new_path))
        
        # Update path
        self.path = new_path
    
    def delete(self):
        """Delete this note from disk."""
        if not self.path or not self.path.exists():
            raise FileNotFoundError(f"Note not found at {self.path}")
        
        self.path.unlink()
    
    def add_link(self, target_id: str, link_type: str = "note"):
        """Add a link to another note or KB."""
        if link_type == "note":
            if target_id not in self.linked_notes:
                self.linked_notes.append(target_id)
        elif link_type == "kb":
            if target_id not in self.linked_kbs:
                self.linked_kbs.append(target_id)
        else:
            raise ValueError(f"Invalid link type: {link_type}")
    
    def remove_link(self, target_id: str, link_type: str = "note"):
        """Remove a link to another note or KB."""
        if link_type == "note":
            if target_id in self.linked_notes:
                self.linked_notes.remove(target_id)
        elif link_type == "kb":
            if target_id in self.linked_kbs:
                self.linked_kbs.remove(target_id)
    
    def extract_links_from_content(self) -> List[str]:
        """Extract note links from content using [[note_id]] syntax."""
        pattern = r'\[\[([^\]]+)\]\]'
        matches = re.findall(pattern, self.content)
        return matches
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert datetimes to strings
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data
    
    def __repr__(self) -> str:
        return f"Note(id={self.id}, title={self.title}, path={self.path})"