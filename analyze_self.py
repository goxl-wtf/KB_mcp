#!/usr/bin/env python3
"""Analyze the hierarchical KB system's own codebase."""

import sys
sys.path.insert(0, 'src')

from pathlib import Path
import os

from models import KnowledgeBase, Category, Note
from utils import ensure_directory
from tools.analysis_tools import (
    _scan_codebase, _analyze_python_files, _create_overview_note,
    _analyze_project_structure, _analyze_python_deps
)


def analyze_hierarchical_kb():
    """Analyze the hierarchical KB system itself."""
    # Set up paths
    project_root = Path(__file__).parent
    src_path = project_root / "src"
    storage_path = project_root / "self_analysis"
    storage_path.mkdir(exist_ok=True)
    
    print("=== Self-Analysis: Hierarchical KB System ===\n")
    print(f"Project root: {project_root}")
    print(f"Analysis storage: {storage_path}\n")
    
    # Create KB for analysis
    kb = KnowledgeBase(
        title="Hierarchical KB System Analysis",
        description="Analysis of the hierarchical KB system's own codebase",
        default_categories=["Architecture", "Components", "Tools", "Models", "Documentation"],
        tags=["self-analysis", "meta", "codebase"]
    )
    kb.save(storage_path)
    print(f"✓ Created KB: {kb.title}\n")
    
    # Scan codebase
    print("1. Scanning codebase structure...")
    files_by_type = _scan_codebase(src_path)
    
    total_files = sum(len(files) for files in files_by_type.values())
    print(f"✓ Found {total_files} source files")
    for lang, files in files_by_type.items():
        print(f"  - {lang}: {len(files)} files")
    
    # Analyze Python files
    print("\n2. Analyzing Python components...")
    
    results = {
        "total_files": total_files,
        "analyzed_files": 0,
        "languages": {lang: len(files) for lang, files in files_by_type.items()},
        "components": {
            "functions": 0,
            "classes": 0,
            "imports": 0,
            "comments": 0
        },
        "errors": []
    }
    
    # Create categories for different components
    models_cat = ensure_directory(kb.path / "Components" / "Models")
    tools_cat = ensure_directory(kb.path / "Components" / "Tools")
    utils_cat = ensure_directory(kb.path / "Components" / "Utils")
    
    # Analyze Python files by category
    for py_file in files_by_type.get("python", []):
        try:
            # Determine category based on path
            if "models" in str(py_file):
                category = models_cat
                component_type = "Model"
            elif "tools" in str(py_file):
                category = tools_cat
                component_type = "Tool"
            elif "utils" in str(py_file):
                category = utils_cat
                component_type = "Utility"
            else:
                category = ensure_directory(kb.path / "Components" / "Core")
                component_type = "Core"
            
            print(f"\nAnalyzing {component_type}: {py_file.name}")
            
            # Simplified analysis
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count basic components
            import ast
            try:
                tree = ast.parse(content)
                
                functions = []
                classes = []
                imports = []
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        functions.append({
                            "name": node.name,
                            "lineno": node.lineno,
                            "docstring": ast.get_docstring(node)
                        })
                        results["components"]["functions"] += 1
                    elif isinstance(node, ast.ClassDef):
                        classes.append({
                            "name": node.name,
                            "lineno": node.lineno,
                            "docstring": ast.get_docstring(node)
                        })
                        results["components"]["classes"] += 1
                    elif isinstance(node, (ast.Import, ast.ImportFrom)):
                        results["components"]["imports"] += 1
                
                # Create note for the file
                note_content = f"""# {py_file.name}

## Overview
- **Type**: {component_type}
- **Path**: {py_file.relative_to(project_root)}
- **Lines**: {len(content.splitlines())}

## Classes ({len(classes)})
"""
                for cls in classes:
                    note_content += f"\n### {cls['name']} (line {cls['lineno']})\n"
                    if cls['docstring']:
                        note_content += f"{cls['docstring'][:200]}...\n"

                note_content += f"\n## Functions ({len(functions)})\n"
                for func in functions[:10]:  # Limit to first 10
                    note_content += f"\n### {func['name']} (line {func['lineno']})\n"
                    if func['docstring']:
                        note_content += f"{func['docstring'][:100]}...\n"
                
                if len(functions) > 10:
                    note_content += f"\n... and {len(functions) - 10} more functions\n"
                
                note = Note(
                    title=f"{py_file.stem} ({component_type})",
                    content=note_content,
                    tags=["python", component_type.lower(), "analysis"]
                )
                note.save(category)
                results["analyzed_files"] += 1
                print(f"  ✓ Created note with {len(functions)} functions, {len(classes)} classes")
                
            except Exception as e:
                results["errors"].append(f"Parse error in {py_file}: {str(e)}")
                print(f"  ❌ Parse error: {str(e)}")
                
        except Exception as e:
            results["errors"].append(f"Error analyzing {py_file}: {str(e)}")
            print(f"  ❌ Error: {str(e)}")
    
    # Create architecture documentation
    print("\n3. Analyzing project architecture...")
    _analyze_project_structure(project_root, kb.path, results)
    print("✓ Created architecture documentation")
    
    # Create overview
    print("\n4. Creating project overview...")
    _create_overview_note(kb.path, project_root, results)
    print("✓ Created overview note")
    
    # Analyze dependencies
    print("\n5. Analyzing dependencies...")
    dep_results = {
        "dependency_files_found": [],
        "total_dependencies": 0,
        "languages": {}
    }
    
    req_file = project_root / "requirements.txt"
    if req_file.exists():
        dep_results["dependency_files_found"].append("requirements.txt")
        python_deps = _analyze_python_deps(project_root, include_versions=True)
        dep_results["languages"]["python"] = python_deps
        dep_results["total_dependencies"] += len(python_deps.get("dependencies", []))
        
        # Create dependencies note
        deps_cat = ensure_directory(kb.path / "Architecture" / "Dependencies")
        deps_content = f"""# Python Dependencies

## Production Dependencies ({len(python_deps.get('dependencies', []))})
{chr(10).join(f"- `{dep}`" for dep in python_deps.get('dependencies', []))}

## Development Dependencies ({len(python_deps.get('dev_dependencies', []))})
{chr(10).join(f"- `{dep}`" for dep in python_deps.get('dev_dependencies', []))}
"""
        
        deps_note = Note(
            title="Dependencies",
            content=deps_content,
            tags=["dependencies", "architecture", "python"]
        )
        deps_note.save(deps_cat)
        print(f"✓ Documented {dep_results['total_dependencies']} dependencies")
    
    # Create tool documentation
    print("\n6. Documenting tools...")
    tools_doc_cat = ensure_directory(kb.path / "Documentation" / "Tools")
    
    tool_groups = {
        "kb_tools": "Knowledge Base Management",
        "category_tools": "Category Management",
        "note_tools": "Note Management",
        "search_tools": "Search and Discovery",
        "viz_tools": "Visualization",
        "analysis_tools": "Codebase Analysis"
    }
    
    for tool_file, description in tool_groups.items():
        tool_path = src_path / "tools" / f"{tool_file}.py"
        if tool_path.exists():
            tool_note = Note(
                title=f"{description} Tools",
                content=f"""# {description} Tools

## Overview
The {tool_file} module provides MCP tools for {description.lower()}.

## Location
`src/tools/{tool_file}.py`

## Tool Categories
- Primary functionality
- Helper functions
- Error handling

## Integration
These tools are registered with the MCP server and can be invoked by clients.
""",
                tags=["tools", "documentation", tool_file]
            )
            tool_note.save(tools_doc_cat)
    
    print("✓ Created tool documentation")
    
    # Summary statistics
    print("\n7. Analysis Summary:")
    print(f"  - Total files: {results['total_files']}")
    print(f"  - Analyzed files: {results['analyzed_files']}")
    print(f"  - Functions: {results['components']['functions']}")
    print(f"  - Classes: {results['components']['classes']}")
    print(f"  - Dependencies: {dep_results['total_dependencies']}")
    print(f"  - Errors: {len(results['errors'])}")
    
    # Show final structure
    print("\n8. Knowledge Base Structure:")
    
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
    
    print(f"\n✅ Self-analysis completed! KB created at: {storage_path}")


if __name__ == "__main__":
    analyze_hierarchical_kb()