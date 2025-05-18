#!/usr/bin/env python3
"""Direct test of the hierarchical KB functionality."""

import sys
sys.path.insert(0, 'src')

from pathlib import Path
import tempfile
import shutil

# Import models
from models import KnowledgeBase, Category, Note

def test_hierarchical_kb():
    """Test the hierarchical KB functionality directly."""
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        storage_path = Path(temp_dir)
        print(f"Testing with storage path: {storage_path}\n")
        
        # Test 1: Create a knowledge base
        print("1. Creating knowledge base...")
        kb = KnowledgeBase(
            title="Development Guide",
            description="A comprehensive development guide",
            default_categories=["Getting Started", "API Reference", "Examples", "Best Practices"],
            tags=["development", "documentation"]
        )
        kb.save(storage_path)
        print(f"✓ Created KB: {kb.title}")
        print(f"  ID: {kb.id}")
        print(f"  Path: {kb.path}")
        
        # Test 2: Create categories
        print("\n2. Creating categories...")
        
        # Create a subcategory under API Reference
        api_ref_path = kb.path / "API_Reference"
        rest_api_category = Category(
            name="REST API",
            description="REST API documentation",
            parent="API_Reference"
        )
        rest_api_category.path = api_ref_path / "REST_API"
        rest_api_category.relative_path = "API_Reference/REST_API"
        rest_api_category.save()
        print(f"✓ Created category: {rest_api_category.name}")
        
        # Create another subcategory
        graphql_category = Category(
            name="GraphQL API",
            description="GraphQL API documentation",
            parent="API_Reference"
        )
        graphql_category.path = api_ref_path / "GraphQL_API"
        graphql_category.relative_path = "API_Reference/GraphQL_API"
        graphql_category.save()
        print(f"✓ Created category: {graphql_category.name}")
        
        # Test 3: Create notes
        print("\n3. Creating notes...")
        
        # Create a note in the REST API category
        rest_note = Note(
            title="Authentication Guide",
            content="""# Authentication Guide

## Overview
This guide explains how to authenticate with our REST API.

## Authentication Methods
1. API Key Authentication
2. OAuth 2.0
3. JWT Tokens

## Example
```python
import requests

headers = {
    'Authorization': 'Bearer YOUR_API_KEY'
}
response = requests.get('https://api.example.com/v1/users', headers=headers)
```

For more information, see [[oauth_guide]] and [[jwt_guide]].
""",
            tags=["authentication", "security", "rest"],
            linked_notes=["oauth_guide", "jwt_guide"]
        )
        rest_note.save(rest_api_category.path)
        print(f"✓ Created note: {rest_note.title}")
        
        # Create another note
        graphql_note = Note(
            title="GraphQL Schema",
            content="""# GraphQL Schema

## User Type
```graphql
type User {
  id: ID!
  username: String!
  email: String!
  createdAt: DateTime!
}
```

## Query Type
```graphql
type Query {
  user(id: ID!): User
  users(limit: Int = 10): [User!]!
}
```

Related: [[authentication_guide]]
""",
            tags=["graphql", "schema", "api"],
            linked_notes=["authentication_guide"]
        )
        graphql_note.save(graphql_category.path)
        print(f"✓ Created note: {graphql_note.title}")
        
        # Test 4: Read back the structure
        print("\n4. Reading back the structure...")
        
        # List all categories
        all_categories = Category.list_all(kb.path)
        print(f"✓ Found {len(all_categories)} categories")
        for cat in all_categories:
            note_count = len(cat.get_notes())
            print(f"  - {cat.relative_path} ({note_count} notes)")
        
        # Test 5: Search for notes
        print("\n5. Testing note retrieval...")
        
        # Load a specific note
        loaded_note = Note.load(rest_note.path)
        print(f"✓ Loaded note: {loaded_note.title}")
        print(f"  Tags: {loaded_note.tags}")
        print(f"  Links: {loaded_note.linked_notes}")
        
        # Extract links from content
        content_links = loaded_note.extract_links_from_content()
        print(f"  Content links: {content_links}")
        
        # Test 6: Test cross-references
        print("\n6. Testing cross-references...")
        
        # Create a derived KB
        derived_kb = KnowledgeBase(
            title="API Best Practices",
            description="Best practices derived from the main guide",
            parent_kb=kb.id,
            tags=["best-practices", "derived"]
        )
        derived_kb.relationships.append(kb.id)
        derived_kb.save(storage_path)
        print(f"✓ Created derived KB: {derived_kb.title}")
        print(f"  Parent: {derived_kb.parent_kb}")
        
        # Test 7: List all KBs
        print("\n7. Listing all knowledge bases...")
        all_kbs = KnowledgeBase.list_all(storage_path)
        print(f"✓ Found {len(all_kbs)} knowledge bases")
        for kb_item in all_kbs:
            print(f"  - {kb_item.title} (ID: {kb_item.id})")
            if kb_item.parent_kb:
                print(f"    Parent: {kb_item.parent_kb}")
        
        print("\n✅ All tests completed successfully!")
        
        # Show the final directory structure
        print("\nFinal directory structure:")
        def print_tree(path, prefix="", level=0):
            if level > 5:  # Prevent too deep recursion
                return
            items = sorted(path.iterdir())
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                print(f"{prefix}{current_prefix}{item.name}")
                if item.is_dir() and not item.name.startswith('.'):
                    next_prefix = prefix + ("    " if is_last else "│   ")
                    print_tree(item, next_prefix, level + 1)
        
        print_tree(storage_path)

if __name__ == "__main__":
    test_hierarchical_kb()