"""Migration utilities for converting JSON-based KBs to hierarchical structure."""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import shutil

from models import KnowledgeBase, Category, Note
from utils import ensure_directory, get_safe_filename


class MigrationManager:
    """Manages migration from JSON-based KBs to hierarchical structure."""
    
    def __init__(self, json_kb_path: Path, target_storage_path: Path):
        self.json_kb_path = json_kb_path
        self.target_storage_path = target_storage_path
        self.migration_log = []
    
    def migrate_all_kbs(self) -> Dict[str, Any]:
        """Migrate all knowledge bases from JSON format."""
        results = {
            'migrated': [],
            'failed': [],
            'stats': {
                'total_kbs': 0,
                'total_notes': 0,
                'total_tasks': 0
            }
        }
        
        # Backup existing JSON files
        backup_dir = self.target_storage_path / "migration_backup"
        ensure_directory(backup_dir)
        
        # Find all JSON KB files
        json_files = list(self.json_kb_path.glob("*.json"))
        results['stats']['total_kbs'] = len(json_files)
        
        for json_file in json_files:
            try:
                # Create backup
                backup_path = backup_dir / json_file.name
                shutil.copy2(json_file, backup_path)
                
                # Migrate KB
                kb_title = json_file.stem.replace("_", " ")
                migrated_kb = self.migrate_kb(json_file, kb_title)
                
                results['migrated'].append(migrated_kb)
                self.log(f"Successfully migrated KB: {kb_title}")
                
            except Exception as e:
                results['failed'].append({
                    'file': str(json_file),
                    'error': str(e)
                })
                self.log(f"Failed to migrate {json_file}: {e}", level="ERROR")
        
        # Save migration report
        self.save_migration_report(results)
        
        return results
    
    def migrate_kb(self, json_file: Path, kb_title: str) -> Dict[str, Any]:
        """Migrate a single knowledge base from JSON format."""
        # Load JSON data
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Create new KB
        kb = KnowledgeBase(
            title=kb_title,
            description=f"Migrated from {json_file.name}",
            created_at=datetime.now(),
            tags=["migrated"]
        )
        
        # Save KB to create directory structure
        kb.save(self.target_storage_path)
        
        stats = {
            'kb_id': kb.id,
            'notes': 0,
            'tasks': 0
        }
        
        # Process notes
        notes_data = data.get('notes', [])
        if notes_data:
            # Create default categories
            notes_category_path = kb.path / "Notes"
            ensure_directory(notes_category_path)
            
            # Create category metadata
            notes_category = Category(
                name="Notes",
                description="Migrated notes",
                path=notes_category_path,
                relative_path="Notes"
            )
            notes_category.save()
            
            # Migrate notes
            for note_data in notes_data:
                note = self._migrate_note(note_data, notes_category_path)
                stats['notes'] += 1
        
        # Process tasks (if any)
        tasks_data = data.get('todos', data.get('tasks', []))
        if tasks_data:
            # Create tasks category
            tasks_category_path = kb.path / "Tasks"
            ensure_directory(tasks_category_path)
            
            # Create category metadata
            tasks_category = Category(
                name="Tasks",
                description="Migrated tasks",
                path=tasks_category_path,
                relative_path="Tasks"
            )
            tasks_category.save()
            
            # Migrate tasks as notes
            for task_data in tasks_data:
                note = self._migrate_task(task_data, tasks_category_path)
                stats['tasks'] += 1
        
        return stats
    
    def _migrate_note(self, note_data: Dict[str, Any], category_path: Path) -> Note:
        """Migrate a single note."""
        # Extract note data
        note_id = note_data.get('id', '')
        content = note_data.get('content', '')
        created_at = note_data.get('created_at', datetime.now().isoformat())
        
        # Try to parse datetime
        try:
            created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        except:
            created_dt = datetime.now()
        
        # Extract title from content or use ID
        title = self._extract_title(content) or note_id
        
        # Create note
        note = Note(
            title=title,
            content=content,
            created_at=created_dt,
            updated_at=created_dt,
            id=note_id or get_safe_filename(title)
        )
        
        # Save note
        note.save(category_path)
        
        return note
    
    def _migrate_task(self, task_data: Dict[str, Any], category_path: Path) -> Note:
        """Migrate a task as a note."""
        # Extract task data
        task_id = task_data.get('id', '')
        description = task_data.get('description', task_data.get('content', ''))
        completed = task_data.get('completed', False)
        priority = task_data.get('priority', 'medium')
        
        # Create content with task metadata
        content = f"**Priority:** {priority}\n"
        content += f"**Status:** {'Completed' if completed else 'Pending'}\n\n"
        content += description
        
        # Create note from task
        note = Note(
            title=self._extract_title(description) or f"Task {task_id}",
            content=content,
            tags=['task', f'priority-{priority}'] + (['completed'] if completed else []),
            id=task_id or get_safe_filename(description[:50])
        )
        
        # Save note
        note.save(category_path)
        
        return note
    
    def _extract_title(self, content: str) -> str:
        """Extract title from content (first line or heading)."""
        lines = content.strip().split('\n')
        if not lines:
            return ""
        
        first_line = lines[0].strip()
        
        # Remove markdown heading markers
        if first_line.startswith('#'):
            first_line = first_line.lstrip('#').strip()
        
        # Truncate if too long
        if len(first_line) > 100:
            first_line = first_line[:97] + "..."
        
        return first_line
    
    def log(self, message: str, level: str = "INFO"):
        """Add entry to migration log."""
        timestamp = datetime.now().isoformat()
        self.migration_log.append(f"[{timestamp}] {level}: {message}")
    
    def save_migration_report(self, results: Dict[str, Any]):
        """Save migration report to file."""
        report_path = self.target_storage_path / "migration_report.json"
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'log': self.migration_log
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Also save human-readable log
        log_path = self.target_storage_path / "migration.log"
        with open(log_path, 'w') as f:
            f.write('\n'.join(self.migration_log))