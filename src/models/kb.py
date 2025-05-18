"""Knowledge Base Model

Represents a knowledge base within the hierarchical storage system.
Each KB is a directory containing categories (subdirectories) and metadata.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class KnowledgeBase:
    """Represents a knowledge base with metadata and relationships."""
    
    title: str
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    parent_kb: Optional[str] = None  # For derived knowledge bases
    relationships: List[str] = field(default_factory=list)  # Related KB IDs
    default_categories: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    # Path information
    id: str = ""  # Directory name (derived from title)
    path: Optional[Path] = None
    
    META_FILENAME = "meta.json"
    
    def __post_init__(self):
        """Initialize ID from title if not provided."""
        if not self.id:
            self.id = self._title_to_id(self.title)
    
    @staticmethod
    def _title_to_id(title: str) -> str:
        """Convert a title to a valid directory name."""
        # Replace spaces with underscores and remove special characters
        id_str = title.replace(" ", "_")
        # Keep only alphanumeric, underscore, and hyphen
        id_str = "".join(c for c in id_str if c.isalnum() or c in "_-")
        return id_str
    
    def save(self, storage_path: Path):
        """Save knowledge base metadata to disk."""
        if not self.path:
            self.path = storage_path / self.id
        
        # Create directory if it doesn't exist
        self.path.mkdir(parents=True, exist_ok=True)
        
        # Update timestamp
        self.updated_at = datetime.now()
        
        # Save metadata
        meta_path = self.path / self.META_FILENAME
        meta_data = self.to_dict()
        # Remove path from metadata (it's derived from location)
        meta_data.pop('path', None)
        
        with open(meta_path, 'w') as f:
            json.dump(meta_data, f, indent=2, default=str)
        
        # Create default categories if specified
        for category in self.default_categories:
            category_path = self.path / category
            category_path.mkdir(exist_ok=True)
    
    @classmethod
    def load(cls, kb_path: Path) -> "KnowledgeBase":
        """Load knowledge base from disk."""
        meta_path = kb_path / cls.META_FILENAME
        
        if not meta_path.exists():
            raise FileNotFoundError(f"Knowledge base metadata not found at {meta_path}")
        
        with open(meta_path, 'r') as f:
            data = json.load(f)
        
        # Convert datetime strings back to datetime objects
        for date_field in ['created_at', 'updated_at']:
            if date_field in data:
                data[date_field] = datetime.fromisoformat(data[date_field])
        
        kb = cls(**data)
        kb.path = kb_path
        return kb
    
    @classmethod
    def list_all(cls, storage_path: Path) -> List["KnowledgeBase"]:
        """List all knowledge bases in storage."""
        kbs = []
        
        for item in storage_path.iterdir():
            if item.is_dir():
                meta_path = item / cls.META_FILENAME
                if meta_path.exists():
                    try:
                        kb = cls.load(item)
                        kbs.append(kb)
                    except Exception as e:
                        # Log error but continue with other KBs
                        print(f"Error loading KB at {item}: {e}")
        
        return kbs
    
    def delete(self):
        """Delete this knowledge base from disk."""
        if not self.path or not self.path.exists():
            raise FileNotFoundError(f"Knowledge base not found at {self.path}")
        
        # Recursively remove the directory
        import shutil
        shutil.rmtree(self.path)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert datetimes to strings
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data
    
    def __repr__(self) -> str:
        return f"KnowledgeBase(id={self.id}, title={self.title}, path={self.path})"