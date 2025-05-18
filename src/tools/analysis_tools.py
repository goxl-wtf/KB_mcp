"""Codebase Analysis Tools

Tools for analyzing codebases to create and maintain knowledge bases.
"""

import ast
import json
import os
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Any, Set
from collections import defaultdict
from datetime import datetime

import fastmcp

from models import KnowledgeBase, Category, Note
from utils import ensure_directory, get_safe_filename, get_content_preview


# Language file extensions mapping
LANGUAGE_EXTENSIONS = {
    "python": [".py"],
    "javascript": [".js", ".jsx"],
    "typescript": [".ts", ".tsx"],
    "java": [".java"],
    "cpp": [".cpp", ".cc", ".cxx", ".hpp", ".h"],
    "go": [".go"],
    "rust": [".rs"],
    "ruby": [".rb"],
    "php": [".php"],
    "csharp": [".cs"],
    "swift": [".swift"],
    "kotlin": [".kt"],
    "markdown": [".md", ".markdown"],
    "yaml": [".yml", ".yaml"],
    "json": [".json"],
    "shell": [".sh", ".bash"],
}

# File patterns to ignore
IGNORE_PATTERNS = [
    "__pycache__",
    ".git",
    ".venv",
    "env",
    "venv",
    "node_modules",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
    ".next",
    ".cache",
]


def register_analysis_tools(mcp: fastmcp.FastMCP, state):
    """Register all codebase analysis tools with the MCP server."""
    
    @mcp.tool()
    def analyze_codebase(
        codebase_path: str,
        kb_title: Optional[str] = None,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        analyze_imports: bool = True,
        analyze_functions: bool = True,
        analyze_classes: bool = True,
        analyze_comments: bool = True,
        max_file_size: int = 1024 * 1024  # 1MB
    ) -> Dict[str, Any]:
        """Analyze a codebase and create a knowledge base from it.
        
        Args:
            codebase_path: Path to the codebase to analyze
            kb_title: Title for the new KB (defaults to directory name)
            include_patterns: File patterns to include
            exclude_patterns: Additional patterns to exclude
            analyze_imports: Whether to analyze import statements
            analyze_functions: Whether to analyze function definitions
            analyze_classes: Whether to analyze class definitions
            analyze_comments: Whether to extract documentation comments
            max_file_size: Maximum file size to analyze (in bytes)
        
        Returns:
            Analysis results and KB creation info
        """
        try:
            code_path = Path(codebase_path)
            if not code_path.exists():
                return {"error": f"Codebase path '{codebase_path}' not found"}
            
            # Create KB for the codebase
            if not kb_title:
                kb_title = f"{code_path.name} Codebase"
            
            kb = KnowledgeBase(
                title=kb_title,
                description=f"Analysis of {code_path.name} codebase",
                default_categories=["Overview", "Architecture", "Components", "Documentation"],
                tags=["codebase", "analysis", "automated"]
            )
            kb.save(state.storage_path)
            
            # Set as current KB
            state.current_kb = kb.id
            
            # Initialize results
            results = {
                "kb_id": kb.id,
                "kb_title": kb.title,
                "analyzed_files": 0,
                "total_files": 0,
                "languages": defaultdict(int),
                "components": {
                    "functions": 0,
                    "classes": 0,
                    "imports": 0,
                    "comments": 0
                },
                "errors": []
            }
            
            # Scan codebase
            files_by_type = _scan_codebase(
                code_path,
                include_patterns,
                exclude_patterns,
                max_file_size
            )
            results["total_files"] = sum(len(files) for files in files_by_type.values())
            
            # Create language-specific categories
            for language, files in files_by_type.items():
                if files:
                    lang_category = ensure_directory(kb.path / "Components" / language.title())
                    results["languages"][language] = len(files)
                    
                    # Analyze files by language
                    if language == "python" and (analyze_imports or analyze_functions or analyze_classes):
                        _analyze_python_files(
                            files, lang_category, kb.path,
                            analyze_imports, analyze_functions, 
                            analyze_classes, analyze_comments,
                            results
                        )
                    elif language in ["javascript", "typescript"] and analyze_functions:
                        _analyze_js_files(
                            files, lang_category, kb.path,
                            analyze_imports, analyze_functions,
                            analyze_comments, results
                        )
                    else:
                        # Basic analysis for other languages
                        _analyze_generic_files(
                            files, lang_category, kb.path,
                            language, results
                        )
            
            # Create overview documentation
            _create_overview_note(kb.path, code_path, results)
            
            # Create architecture notes
            _analyze_project_structure(code_path, kb.path, results)
            
            return results
            
        except Exception as e:
            return {"error": f"Failed to analyze codebase: {str(e)}"}
    
    @mcp.tool()
    def extract_patterns(
        kb_id: Optional[str] = None,
        pattern_types: Optional[List[str]] = None,
        min_occurrences: int = 2
    ) -> Dict[str, Any]:
        """Extract design patterns and best practices from analyzed code.
        
        Args:
            kb_id: KB to analyze (uses current if not specified)
            pattern_types: Types of patterns to look for
            min_occurrences: Minimum occurrences to consider a pattern
        
        Returns:
            Extracted patterns and recommendations
        """
        try:
            # Determine KB
            if kb_id:
                kb_path = state.storage_path / kb_id
            elif state.current_kb:
                kb_path = state.storage_path / state.current_kb
            else:
                return {"error": "No KB specified or selected"}
            
            patterns = {
                "design_patterns": [],
                "naming_conventions": [],
                "code_structure": [],
                "best_practices": [],
                "anti_patterns": []
            }
            
            # Analyze notes for patterns
            for note_path in kb_path.rglob("*.md"):
                try:
                    note = Note.load(note_path)
                    
                    # Look for design patterns
                    if "class" in note.tags or "architecture" in note.tags:
                        design_patterns = _identify_design_patterns(note.content)
                        patterns["design_patterns"].extend(design_patterns)
                    
                    # Look for naming conventions
                    if "function" in note.tags or "class" in note.tags:
                        naming = _analyze_naming_conventions(note.content)
                        patterns["naming_conventions"].extend(naming)
                    
                    # Look for code structure patterns
                    if "module" in note.tags or "package" in note.tags:
                        structure = _analyze_code_structure(note.content)
                        patterns["code_structure"].extend(structure)
                    
                except Exception as e:
                    print(f"Error analyzing note {note_path}: {e}")
                    continue
            
            # Consolidate patterns
            consolidated = _consolidate_patterns(patterns, min_occurrences)
            
            # Create pattern documentation
            pattern_category = ensure_directory(kb_path / "Patterns")
            
            for pattern_type, pattern_list in consolidated.items():
                if pattern_list:
                    note = Note(
                        title=f"{pattern_type.replace('_', ' ').title()} Analysis",
                        content=_format_pattern_documentation(pattern_type, pattern_list),
                        tags=["patterns", "analysis", pattern_type]
                    )
                    note.save(pattern_category)
            
            return {
                "kb_id": kb_id or state.current_kb,
                "patterns_found": {k: len(v) for k, v in consolidated.items()},
                "total_patterns": sum(len(v) for v in consolidated.values()),
                "pattern_details": consolidated
            }
            
        except Exception as e:
            return {"error": f"Failed to extract patterns: {str(e)}"}
    
    @mcp.tool()
    def generate_documentation(
        source_path: str,
        output_kb_id: Optional[str] = None,
        doc_format: str = "markdown",
        include_examples: bool = True,
        include_tests: bool = True
    ) -> Dict[str, Any]:
        """Generate documentation from source code.
        
        Args:
            source_path: Path to source code
            output_kb_id: KB to write documentation to
            doc_format: Documentation format
            include_examples: Include code examples
            include_tests: Include test documentation
        
        Returns:
            Documentation generation results
        """
        try:
            source = Path(source_path)
            if not source.exists():
                return {"error": f"Source path '{source_path}' not found"}
            
            # Determine output KB
            if output_kb_id:
                kb_path = state.storage_path / output_kb_id
            elif state.current_kb:
                kb_path = state.storage_path / state.current_kb
            else:
                return {"error": "No output KB specified"}
            
            results = {
                "files_processed": 0,
                "documentation_created": 0,
                "examples_extracted": 0,
                "tests_documented": 0
            }
            
            # Create documentation category
            doc_category = ensure_directory(kb_path / "Documentation" / "API")
            
            # Process source files
            if source.is_file():
                files = [source]
            else:
                files = list(source.rglob("*.py"))  # Starting with Python
            
            for file_path in files:
                try:
                    if file_path.stat().st_size > 1024 * 1024:  # Skip large files
                        continue
                    
                    # Generate documentation
                    doc = _generate_file_documentation(
                        file_path,
                        include_examples,
                        include_tests
                    )
                    
                    if doc:
                        # Create documentation note
                        note = Note(
                            title=f"{file_path.stem} Documentation",
                            content=doc["content"],
                            tags=["documentation", "api", doc["language"]],
                            linked_notes=doc.get("references", [])
                        )
                        
                        # Organize by module structure
                        module_path = _get_module_path(file_path, source)
                        category_path = doc_category
                        
                        if module_path:
                            for part in module_path.parts[:-1]:
                                category_path = ensure_directory(category_path / part)
                        
                        note.save(category_path)
                        results["documentation_created"] += 1
                        results["examples_extracted"] += doc.get("examples", 0)
                        results["tests_documented"] += doc.get("tests", 0)
                    
                    results["files_processed"] += 1
                    
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
                    continue
            
            return results
            
        except Exception as e:
            return {"error": f"Failed to generate documentation: {str(e)}"}
    
    @mcp.tool()
    def sync_codebase(
        codebase_path: str,
        kb_id: str,
        update_only_changed: bool = True,
        delete_removed: bool = False
    ) -> Dict[str, Any]:
        """Synchronize a knowledge base with codebase changes.
        
        Args:
            codebase_path: Path to the codebase
            kb_id: KB to synchronize
            update_only_changed: Only update files that have changed
            delete_removed: Remove notes for deleted files
        
        Returns:
            Synchronization results
        """
        try:
            code_path = Path(codebase_path)
            kb_path = state.storage_path / kb_id
            
            if not code_path.exists():
                return {"error": f"Codebase path '{codebase_path}' not found"}
            
            if not kb_path.exists():
                return {"error": f"Knowledge base '{kb_id}' not found"}
            
            results = {
                "files_checked": 0,
                "files_updated": 0,
                "files_added": 0,
                "files_removed": 0,
                "errors": []
            }
            
            # Track existing notes
            existing_notes = {}
            for note_path in kb_path.rglob("*.md"):
                try:
                    note = Note.load(note_path)
                    # Extract source file from metadata
                    if "source_file" in note.tags:
                        source_tag = next((t for t in note.tags if t.startswith("source:")), None)
                        if source_tag:
                            source_file = source_tag.split(":", 1)[1]
                            existing_notes[source_file] = note_path
                except:
                    pass
            
            # Scan current codebase
            current_files = _scan_codebase(code_path)
            all_current_files = []
            
            for language, files in current_files.items():
                for file_path in files:
                    all_current_files.append(file_path)
                    results["files_checked"] += 1
                    
                    relative_path = file_path.relative_to(code_path)
                    note_key = str(relative_path)
                    
                    # Check if file has changed
                    if update_only_changed and note_key in existing_notes:
                        existing_note_path = existing_notes[note_key]
                        try:
                            existing_note = Note.load(existing_note_path)
                            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                            
                            if file_mtime <= existing_note.updated_at:
                                continue  # Skip unchanged files
                        except:
                            pass
                    
                    # Update or create note
                    try:
                        doc = _generate_file_documentation(file_path)
                        if doc:
                            note = Note(
                                title=f"{file_path.stem} - {language.title()}",
                                content=doc["content"],
                                tags=["code", language, f"source:{note_key}"],
                                linked_notes=doc.get("references", [])
                            )
                            
                            # Determine category
                            lang_category = ensure_directory(
                                kb_path / "Components" / language.title()
                            )
                            module_path = _get_module_path(file_path, code_path)
                            category_path = lang_category
                            
                            if module_path:
                                for part in module_path.parts[:-1]:
                                    category_path = ensure_directory(category_path / part)
                            
                            note.save(category_path)
                            
                            if note_key in existing_notes:
                                results["files_updated"] += 1
                            else:
                                results["files_added"] += 1
                    
                    except Exception as e:
                        results["errors"].append(f"Error updating {file_path}: {str(e)}")
            
            # Handle removed files
            if delete_removed:
                for source_file, note_path in existing_notes.items():
                    current_file = code_path / source_file
                    if not current_file.exists():
                        try:
                            note_path.unlink()
                            results["files_removed"] += 1
                        except Exception as e:
                            results["errors"].append(f"Error removing {note_path}: {str(e)}")
            
            return results
            
        except Exception as e:
            return {"error": f"Failed to sync codebase: {str(e)}"}
    
    @mcp.tool()
    def analyze_dependencies(
        codebase_path: str,
        output_kb_id: Optional[str] = None,
        include_versions: bool = True,
        check_vulnerabilities: bool = False
    ) -> Dict[str, Any]:
        """Analyze project dependencies and create documentation.
        
        Args:
            codebase_path: Path to the codebase
            output_kb_id: KB to write analysis to
            include_versions: Include version information
            check_vulnerabilities: Check for known vulnerabilities
        
        Returns:
            Dependency analysis results
        """
        try:
            code_path = Path(codebase_path)
            if not code_path.exists():
                return {"error": f"Codebase path '{codebase_path}' not found"}
            
            # Determine output KB
            if output_kb_id:
                kb_path = state.storage_path / output_kb_id
            elif state.current_kb:
                kb_path = state.storage_path / state.current_kb
            else:
                return {"error": "No output KB specified"}
            
            results = {
                "dependency_files_found": [],
                "total_dependencies": 0,
                "languages": {},
                "vulnerabilities": []
            }
            
            # Create dependencies category
            deps_category = ensure_directory(kb_path / "Architecture" / "Dependencies")
            
            # Check for Python dependencies
            if (code_path / "requirements.txt").exists():
                results["dependency_files_found"].append("requirements.txt")
                python_deps = _analyze_python_deps(code_path, include_versions)
                results["languages"]["python"] = python_deps
                results["total_dependencies"] += len(python_deps["dependencies"])
                
                # Create note
                note = Note(
                    title="Python Dependencies",
                    content=_format_dependency_doc("Python", python_deps),
                    tags=["dependencies", "python", "architecture"]
                )
                note.save(deps_category)
            
            # Check for Node.js dependencies
            if (code_path / "package.json").exists():
                results["dependency_files_found"].append("package.json")
                node_deps = _analyze_node_deps(code_path, include_versions)
                results["languages"]["javascript"] = node_deps
                results["total_dependencies"] += len(node_deps["dependencies"])
                
                # Create note
                note = Note(
                    title="Node.js Dependencies",
                    content=_format_dependency_doc("Node.js", node_deps),
                    tags=["dependencies", "javascript", "architecture"]
                )
                note.save(deps_category)
            
            # Check for other dependency files
            dep_files = {
                "Gemfile": ("ruby", "Ruby"),
                "go.mod": ("go", "Go"),
                "Cargo.toml": ("rust", "Rust"),
                "pom.xml": ("java", "Java/Maven"),
                "build.gradle": ("java", "Java/Gradle")
            }
            
            for filename, (lang, title) in dep_files.items():
                if (code_path / filename).exists():
                    results["dependency_files_found"].append(filename)
                    # Basic parsing for other languages
                    results["languages"][lang] = {"file": filename}
            
            # Create summary note
            summary_note = Note(
                title="Dependency Analysis Summary",
                content=_format_dependency_summary(results),
                tags=["dependencies", "architecture", "summary"]
            )
            summary_note.save(deps_category)
            
            return results
            
        except Exception as e:
            return {"error": f"Failed to analyze dependencies: {str(e)}"}


# Helper functions

def _scan_codebase(
    path: Path,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    max_file_size: int = 1024 * 1024
) -> Dict[str, List[Path]]:
    """Scan codebase and organize files by language."""
    files_by_type = defaultdict(list)
    exclude = set(IGNORE_PATTERNS)
    
    if exclude_patterns:
        exclude.update(exclude_patterns)
    
    for item in path.rglob("*"):
        # Skip excluded directories
        if any(exc in str(item) for exc in exclude):
            continue
        
        if item.is_file():
            # Skip large files
            if item.stat().st_size > max_file_size:
                continue
            
            # Apply include patterns if specified
            if include_patterns:
                if not any(item.match(pattern) for pattern in include_patterns):
                    continue
            
            # Categorize by language
            ext = item.suffix.lower()
            for language, extensions in LANGUAGE_EXTENSIONS.items():
                if ext in extensions:
                    files_by_type[language].append(item)
                    break
    
    return dict(files_by_type)


def _analyze_python_files(
    files: List[Path],
    category_path: Path,
    kb_path: Path,
    analyze_imports: bool,
    analyze_functions: bool,
    analyze_classes: bool,
    analyze_comments: bool,
    results: Dict[str, Any]
):
    """Analyze Python files and create notes."""
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            try:
                tree = ast.parse(content)
            except SyntaxError:
                results["errors"].append(f"Syntax error in {file_path}")
                continue
            
            # Analyze components
            imports = []
            functions = []
            classes = []
            docstrings = []
            
            for node in ast.walk(tree):
                if analyze_imports and isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports.append(_extract_import_info(node))
                    results["components"]["imports"] += 1
                
                elif analyze_functions and isinstance(node, ast.FunctionDef):
                    func_info = _extract_function_info(node)
                    functions.append(func_info)
                    results["components"]["functions"] += 1
                    
                    if analyze_comments and ast.get_docstring(node):
                        docstrings.append({
                            "type": "function",
                            "name": node.name,
                            "docstring": ast.get_docstring(node)
                        })
                        results["components"]["comments"] += 1
                
                elif analyze_classes and isinstance(node, ast.ClassDef):
                    class_info = _extract_class_info(node)
                    classes.append(class_info)
                    results["components"]["classes"] += 1
                    
                    if analyze_comments and ast.get_docstring(node):
                        docstrings.append({
                            "type": "class",
                            "name": node.name,
                            "docstring": ast.get_docstring(node)
                        })
                        results["components"]["comments"] += 1
            
            # Create note for the file
            note_content = _format_python_analysis(
                file_path,
                imports,
                functions,
                classes,
                docstrings
            )
            
            note = Note(
                title=f"{file_path.stem} (Python)",
                content=note_content,
                tags=["python", "code", "analysis"],
                linked_notes=_extract_references(functions, classes)
            )
            
            # Organize by module structure
            relative_path = file_path.relative_to(file_path.parent.parent.parent)
            module_path = Path(*relative_path.parts[:-1])
            
            note_category = category_path
            for part in module_path.parts:
                note_category = ensure_directory(note_category / part)
            
            note.save(note_category)
            results["analyzed_files"] += 1
            
        except Exception as e:
            results["errors"].append(f"Error analyzing {file_path}: {str(e)}")


def _analyze_js_files(
    files: List[Path],
    category_path: Path,
    kb_path: Path,
    analyze_imports: bool,
    analyze_functions: bool,
    analyze_comments: bool,
    results: Dict[str, Any]
):
    """Analyze JavaScript/TypeScript files and create notes."""
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract components using regex
            imports = []
            functions = []
            classes = []
            comments = []
            
            if analyze_imports:
                # Extract imports
                import_pattern = r'(?:import|const|let|var)\s+.*\s+(?:from|require)\s*\(?[\'"`]([^\'"`]+)[\'"`]\)?'
                imports = re.findall(import_pattern, content)
                results["components"]["imports"] += len(imports)
            
            if analyze_functions:
                # Extract function definitions
                func_pattern = r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>))'
                func_matches = re.finditer(func_pattern, content)
                for match in func_matches:
                    func_name = match.group(1) or match.group(2)
                    functions.append({"name": func_name})
                    results["components"]["functions"] += 1
            
            if analyze_comments:
                # Extract JSDoc comments
                jsdoc_pattern = r'/\*\*\s*(.*?)\s*\*/'
                comments = re.findall(jsdoc_pattern, content, re.DOTALL)
                results["components"]["comments"] += len(comments)
            
            # Create note for the file
            note_content = _format_js_analysis(
                file_path,
                imports,
                functions,
                comments
            )
            
            note = Note(
                title=f"{file_path.stem} (JavaScript)",
                content=note_content,
                tags=["javascript", "code", "analysis"],
                linked_notes=[]
            )
            
            note.save(category_path)
            results["analyzed_files"] += 1
            
        except Exception as e:
            results["errors"].append(f"Error analyzing {file_path}: {str(e)}")


def _analyze_generic_files(
    files: List[Path],
    category_path: Path,
    kb_path: Path,
    language: str,
    results: Dict[str, Any]
):
    """Generic analysis for other language files."""
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic analysis
            lines = content.split('\n')
            
            # Count basic metrics
            metrics = {
                "lines": len(lines),
                "non_empty_lines": len([l for l in lines if l.strip()]),
                "comment_lines": 0
            }
            
            # Detect comments based on language
            comment_chars = {
                "cpp": ["//", "/*"],
                "java": ["//", "/*"],
                "go": ["//", "/*"],
                "rust": ["//", "/*"],
                "ruby": ["#"],
                "php": ["//", "/*", "#"],
                "csharp": ["//", "/*"],
                "swift": ["//", "/*"],
                "kotlin": ["//", "/*"],
                "shell": ["#"],
            }
            
            if language in comment_chars:
                for line in lines:
                    stripped = line.strip()
                    if any(stripped.startswith(char) for char in comment_chars[language]):
                        metrics["comment_lines"] += 1
            
            # Create note
            note_content = f"""# {file_path.name}

## File Information
- **Language**: {language.title()}
- **Path**: {file_path.relative_to(file_path.parent.parent.parent)}
- **Size**: {file_path.stat().st_size} bytes

## Metrics
- **Total Lines**: {metrics['lines']}
- **Non-empty Lines**: {metrics['non_empty_lines']}
- **Comment Lines**: {metrics['comment_lines']}
- **Comment Ratio**: {metrics['comment_lines'] / max(metrics['non_empty_lines'], 1) * 100:.1f}%

## Content Preview
```{language}
{content[:500]}{"..." if len(content) > 500 else ""}
```
"""
            
            note = Note(
                title=f"{file_path.stem} ({language.title()})",
                content=note_content,
                tags=[language, "code", "analysis"]
            )
            
            note.save(category_path)
            results["analyzed_files"] += 1
            
        except Exception as e:
            results["errors"].append(f"Error analyzing {file_path}: {str(e)}")


def _create_overview_note(kb_path: Path, code_path: Path, results: Dict[str, Any]):
    """Create an overview note for the codebase analysis."""
    content = f"""# Codebase Overview

## Project Information
- **Name**: {code_path.name}
- **Path**: {code_path}
- **Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Summary
- **Total Files**: {results['total_files']}
- **Analyzed Files**: {results['analyzed_files']}
- **Languages**: {', '.join(results['languages'].keys())}

## Language Distribution
"""
    
    for language, count in results['languages'].items():
        percentage = (count / results['total_files']) * 100 if results['total_files'] > 0 else 0
        content += f"- **{language.title()}**: {count} files ({percentage:.1f}%)\n"
    
    content += f"""
## Component Summary
- **Functions**: {results['components']['functions']}
- **Classes**: {results['components']['classes']}
- **Imports**: {results['components']['imports']}
- **Comments/Docs**: {results['components']['comments']}

## Analysis Errors
{len(results['errors'])} errors encountered during analysis.

## Navigation
- [[Architecture]] - Project structure and design
- [[Components]] - Code components by language
- [[Documentation]] - Generated documentation
- [[Patterns]] - Identified patterns and practices
"""
    
    note = Note(
        title="Codebase Overview",
        content=content,
        tags=["overview", "analysis", "codebase"]
    )
    
    overview_path = ensure_directory(kb_path / "Overview")
    note.save(overview_path)


def _analyze_project_structure(code_path: Path, kb_path: Path, results: Dict[str, Any]):
    """Analyze and document project structure."""
    structure = {
        "directories": [],
        "config_files": [],
        "documentation": [],
        "tests": []
    }
    
    # Analyze directory structure
    for item in code_path.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            structure["directories"].append({
                "name": item.name,
                "type": _identify_directory_type(item.name)
            })
    
    # Identify config files
    config_patterns = [
        "*.json", "*.yml", "*.yaml", "*.toml", "*.ini",
        "Dockerfile", "Makefile", ".gitignore", ".env*"
    ]
    
    for pattern in config_patterns:
        for config_file in code_path.glob(pattern):
            structure["config_files"].append(config_file.name)
    
    # Find documentation
    doc_patterns = ["README*", "CONTRIBUTING*", "LICENSE*", "CHANGELOG*", "docs/"]
    for pattern in doc_patterns:
        for doc in code_path.glob(pattern):
            structure["documentation"].append(doc.name)
    
    # Find test directories
    test_patterns = ["test*", "tests*", "spec*", "__tests__"]
    for pattern in test_patterns:
        for test_dir in code_path.glob(pattern):
            if test_dir.is_dir():
                structure["tests"].append(test_dir.name)
    
    # Create architecture note
    content = _format_architecture_doc(structure)
    
    note = Note(
        title="Project Architecture",
        content=content,
        tags=["architecture", "structure", "codebase"]
    )
    
    arch_path = ensure_directory(kb_path / "Architecture")
    note.save(arch_path)


# Formatting helper functions

def _format_python_analysis(
    file_path: Path,
    imports: List[Dict],
    functions: List[Dict],
    classes: List[Dict],
    docstrings: List[Dict]
) -> str:
    """Format Python file analysis as markdown."""
    content = f"""# {file_path.name}

## File Information
- **Type**: Python Module
- **Path**: {file_path}

## Imports ({len(imports)})
"""
    
    if imports:
        for imp in imports[:10]:  # Limit to first 10
            names_str = f"({imp['names']})" if imp.get("names") else ""
            content += f"- `{imp['module']}` {names_str}\n"
        if len(imports) > 10:
            content += f"- ... and {len(imports) - 10} more\n"
    
    content += f"""
## Functions ({len(functions)})
"""
    
    if functions:
        for func in functions[:10]:
            content += f"### `{func['name']}({', '.join(func.get('args', []))})`\n"
            if func.get('docstring'):
                content += f"{func['docstring'][:200]}...\n\n"
            else:
                content += "No documentation\n\n"
        if len(functions) > 10:
            content += f"... and {len(functions) - 10} more functions\n"
    
    content += f"""
## Classes ({len(classes)})
"""
    
    if classes:
        for cls in classes[:10]:
            content += f"### `{cls['name']}`\n"
            if cls.get('bases'):
                content += f"**Inherits from**: {', '.join(cls['bases'])}\n"
            if cls.get('docstring'):
                content += f"{cls['docstring'][:200]}...\n"
            if cls.get('methods'):
                content += f"**Methods**: {', '.join(cls['methods'][:5])}\n"
            content += "\n"
        if len(classes) > 10:
            content += f"... and {len(classes) - 10} more classes\n"
    
    return content


def _format_js_analysis(
    file_path: Path,
    imports: List[str],
    functions: List[Dict],
    comments: List[str]
) -> str:
    """Format JavaScript file analysis as markdown."""
    content = f"""# {file_path.name}

## File Information
- **Type**: JavaScript/TypeScript Module
- **Path**: {file_path}

## Imports ({len(imports)})
"""
    
    if imports:
        for imp in imports[:10]:
            content += f"- `{imp}`\n"
        if len(imports) > 10:
            content += f"- ... and {len(imports) - 10} more\n"
    
    content += f"""
## Functions ({len(functions)})
"""
    
    if functions:
        for func in functions[:10]:
            content += f"- `{func['name']}()`\n"
        if len(functions) > 10:
            content += f"- ... and {len(functions) - 10} more\n"
    
    content += f"""
## Documentation Comments ({len(comments)})
"""
    
    if comments:
        for comment in comments[:5]:
            content += f"```\n{comment[:200]}{'...' if len(comment) > 200 else ''}\n```\n\n"
        if len(comments) > 5:
            content += f"... and {len(comments) - 5} more comments\n"
    
    return content


def _identify_directory_type(name: str) -> str:
    """Identify the type of directory based on its name."""
    patterns = {
        "source": ["src", "source", "lib", "app"],
        "tests": ["test", "tests", "spec", "__tests__"],
        "documentation": ["docs", "documentation", "doc"],
        "configuration": ["config", "conf", ".config"],
        "assets": ["assets", "static", "public", "resources"],
        "build": ["build", "dist", "output", "out"],
        "dependencies": ["node_modules", "venv", "env", "vendor"]
    }
    
    name_lower = name.lower()
    for dir_type, matches in patterns.items():
        if any(match in name_lower for match in matches):
            return dir_type
    
    return "other"


def _format_architecture_doc(structure: Dict[str, List]) -> str:
    """Format architecture documentation."""
    content = """# Project Architecture

## Directory Structure
"""
    
    for dir_info in structure["directories"]:
        content += f"- **{dir_info['name']}/** - {dir_info['type'].title()}\n"
    
    content += """
## Configuration Files
"""
    
    for config in structure["config_files"]:
        content += f"- `{config}`\n"
    
    content += """
## Documentation
"""
    
    for doc in structure["documentation"]:
        content += f"- {doc}\n"
    
    content += """
## Test Structure
"""
    
    for test in structure["tests"]:
        content += f"- {test}/\n"
    
    return content


# Pattern extraction helpers

def _identify_design_patterns(content: str) -> List[str]:
    """Identify common design patterns in code."""
    patterns = []
    
    # Common pattern indicators
    pattern_indicators = {
        "singleton": ["singleton", "getInstance", "_instance"],
        "factory": ["factory", "create", "build"],
        "observer": ["observer", "subscribe", "notify", "listener"],
        "decorator": ["decorator", "wrapper", "@"],
        "adapter": ["adapter", "adapt", "wrapper"],
        "strategy": ["strategy", "algorithm", "behavior"],
        "template": ["template", "abstract", "hook"],
        "mvc": ["model", "view", "controller"],
        "repository": ["repository", "store", "dao"]
    }
    
    content_lower = content.lower()
    
    for pattern, indicators in pattern_indicators.items():
        if any(indicator in content_lower for indicator in indicators):
            patterns.append(pattern)
    
    return patterns


def _analyze_naming_conventions(content: str) -> List[Dict[str, str]]:
    """Analyze naming conventions used in code."""
    conventions = []
    
    # Function naming
    func_pattern = r'(?:def|function)\s+([a-zA-Z_]\w*)'
    func_names = re.findall(func_pattern, content)
    
    if func_names:
        # Check convention
        snake_case = sum(1 for n in func_names if '_' in n and n.islower())
        camel_case = sum(1 for n in func_names if n[0].islower() and any(c.isupper() for c in n))
        pascal_case = sum(1 for n in func_names if n[0].isupper())
        
        dominant = max(
            ("snake_case", snake_case),
            ("camelCase", camel_case),
            ("PascalCase", pascal_case),
            key=lambda x: x[1]
        )
        
        if dominant[1] > 0:
            conventions.append({
                "type": "function_naming",
                "convention": dominant[0],
                "confidence": dominant[1] / len(func_names)
            })
    
    return conventions


def _analyze_code_structure(content: str) -> List[Dict[str, Any]]:
    """Analyze code structure patterns."""
    structure_patterns = []
    
    # Module structure
    if "import" in content or "from" in content:
        imports_at_top = content.find("import") < 200 or content.find("from") < 200
        structure_patterns.append({
            "pattern": "imports_at_top",
            "present": imports_at_top
        })
    
    # Docstring presence
    has_module_docstring = content.strip().startswith('"""') or content.strip().startswith("'''")
    structure_patterns.append({
        "pattern": "module_docstring",
        "present": has_module_docstring
    })
    
    return structure_patterns


def _consolidate_patterns(patterns: Dict[str, List], min_occurrences: int) -> Dict[str, List]:
    """Consolidate and filter patterns by occurrence."""
    consolidated = {}
    
    for pattern_type, pattern_list in patterns.items():
        # Count occurrences
        counts = defaultdict(int)
        for pattern in pattern_list:
            if isinstance(pattern, dict):
                key = str(pattern)
            else:
                key = pattern
            counts[key] += 1
        
        # Filter by minimum occurrences
        filtered = []
        for pattern_key, count in counts.items():
            if count >= min_occurrences:
                if isinstance(pattern_list[0], dict):
                    filtered.append(eval(pattern_key))
                else:
                    filtered.append(pattern_key)
        
        consolidated[pattern_type] = filtered
    
    return consolidated


def _format_pattern_documentation(pattern_type: str, patterns: List) -> str:
    """Format pattern documentation."""
    content = f"""# {pattern_type.replace('_', ' ').title()}

## Identified Patterns

"""
    
    for i, pattern in enumerate(patterns, 1):
        if isinstance(pattern, dict):
            content += f"### Pattern {i}\n"
            for key, value in pattern.items():
                content += f"- **{key}**: {value}\n"
            content += "\n"
        else:
            content += f"- {pattern}\n"
    
    content += """
## Recommendations

Based on the identified patterns, consider:
- Documenting these patterns for consistency
- Creating code templates
- Setting up linting rules
- Establishing team conventions
"""
    
    return content


# Dependency analysis helpers

def _analyze_python_deps(code_path: Path, include_versions: bool) -> Dict[str, Any]:
    """Analyze Python dependencies."""
    deps = {
        "dependencies": [],
        "dev_dependencies": []
    }
    
    req_file = code_path / "requirements.txt"
    if req_file.exists():
        with open(req_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if include_versions:
                        deps["dependencies"].append(line)
                    else:
                        # Strip version specifiers
                        pkg = re.split(r'[<>=!]', line)[0].strip()
                        deps["dependencies"].append(pkg)
    
    # Check for dev requirements
    dev_req_file = code_path / "requirements-dev.txt"
    if dev_req_file.exists():
        with open(dev_req_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if include_versions:
                        deps["dev_dependencies"].append(line)
                    else:
                        pkg = re.split(r'[<>=!]', line)[0].strip()
                        deps["dev_dependencies"].append(pkg)
    
    return deps


def _analyze_node_deps(code_path: Path, include_versions: bool) -> Dict[str, Any]:
    """Analyze Node.js dependencies."""
    deps = {
        "dependencies": [],
        "dev_dependencies": []
    }
    
    package_file = code_path / "package.json"
    if package_file.exists():
        with open(package_file, 'r') as f:
            package_data = json.load(f)
        
        if "dependencies" in package_data:
            for pkg, version in package_data["dependencies"].items():
                if include_versions:
                    deps["dependencies"].append(f"{pkg}@{version}")
                else:
                    deps["dependencies"].append(pkg)
        
        if "devDependencies" in package_data:
            for pkg, version in package_data["devDependencies"].items():
                if include_versions:
                    deps["dev_dependencies"].append(f"{pkg}@{version}")
                else:
                    deps["dev_dependencies"].append(pkg)
    
    return deps


def _format_dependency_doc(language: str, deps: Dict[str, Any]) -> str:
    """Format dependency documentation."""
    content = f"""# {language} Dependencies

## Production Dependencies ({len(deps.get('dependencies', []))})

"""
    
    for dep in deps.get("dependencies", []):
        content += f"- `{dep}`\n"
    
    content += f"""
## Development Dependencies ({len(deps.get('dev_dependencies', []))})

"""
    
    for dep in deps.get("dev_dependencies", []):
        content += f"- `{dep}`\n"
    
    return content


def _format_dependency_summary(results: Dict[str, Any]) -> str:
    """Format dependency summary documentation."""
    content = f"""# Dependency Analysis Summary

## Overview
- **Total Dependencies**: {results['total_dependencies']}
- **Languages**: {', '.join(results['languages'].keys())}
- **Files Found**: {', '.join(results['dependency_files_found'])}

## By Language
"""
    
    for language, deps in results['languages'].items():
        if isinstance(deps, dict) and 'dependencies' in deps:
            content += f"### {language.title()}\n"
            content += f"- Production: {len(deps.get('dependencies', []))}\n"
            content += f"- Development: {len(deps.get('dev_dependencies', []))}\n\n"
    
    content += """
## Security Considerations
- Review dependencies for known vulnerabilities
- Keep dependencies up to date
- Use lock files for consistent builds
- Audit dependencies regularly
"""
    
    return content


# Documentation generation helpers

def _generate_file_documentation(
    file_path: Path,
    include_examples: bool = True,
    include_tests: bool = True
) -> Optional[Dict[str, Any]]:
    """Generate documentation for a source file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        doc = {
            "content": "",
            "language": _detect_language(file_path),
            "examples": 0,
            "tests": 0,
            "references": []
        }
        
        if doc["language"] == "python":
            doc = _generate_python_doc(content, file_path, include_examples, include_tests)
        else:
            doc["content"] = _generate_generic_doc(content, file_path, doc["language"])
        
        return doc
        
    except Exception as e:
        print(f"Error generating documentation for {file_path}: {e}")
        return None


def _generate_python_doc(
    content: str,
    file_path: Path,
    include_examples: bool,
    include_tests: bool
) -> Dict[str, Any]:
    """Generate Python-specific documentation."""
    doc = {
        "content": f"# {file_path.stem} Module Documentation\n\n",
        "language": "python",
        "examples": 0,
        "tests": 0,
        "references": []
    }
    
    try:
        tree = ast.parse(content)
        
        # Module docstring
        module_doc = ast.get_docstring(tree)
        if module_doc:
            doc["content"] += f"## Module Description\n\n{module_doc}\n\n"
        
        # Document functions and classes
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                func_doc = _document_python_function(node, include_examples)
                doc["content"] += func_doc
                doc["examples"] += 1 if "Example:" in func_doc else 0
                
            elif isinstance(node, ast.ClassDef):
                class_doc = _document_python_class(node, include_examples)
                doc["content"] += class_doc
                doc["references"].extend(_extract_class_references(node))
        
    except SyntaxError:
        doc["content"] += "Error: Unable to parse Python file\n"
    
    return doc


def _document_python_function(node: ast.FunctionDef, include_examples: bool) -> str:
    """Document a Python function."""
    doc = f"\n## Function: `{node.name}`\n\n"
    
    # Function signature
    args = []
    for arg in node.args.args:
        args.append(arg.arg)
    
    doc += f"```python\ndef {node.name}({', '.join(args)}):\n```\n\n"
    
    # Docstring
    docstring = ast.get_docstring(node)
    if docstring:
        doc += f"{docstring}\n\n"
    else:
        doc += "No documentation available.\n\n"
    
    return doc


def _document_python_class(node: ast.ClassDef, include_examples: bool) -> str:
    """Document a Python class."""
    doc = f"\n## Class: `{node.name}`\n\n"
    
    # Base classes
    if node.bases:
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
        if bases:
            doc += f"**Inherits from**: {', '.join(bases)}\n\n"
    
    # Class docstring
    docstring = ast.get_docstring(node)
    if docstring:
        doc += f"{docstring}\n\n"
    
    # Document methods
    doc += "### Methods\n\n"
    for item in node.body:
        if isinstance(item, ast.FunctionDef):
            doc += f"#### `{item.name}({', '.join(arg.arg for arg in item.args.args)})`\n"
            method_doc = ast.get_docstring(item)
            if method_doc:
                doc += f"{method_doc[:200]}{'...' if len(method_doc) > 200 else ''}\n\n"
            else:
                doc += "No documentation.\n\n"
    
    return doc


def _generate_generic_doc(content: str, file_path: Path, language: str) -> str:
    """Generate generic documentation for non-Python files."""
    doc = f"# {file_path.stem} Documentation\n\n"
    doc += f"**Language**: {language.title()}\n"
    doc += f"**File**: {file_path.name}\n\n"
    
    # Extract comments
    comments = []
    if language in ["javascript", "typescript", "java", "cpp", "go", "rust"]:
        # Multi-line comments
        multiline_pattern = r'/\*\*(.*?)\*/'
        comments.extend(re.findall(multiline_pattern, content, re.DOTALL))
        
        # Single-line comments
        single_pattern = r'//\s*(.+)$'
        comments.extend(re.findall(single_pattern, content, re.MULTILINE))
    
    if comments:
        doc += "## Documentation Comments\n\n"
        for comment in comments[:10]:
            doc += f"```\n{comment.strip()}\n```\n\n"
    
    return doc


def _detect_language(file_path: Path) -> str:
    """Detect programming language from file extension."""
    ext = file_path.suffix.lower()
    
    for language, extensions in LANGUAGE_EXTENSIONS.items():
        if ext in extensions:
            return language
    
    return "unknown"


def _extract_references(functions: List[Dict], classes: List[Dict]) -> List[str]:
    """Extract references from code components."""
    references = []
    
    for func in functions:
        # Extract references from function names and docstrings
        if "calls" in func:
            references.extend(func["calls"])
    
    for cls in classes:
        # Extract base class references
        if "bases" in cls:
            references.extend(cls["bases"])
    
    return list(set(references))


def _extract_class_references(node: ast.ClassDef) -> List[str]:
    """Extract references from a class definition."""
    references = []
    
    # Base classes
    for base in node.bases:
        if isinstance(base, ast.Name):
            references.append(base.id)
    
    return references


def _get_module_path(file_path: Path, root_path: Path) -> Path:
    """Get module path relative to root."""
    try:
        relative = file_path.relative_to(root_path)
        return relative.parent
    except ValueError:
        return Path()


# Helper extraction functions

def _extract_import_info(node) -> Dict[str, Any]:
    """Extract import information from AST node."""
    info = {"module": "", "names": []}
    
    if isinstance(node, ast.Import):
        info["module"] = node.names[0].name
        info["names"] = [alias.asname or alias.name for alias in node.names]
    elif isinstance(node, ast.ImportFrom):
        info["module"] = node.module or ""
        info["names"] = [alias.asname or alias.name for alias in node.names]
    
    return info


def _extract_function_info(node: ast.FunctionDef) -> Dict[str, Any]:
    """Extract function information from AST node."""
    info = {
        "name": node.name,
        "args": [arg.arg for arg in node.args.args],
        "docstring": ast.get_docstring(node),
        "decorators": []
    }
    
    # Extract decorators
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Name):
            info["decorators"].append(decorator.id)
        elif isinstance(decorator, ast.Attribute):
            info["decorators"].append(f"{decorator.value.id}.{decorator.attr}")
    
    return info


def _extract_class_info(node: ast.ClassDef) -> Dict[str, Any]:
    """Extract class information from AST node."""
    info = {
        "name": node.name,
        "bases": [],
        "docstring": ast.get_docstring(node),
        "methods": [],
        "attributes": []
    }
    
    # Extract base classes
    for base in node.bases:
        if isinstance(base, ast.Name):
            info["bases"].append(base.id)
    
    # Extract methods
    for item in node.body:
        if isinstance(item, ast.FunctionDef):
            info["methods"].append(item.name)
    
    return info