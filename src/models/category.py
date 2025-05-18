"""Category Model

Represents a category within a knowledge base.
Categories are directories that can contain notes and subcategories.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class Category:
    """Represents a category within a knowledge base."""
    
    name: str
    description: str = ""
    parent: Optional[str] = None  # Parent category path relative to KB root
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    
    # Path information
    path: Optional[Path] = None
    relative_path: str = ""  # Path relative to KB root
    
    META_FILENAME = "category.json"
    
    def save(self):
        """Save category metadata to disk."""
        if not self.path:
            raise ValueError("Category path not set")
        
        # Create directory if it doesn't exist
        self.path.mkdir(parents=True, exist_ok=True)
        
        # Update timestamp
        self.updated_at = datetime.now()
        
        # Save metadata
        meta_path = self.path / self.META_FILENAME
        meta_data = self.to_dict()
        # Remove absolute path from metadata
        meta_data.pop('path', None)
        
        with open(meta_path, 'w') as f:
            json.dump(meta_data, f, indent=2, default=str)
    
    @classmethod
    def load(cls, category_path: Path, kb_root: Path) -> "Category":
        """Load category from disk."""
        meta_path = category_path / cls.META_FILENAME
        
        # If no metadata file exists, create a basic category
        if not meta_path.exists():
            category = cls(name=category_path.name)
            category.path = category_path
            category.relative_path = str(category_path.relative_to(kb_root))
            # Determine parent
            if category_path.parent != kb_root:
                category.parent = str(category_path.parent.relative_to(kb_root))
            return category
        
        with open(meta_path, 'r') as f:
            data = json.load(f)
        
        # Convert datetime strings back to datetime objects
        for date_field in ['created_at', 'updated_at']:
            if date_field in data:
                data[date_field] = datetime.fromisoformat(data[date_field])
        
        category = cls(**data)
        category.path = category_path
        return category
    
    @classmethod
    def list_all(cls, kb_path: Path) -> List["Category"]:
        """List all categories in a knowledge base."""
        categories = []
        
        for item in kb_path.rglob("*"):
            if item.is_dir() and item != kb_path:
                # Skip if it's a hidden directory
                if any(part.startswith('.') for part in item.parts):
                    continue
                
                try:
                    category = cls.load(item, kb_path)
                    categories.append(category)
                except Exception as e:
                    # Log error but continue
                    print(f"Error loading category at {item}: {e}")
        
        return categories
    
    def get_subcategories(self, kb_path: Path) -> List["Category"]:
        """Get all direct subcategories of this category."""
        if not self.path:
            raise ValueError("Category path not set")
        
        subcategories = []
        for item in self.path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                try:
                    subcategory = self.load(item, kb_path)
                    subcategories.append(subcategory)
                except Exception as e:
                    print(f"Error loading subcategory at {item}: {e}")
        
        return subcategories
    
    def get_notes(self) -> List[Path]:
        """Get all Markdown files in this category."""
        if not self.path:
            raise ValueError("Category path not set")
        
        notes = []
        for item in self.path.iterdir():
            if item.is_file() and item.suffix in ['.md', '.markdown']:
                notes.append(item)
        
        return sorted(notes)
    
    def move_to(self, new_parent_path: Path, kb_root: Path):
        """Move this category to a new parent."""
        if not self.path:
            raise ValueError("Category path not set")
        
        new_path = new_parent_path / self.path.name
        
        # Move the directory
        import shutil
        shutil.move(str(self.path), str(new_path))
        
        # Update path information
        self.path = new_path
        self.relative_path = str(new_path.relative_to(kb_root))
        
        # Update parent
        if new_parent_path == kb_root:
            self.parent = None
        else:
            self.parent = str(new_parent_path.relative_to(kb_root))
        
        # Save updated metadata
        self.save()
    
    def delete(self):
        """Delete this category from disk."""
        if not self.path or not self.path.exists():
            raise FileNotFoundError(f"Category not found at {self.path}")
        
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
        return f"Category(name={self.name}, path={self.relative_path})"