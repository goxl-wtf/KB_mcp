#!/usr/bin/env python3
"""Test codebase analysis functionality."""

import sys
sys.path.insert(0, 'src')

import tempfile
from pathlib import Path
import textwrap

from models import KnowledgeBase, Category, Note
from main import state, register_all_tools, initialize_storage


def create_test_codebase(path: Path):
    """Create a test codebase structure."""
    # Create directories
    (path / "src").mkdir(exist_ok=True)
    (path / "src" / "modules").mkdir(exist_ok=True)
    (path / "tests").mkdir(exist_ok=True)
    (path / "docs").mkdir(exist_ok=True)
    
    # Create Python files
    main_py = path / "src" / "main.py"
    main_py.write_text(textwrap.dedent('''
        """Main module for the test application."""
        
        import os
        import sys
        from modules.utils import process_data
        from modules.database import Database
        
        
        class Application:
            """Main application class."""
            
            def __init__(self, config_path: str):
                """Initialize the application.
                
                Args:
                    config_path: Path to configuration file
                """
                self.config = self._load_config(config_path)
                self.db = Database(self.config["database"])
            
            def run(self):
                """Run the main application logic."""
                data = self.db.fetch_data()
                result = process_data(data)
                return result
            
            def _load_config(self, path: str) -> dict:
                """Load configuration from file."""
                # Implementation here
                return {}
        
        
        def main():
            """Application entry point."""
            app = Application("config.json")
            app.run()
        
        
        if __name__ == "__main__":
            main()
    '''))
    
    utils_py = path / "src" / "modules" / "utils.py"
    utils_py.write_text(textwrap.dedent('''
        """Utility functions for data processing."""
        
        import json
        import logging
        from typing import List, Dict, Any
        
        
        def process_data(data: List[Dict[str, Any]]) -> Dict[str, Any]:
            """Process input data and return results.
            
            Args:
                data: List of data items to process
                
            Returns:
                Processed results dictionary
            """
            results = {
                "total": len(data),
                "processed": 0,
                "errors": []
            }
            
            for item in data:
                try:
                    # Process item
                    results["processed"] += 1
                except Exception as e:
                    results["errors"].append(str(e))
            
            return results
        
        
        def validate_input(value: Any) -> bool:
            """Validate input value."""
            # Basic validation logic
            return value is not None
    '''))
    
    database_py = path / "src" / "modules" / "database.py"
    database_py.write_text(textwrap.dedent('''
        """Database module for data persistence."""
        
        from typing import List, Dict, Any
        
        
        class Database:
            """Database interface class."""
            
            def __init__(self, config: dict):
                """Initialize database connection.
                
                Args:
                    config: Database configuration
                """
                self.config = config
                self._connect()
            
            def fetch_data(self) -> List[Dict[str, Any]]:
                """Fetch data from database."""
                # Mock implementation
                return [
                    {"id": 1, "name": "Item 1"},
                    {"id": 2, "name": "Item 2"}
                ]
            
            def _connect(self):
                """Establish database connection."""
                pass
    '''))
    
    # Create test file
    test_utils_py = path / "tests" / "test_utils.py"
    test_utils_py.write_text(textwrap.dedent('''
        """Tests for utility functions."""
        
        import unittest
        from src.modules.utils import process_data, validate_input
        
        
        class TestUtils(unittest.TestCase):
            """Test utility functions."""
            
            def test_process_data(self):
                """Test data processing."""
                data = [{"id": 1}, {"id": 2}]
                result = process_data(data)
                self.assertEqual(result["total"], 2)
                self.assertEqual(result["processed"], 2)
    '''))
    
    # Create requirements.txt
    (path / "requirements.txt").write_text(textwrap.dedent('''
        pytest>=7.0.0
        requests>=2.28.0
        sqlalchemy>=1.4.0
        pydantic>=1.10.0
    '''))
    
    # Create README
    (path / "README.md").write_text(textwrap.dedent('''
        # Test Application
        
        This is a test application for demonstrating codebase analysis.
        
        ## Features
        - Data processing
        - Database integration
        - Modular architecture
        
        ## Installation
        ```bash
        pip install -r requirements.txt
        ```
    '''))
    
    # Create JavaScript file for mixed-language testing
    (path / "src" / "frontend.js").write_text(textwrap.dedent('''
        /**
         * Frontend module for the application
         */
        
        import axios from 'axios';
        
        /**
         * Fetch data from API
         * @param {string} endpoint - API endpoint
         * @returns {Promise<Object>} API response
         */
        async function fetchData(endpoint) {
            try {
                const response = await axios.get(endpoint);
                return response.data;
            } catch (error) {
                console.error('Error fetching data:', error);
                throw error;
            }
        }
        
        /**
         * Process user input
         * @param {string} input - User input
         */
        function processInput(input) {
            // Input processing logic
            return input.trim().toLowerCase();
        }
        
        export { fetchData, processInput };
    '''))


def test_codebase_analysis():
    """Test codebase analysis functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test storage
        storage_path = Path(temp_dir) / "storage"
        storage_path.mkdir(exist_ok=True)
        state.storage_path = storage_path
        initialize_storage()
        register_all_tools()
        
        # Create test codebase
        codebase_path = Path(temp_dir) / "test_codebase"
        codebase_path.mkdir(exist_ok=True)
        create_test_codebase(codebase_path)
        
        print("=== Codebase Analysis Test ===\n")
        print(f"Test codebase: {codebase_path}")
        print(f"Storage: {storage_path}\n")
        
        # Test basic codebase analysis
        print("1. Testing basic codebase analysis...")
        
        from tools.analysis_tools import analyze_codebase
        
        result = analyze_codebase(
            codebase_path=str(codebase_path),
            kb_title="Test Codebase Analysis",
            analyze_imports=True,
            analyze_functions=True,
            analyze_classes=True,
            analyze_comments=True
        )
        
        if "error" not in result:
            print(f"✓ Analysis completed:")
            print(f"  - KB ID: {result['kb_id']}")
            print(f"  - Total files: {result['total_files']}")
            print(f"  - Analyzed files: {result['analyzed_files']}")
            print(f"  - Languages: {', '.join(result['languages'].keys())}")
            print(f"  - Functions: {result['components']['functions']}")
            print(f"  - Classes: {result['components']['classes']}")
            print(f"  - Comments: {result['components']['comments']}")
            
            # Check created notes
            kb_path = storage_path / result['kb_id']
            notes = list(kb_path.rglob("*.md"))
            print(f"  - Notes created: {len(notes)}")
            
            # Sample a note
            if notes:
                sample_note = Note.load(notes[0])
                print(f"\nSample note: {sample_note.title}")
                print(f"Tags: {sample_note.tags}")
                print(f"Preview: {sample_note.content[:100]}...")
        else:
            print(f"❌ Error: {result['error']}")
        
        # Test documentation generation
        print("\n2. Testing documentation generation...")
        
        from tools.analysis_tools import generate_documentation
        
        if "kb_id" in result:
            doc_result = generate_documentation(
                source_path=str(codebase_path / "src"),
                output_kb_id=result['kb_id'],
                include_examples=True,
                include_tests=True
            )
            
            if "error" not in doc_result:
                print(f"✓ Documentation generated:")
                print(f"  - Files processed: {doc_result['files_processed']}")
                print(f"  - Documentation created: {doc_result['documentation_created']}")
                print(f"  - Examples extracted: {doc_result['examples_extracted']}")
            else:
                print(f"❌ Error: {doc_result['error']}")
        
        # Test pattern extraction
        print("\n3. Testing pattern extraction...")
        
        from tools.analysis_tools import extract_patterns
        
        if "kb_id" in result:
            pattern_result = extract_patterns(
                kb_id=result['kb_id'],
                min_occurrences=1
            )
            
            if "error" not in pattern_result:
                print(f"✓ Patterns extracted:")
                print(f"  - Total patterns: {pattern_result['total_patterns']}")
                for pattern_type, count in pattern_result['patterns_found'].items():
                    print(f"  - {pattern_type}: {count}")
            else:
                print(f"❌ Error: {pattern_result['error']}")
        
        # Test dependency analysis
        print("\n4. Testing dependency analysis...")
        
        from tools.analysis_tools import analyze_dependencies
        
        if "kb_id" in result:
            dep_result = analyze_dependencies(
                codebase_path=str(codebase_path),
                output_kb_id=result['kb_id'],
                include_versions=True
            )
            
            if "error" not in dep_result:
                print(f"✓ Dependencies analyzed:")
                print(f"  - Files found: {', '.join(dep_result['dependency_files_found'])}")
                print(f"  - Total dependencies: {dep_result['total_dependencies']}")
                for lang, deps in dep_result['languages'].items():
                    if isinstance(deps, dict) and 'dependencies' in deps:
                        print(f"  - {lang}: {len(deps['dependencies'])} dependencies")
            else:
                print(f"❌ Error: {dep_result['error']}")
        
        # Show final KB structure
        print("\n5. Final Knowledge Base Structure:")
        
        if "kb_id" in result:
            kb_path = storage_path / result['kb_id']
            
            def print_tree(path, prefix="", max_depth=4, current_depth=0):
                if current_depth >= max_depth:
                    return
                
                items = sorted(path.iterdir())
                for i, item in enumerate(items):
                    is_last = i == len(items) - 1
                    current_prefix = "└── " if is_last else "├── "
                    print(f"{prefix}{current_prefix}{item.name}")
                    
                    if item.is_dir() and not item.name.startswith('.'):
                        next_prefix = prefix + ("    " if is_last else "│   ")
                        print_tree(item, next_prefix, max_depth, current_depth + 1)
            
            print_tree(kb_path)
        
        print("\n✅ Codebase analysis test completed!")


if __name__ == "__main__":
    test_codebase_analysis()