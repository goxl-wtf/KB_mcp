#!/usr/bin/env python3
"""Demo of the Hierarchical Knowledge Base System."""

import sys
sys.path.insert(0, 'src')

from pathlib import Path
import json
from datetime import datetime

# Import models
from models import KnowledgeBase, Category, Note

def create_demo_kb():
    """Create a demonstration knowledge base."""
    demo_path = Path("demo_storage")
    demo_path.mkdir(exist_ok=True)
    
    print("=== Hierarchical Knowledge Base Demo ===\n")
    
    # Create main KB
    print("1. Creating Knowledge Base...")
    main_kb = KnowledgeBase(
        title="Software Engineering Guide",
        description="A comprehensive guide to software engineering practices",
        default_categories=["Architecture", "Design Patterns", "Best Practices", "Technologies"],
        tags=["engineering", "development", "guide"]
    )
    main_kb.save(demo_path)
    print(f"✓ Created KB: {main_kb.title}")
    
    # Create category structure
    print("\n2. Creating Category Structure...")
    
    # Architecture subcategories
    arch_path = main_kb.path / "Architecture"
    microservices_path = arch_path / "Microservices"
    microservices_path.mkdir(parents=True, exist_ok=True)
    
    serverless_path = arch_path / "Serverless"
    serverless_path.mkdir(parents=True, exist_ok=True)
    
    # Technologies subcategories
    tech_path = main_kb.path / "Technologies"
    frontend_path = tech_path / "Frontend"
    frontend_path.mkdir(parents=True, exist_ok=True)
    
    backend_path = tech_path / "Backend"
    backend_path.mkdir(parents=True, exist_ok=True)
    
    print("✓ Created category hierarchy")
    
    # Create interconnected notes
    print("\n3. Creating Interconnected Notes...")
    
    # Microservices note
    microservices_note = Note(
        title="Microservices Architecture",
        content="""# Microservices Architecture

Microservices architecture is a design approach where applications are built as a collection of small, independent services.

## Key Principles
- Single Responsibility
- Decentralized Data Management
- Design for Failure

## Benefits
- Scalability
- Technology Diversity
- Fault Isolation

## Related Topics
- [[api_gateway]] - Central entry point for microservices
- [[service_discovery]] - Automatic service location
- [[event_driven_architecture]] - Communication patterns
- See also: [[serverless_computing]] for comparison
""",
        tags=["architecture", "microservices", "distributed-systems"],
        linked_notes=["api_gateway", "service_discovery", "event_driven_architecture", "serverless_computing"]
    )
    microservices_note.save(microservices_path)
    
    # API Gateway note
    api_gateway_note = Note(
        title="API Gateway Pattern",
        content="""# API Gateway Pattern

An API Gateway is a server that acts as an API front-end, receiving API requests and routing them to appropriate microservices.

## Responsibilities
- Request Routing
- Authentication/Authorization
- Rate Limiting
- Load Balancing

## Implementation Options
- Kong
- AWS API Gateway
- Zuul

## Related Patterns
- [[microservices_architecture]] - The architecture this pattern supports
- [[backend_for_frontend]] - Specialized gateways for different clients
""",
        tags=["architecture", "api", "patterns", "microservices"],
        linked_notes=["microservices_architecture", "backend_for_frontend"]
    )
    api_gateway_note.save(microservices_path)
    
    # Serverless note
    serverless_note = Note(
        title="Serverless Computing",
        content="""# Serverless Computing

Serverless computing allows you to build and run applications without managing infrastructure.

## Key Characteristics
- No server management
- Event-driven execution
- Automatic scaling
- Pay-per-use pricing

## Popular Platforms
- AWS Lambda
- Azure Functions
- Google Cloud Functions

## Use Cases
- API backends
- Data processing
- Real-time file processing

## Comparison
- vs [[microservices_architecture]] - Different scaling approaches
- Related: [[event_driven_architecture]] - Natural fit for serverless
""",
        tags=["architecture", "serverless", "cloud", "computing"],
        linked_notes=["microservices_architecture", "event_driven_architecture"]
    )
    serverless_note.save(serverless_path)
    
    # Frontend note
    react_note = Note(
        title="React Best Practices",
        content="""# React Best Practices

Essential best practices for React development.

## Component Design
- Keep components small and focused
- Use functional components with hooks
- Implement proper prop validation

## State Management
- Use local state when possible
- Consider Context API before Redux
- Implement proper data flow

## Performance
- Use React.memo for expensive components
- Implement code splitting
- Optimize re-renders

## Testing
- Write unit tests for components
- Use React Testing Library
- Implement integration tests

## Related Topics
- [[frontend_architecture]] - Overall frontend design
- [[state_management_patterns]] - Different approaches
- Compare with [[vue_best_practices]]
""",
        tags=["frontend", "react", "javascript", "best-practices"],
        linked_notes=["frontend_architecture", "state_management_patterns", "vue_best_practices"]
    )
    react_note.save(frontend_path)
    
    print("✓ Created 4 interconnected notes")
    
    # Show relationships
    print("\n4. Knowledge Graph Visualization...")
    
    # Count statistics
    total_notes = len(list(main_kb.path.rglob("*.md")))
    total_categories = len(list(filter(lambda p: p.is_dir(), main_kb.path.rglob("*"))))
    total_links = sum(len(Note.load(p).linked_notes) for p in main_kb.path.rglob("*.md"))
    
    print(f"✓ Knowledge Base Statistics:")
    print(f"  - Categories: {total_categories}")
    print(f"  - Notes: {total_notes}")
    print(f"  - Cross-references: {total_links}")
    
    # Show sample search
    print("\n5. Search Demonstration...")
    
    # Search for "architecture"
    architecture_notes = []
    for note_path in main_kb.path.rglob("*.md"):
        note = Note.load(note_path)
        if "architecture" in note.content.lower() or "architecture" in note.tags:
            architecture_notes.append(note.title)
    
    print(f"✓ Notes about 'architecture': {len(architecture_notes)}")
    for title in architecture_notes:
        print(f"  - {title}")
    
    # Find related notes
    print("\n6. Related Notes Discovery...")
    
    # Find notes related to microservices
    ms_note = microservices_note
    related_titles = []
    for linked_id in ms_note.linked_notes:
        for note_path in main_kb.path.rglob(f"*{linked_id}*.md"):
            try:
                related_note = Note.load(note_path)
                related_titles.append(related_note.title)
            except:
                pass
    
    print(f"✓ Notes related to '{ms_note.title}':")
    for title in related_titles:
        print(f"  - {title}")
    
    # Create derived KB
    print("\n7. Creating Derived Knowledge Base...")
    
    patterns_kb = KnowledgeBase(
        title="Design Patterns Reference",
        description="A focused guide on software design patterns",
        parent_kb=main_kb.id,
        tags=["patterns", "reference", "derived"]
    )
    patterns_kb.save(demo_path)
    print(f"✓ Created derived KB: {patterns_kb.title}")
    print(f"  Parent: {patterns_kb.parent_kb}")
    
    # Show final structure
    print("\n8. Final Knowledge Base Structure:")
    print("\nDirectory Tree:")
    
    def print_tree(path, prefix="", max_depth=5, current_depth=0):
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
    
    print_tree(demo_path, max_depth=4)
    
    print("\n✅ Demo completed! Knowledge base created at: demo_storage/")
    print("\nTo explore the knowledge base:")
    print("1. Navigate to demo_storage/")
    print("2. Browse the markdown files and directory structure")
    print("3. Notice the cross-references in [[brackets]]")
    print("4. Check meta.json files for metadata")


if __name__ == "__main__":
    create_demo_kb()