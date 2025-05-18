#!/usr/bin/env python3
"""Simple test of codebase analysis functionality."""

import sys
sys.path.insert(0, 'src')

import tempfile
from pathlib import Path
import textwrap
import ast

from models import KnowledgeBase, Category, Note
from utils import ensure_directory


def create_simple_codebase(path: Path):
    """Create a simple test codebase."""
    # Create main.py
    main_py = path / "main.py"
    main_py.write_text(textwrap.dedent('''
        """Main module for the test application."""
        
        import os
        import sys
        
        class TestApp:
            """Test application class."""
            
            def __init__(self):
                self.name = "Test"
            
            def run(self):
                """Run the application."""
                print(f"Running {self.name}")
        
        def main():
            """Entry point."""
            app = TestApp()
            app.run()
        
        if __name__ == "__main__":
            main()
    '''))
    
    # Create utils.py
    utils_py = path / "utils.py"
    utils_py.write_text(textwrap.dedent('''
        """Utility functions."""
        
        def process_data(data):
            """Process data."""
            return {"processed": data}
        
        def validate(value):
            """Validate value."""
            return value is not None
    '''))


def analyze_python_file(file_path: Path) -> dict:
    """Analyze a Python file directly."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
        
        # Count components
        functions = []
        classes = []
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                module = getattr(node, 'module', None) or node.names[0].name
                imports.append(module)
        
        return {
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "lines": len(content.splitlines())
        }
    except Exception as e:
        return {"error": str(e)}


def test_analysis_direct():
    """Test codebase analysis directly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test codebase
        codebase_path = Path(temp_dir) / "test_code"
        codebase_path.mkdir()
        create_simple_codebase(codebase_path)
        
        # Create storage
        storage_path = Path(temp_dir) / "storage"
        storage_path.mkdir()
        
        print("=== Direct Codebase Analysis Test ===\n")
        print(f"Codebase: {codebase_path}")
        print(f"Storage: {storage_path}\n")
        
        # Create KB for analysis
        kb = KnowledgeBase(
            title="Code Analysis Test",
            description="Test codebase analysis",
            default_categories=["Overview", "Components", "Documentation"],
            tags=["test", "analysis"]
        )
        kb.save(storage_path)
        print(f"✓ Created KB: {kb.title}")
        
        # Analyze files
        print("\n1. Analyzing Python files...")
        
        components_cat = ensure_directory(kb.path / "Components" / "Python")
        
        for py_file in codebase_path.glob("*.py"):
            print(f"\nAnalyzing: {py_file.name}")
            
            # Analyze the file
            analysis = analyze_python_file(py_file)
            
            if "error" not in analysis:
                print(f"  Functions: {analysis['functions']}")
                print(f"  Classes: {analysis['classes']}")
                print(f"  Imports: {analysis['imports']}")
                print(f"  Lines: {analysis['lines']}")
                
                # Create note
                content = f"""# {py_file.name}

## Analysis Summary
- **Functions**: {len(analysis['functions'])}
- **Classes**: {len(analysis['classes'])}
- **Imports**: {len(analysis['imports'])}
- **Lines**: {analysis['lines']}

## Functions
{chr(10).join(f"- `{func}()`" for func in analysis['functions'])}

## Classes
{chr(10).join(f"- `{cls}`" for cls in analysis['classes'])}

## Imports
{chr(10).join(f"- `{imp}`" for imp in analysis['imports'])}
"""
                
                note = Note(
                    title=f"{py_file.stem} Analysis",
                    content=content,
                    tags=["python", "analysis", "code"]
                )
                note.save(components_cat)
                print(f"  ✓ Created note: {note.title}")
            else:
                print(f"  ❌ Error: {analysis['error']}")
        
        # Create overview
        print("\n2. Creating overview...")
        
        overview_cat = ensure_directory(kb.path / "Overview")
        
        # Count total components
        total_functions = 0
        total_classes = 0
        total_files = 0
        
        for py_file in codebase_path.glob("*.py"):
            analysis = analyze_python_file(py_file)
            if "error" not in analysis:
                total_functions += len(analysis["functions"])
                total_classes += len(analysis["classes"])
                total_files += 1
        
        overview_content = f"""# Codebase Overview

## Summary
- **Files analyzed**: {total_files}
- **Total functions**: {total_functions}
- **Total classes**: {total_classes}

## File List
{chr(10).join(f"- [[{f.stem}_Analysis|{f.name}]]" for f in codebase_path.glob("*.py"))}

## Navigation
- [[Components]] - Code components by language
- [[Documentation]] - Generated documentation
"""
        
        overview_note = Note(
            title="Codebase Overview",
            content=overview_content,
            tags=["overview", "analysis"]
        )
        overview_note.save(overview_cat)
        print(f"✓ Created overview note")
        
        # Show final structure
        print("\n3. Final KB Structure:")
        
        def print_tree(path, prefix="", level=0):
            if level > 3:
                return
            items = sorted(path.iterdir())
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                current = "└── " if is_last else "├── "
                print(f"{prefix}{current}{item.name}")
                if item.is_dir():
                    next_prefix = prefix + ("    " if is_last else "│   ")
                    print_tree(item, next_prefix, level + 1)
        
        print_tree(kb.path)
        
        print("\n✅ Analysis test completed!")


if __name__ == "__main__":
    test_analysis_direct()