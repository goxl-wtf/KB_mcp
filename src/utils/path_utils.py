"""Path Management Utilities

Utilities for managing paths in the hierarchical knowledge base system.
"""

from pathlib import Path
from typing import Optional, List, Tuple
import os
import shutil


def normalize_path(path: str | Path) -> Path:
    """Normalize a path to a Path object."""
    return Path(path).resolve()


def ensure_directory(path: Path) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_relative_path(path: Path, base: Path) -> str:
    """Get a path relative to a base path."""
    try:
        return str(path.relative_to(base))
    except ValueError:
        # Path is not relative to base
        return str(path)


def is_safe_path(path: Path, base_path: Path) -> bool:
    """Check if a path is within the allowed base path."""
    try:
        # Resolve both paths to absolute paths
        resolved_path = path.resolve()
        resolved_base = base_path.resolve()
        
        # Check if the path is within the base path
        resolved_path.relative_to(resolved_base)
        return True
    except ValueError:
        return False


def safe_delete(path: Path, base_path: Path) -> bool:
    """Safely delete a file or directory within the allowed base path."""
    if not is_safe_path(path, base_path):
        raise ValueError(f"Path {path} is outside allowed base path {base_path}")
    
    if path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)
    else:
        return False
    
    return True


def find_files(root: Path, pattern: str = "*", recursive: bool = True) -> List[Path]:
    """Find files matching a pattern."""
    if recursive:
        return list(root.rglob(pattern))
    else:
        return list(root.glob(pattern))


def create_backup(path: Path, backup_dir: Path) -> Path:
    """Create a backup of a file or directory."""
    backup_dir = ensure_directory(backup_dir)
    
    # Generate backup filename with timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{path.name}_{timestamp}"
    backup_path = backup_dir / backup_name
    
    if path.is_file():
        shutil.copy2(path, backup_path)
    elif path.is_dir():
        shutil.copytree(path, backup_path)
    
    return backup_path


def get_kb_hierarchy(kb_path: Path) -> List[Tuple[str, int]]:
    """Get the hierarchical structure of a knowledge base.
    
    Returns a list of tuples (path, level) representing the hierarchy.
    """
    hierarchy = []
    
    def walk_directory(path: Path, level: int = 0):
        if path.is_dir():
            # Add current directory
            rel_path = get_relative_path(path, kb_path)
            if rel_path != ".":
                hierarchy.append((rel_path, level))
            
            # Walk subdirectories
            for item in sorted(path.iterdir()):
                if item.is_dir() and not item.name.startswith('.'):
                    walk_directory(item, level + 1)
    
    walk_directory(kb_path)
    return hierarchy


def validate_id(id_str: str) -> bool:
    """Validate that an ID is safe for use as a filename/directory name."""
    # Check for empty or special values
    if not id_str or id_str in [".", "..", ""]:
        return False
    
    # Check for path separators
    if "/" in id_str or "\\" in id_str:
        return False
    
    # Check for special characters that might cause issues
    invalid_chars = ["<", ">", ":", '"', "|", "?", "*", "\x00"]
    if any(char in id_str for char in invalid_chars):
        return False
    
    # Check for hidden files (starting with dot)
    if id_str.startswith('.'):
        return False
    
    return True


def get_safe_filename(title: str) -> str:
    """Convert a title to a safe filename."""
    # Replace spaces with underscores
    filename = title.replace(" ", "_")
    
    # Remove or replace invalid characters
    invalid_chars = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]
    for char in invalid_chars:
        filename = filename.replace(char, "_")
    
    # Remove control characters
    filename = "".join(char for char in filename if ord(char) >= 32)
    
    # Limit length (leaving room for extension)
    max_length = 200
    if len(filename) > max_length:
        filename = filename[:max_length]
    
    # Remove trailing dots and spaces
    filename = filename.rstrip(". ")
    
    # Ensure it's not empty
    if not filename:
        filename = "untitled"
    
    return filename