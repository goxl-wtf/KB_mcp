#!/usr/bin/env python3
"""Migration script to convert JSON-based knowledge bases to hierarchical structure."""

import sys
sys.path.insert(0, 'src')

import argparse
from pathlib import Path
from utils.migration import MigrationManager
import json


def main():
    parser = argparse.ArgumentParser(
        description="Migrate JSON-based knowledge bases to hierarchical structure"
    )
    parser.add_argument(
        "source",
        type=str,
        help="Path to source directory containing JSON KB files"
    )
    parser.add_argument(
        "target",
        type=str,
        help="Path to target directory for hierarchical KBs"
    )
    parser.add_argument(
        "--single-file",
        type=str,
        help="Migrate a single KB file instead of directory"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without actually doing it"
    )
    
    args = parser.parse_args()
    
    source_path = Path(args.source)
    target_path = Path(args.target)
    
    if not source_path.exists():
        print(f"Error: Source path '{source_path}' does not exist")
        return 1
    
    # Create target directory if it doesn't exist
    target_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Migration Configuration:")
    print(f"  Source: {source_path}")
    print(f"  Target: {target_path}")
    print(f"  Dry run: {args.dry_run}")
    print()
    
    if args.dry_run:
        print("DRY RUN MODE - No changes will be made")
        print()
    
    # Create migration manager
    manager = MigrationManager(source_path, target_path)
    
    if args.single_file:
        # Migrate single file
        json_file = Path(args.single_file)
        if not json_file.exists():
            print(f"Error: File '{json_file}' does not exist")
            return 1
        
        print(f"Migrating single KB: {json_file}")
        
        if not args.dry_run:
            try:
                kb_title = json_file.stem.replace("_", " ")
                result = manager.migrate_kb(json_file, kb_title)
                print(f"✅ Successfully migrated: {kb_title}")
                print(f"   Notes: {result['notes']}")
                print(f"   Tasks: {result['tasks']}")
            except Exception as e:
                print(f"❌ Failed to migrate: {e}")
                return 1
    else:
        # Migrate all KBs in directory
        print("Scanning for JSON knowledge bases...")
        json_files = list(source_path.glob("*.json"))
        print(f"Found {len(json_files)} JSON files")
        print()
        
        if args.dry_run:
            for json_file in json_files:
                print(f"Would migrate: {json_file.name}")
        else:
            results = manager.migrate_all_kbs()
            
            print("\nMigration Summary:")
            print(f"  Total KBs: {results['stats']['total_kbs']}")
            print(f"  Successfully migrated: {len(results['migrated'])}")
            print(f"  Failed: {len(results['failed'])}")
            
            if results['failed']:
                print("\nFailed migrations:")
                for failure in results['failed']:
                    print(f"  - {failure['file']}: {failure['error']}")
            
            print(f"\nMigration report saved to: {target_path / 'migration_report.json'}")
    
    print("\n✅ Migration completed")
    return 0


if __name__ == "__main__":
    sys.exit(main())