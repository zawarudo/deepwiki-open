#!/usr/bin/env python3
"""
Simple database rebuild script for DeepWiki.

This script removes the existing embedding database to force a complete rebuild
with fresh embeddings on the next application run.

Usage:
    python scripts/utils/rebuild_database.py
    python scripts/utils/rebuild_database.py --repo-name MyRepo
    python scripts/utils/rebuild_database.py --force
    python scripts/utils/rebuild_database.py --list
"""

import os
import sys
import argparse
import glob
from pathlib import Path
from datetime import datetime


def find_database_files(repo_name=None):
    """Find all database files in the adalflow directory."""
    db_dir = os.path.expanduser("~/.adalflow/databases")
    
    if not os.path.exists(db_dir):
        return []
    
    if repo_name:
        pattern = f"{db_dir}/{repo_name}.pkl"
    else:
        pattern = f"{db_dir}/*.pkl"
    
    return glob.glob(pattern)


def list_databases():
    """List all existing databases."""
    db_files = find_database_files()
    
    if not db_files:
        print("No databases found.")
        return
    
    print("\nExisting databases:")
    print("-" * 60)
    
    for db_file in db_files:
        path = Path(db_file)
        size = path.stat().st_size / (1024 * 1024)  # Convert to MB
        modified = datetime.fromtimestamp(path.stat().st_mtime)
        
        print(f"  • {path.name}")
        print(f"    Size: {size:.2f} MB")
        print(f"    Modified: {modified.strftime('%Y-%m-%d %H:%M:%S')}")
        print()


def backup_database(db_path):
    """Create a backup of the database before deletion."""
    backup_dir = os.path.expanduser("~/.adalflow/database_backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_name = Path(db_path).stem
    backup_path = f"{backup_dir}/{db_name}_{timestamp}.pkl"
    
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup created: {backup_path}")
        return True
    except Exception as e:
        print(f"⚠️  Failed to create backup: {e}")
        return False


def rebuild_database(repo_name=None, force=False, no_backup=False):
    """Remove database file(s) to force rebuild."""
    db_files = find_database_files(repo_name)
    
    if not db_files:
        if repo_name:
            print(f"No database found for repository: {repo_name}")
        else:
            print("No databases found to rebuild.")
        return 0
    
    print(f"\nFound {len(db_files)} database(s) to rebuild:")
    for db_file in db_files:
        print(f"  • {db_file}")
    
    if not force:
        response = input("\nAre you sure you want to delete these databases? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return 1
    
    success_count = 0
    fail_count = 0
    
    for db_file in db_files:
        print(f"\nProcessing: {Path(db_file).name}")
        
        # Create backup unless disabled
        if not no_backup:
            if not backup_database(db_file):
                if not force:
                    response = input("Continue without backup? (y/N): ")
                    if response.lower() != 'y':
                        print("Skipping this database.")
                        continue
        
        # Delete the database
        try:
            os.remove(db_file)
            print(f"✅ Deleted: {db_file}")
            success_count += 1
        except Exception as e:
            print(f"❌ Failed to delete {db_file}: {e}")
            fail_count += 1
    
    print("\n" + "=" * 60)
    print("DATABASE REBUILD SUMMARY")
    print("=" * 60)
    print(f"Successfully deleted: {success_count} database(s)")
    
    if fail_count > 0:
        print(f"Failed to delete: {fail_count} database(s)")
    
    if success_count > 0:
        print("\n✨ The database(s) will be automatically rebuilt with fresh")
        print("   embeddings when you next run the application.")
        print("\n   This will ensure:")
        print("   • No empty embeddings persist")
        print("   • All documents have valid 768-dimensional vectors")
        print("   • Proper error handling for failed embeddings")
    
    return 0 if fail_count == 0 else 1


def main():
    """Main function for database rebuild."""
    parser = argparse.ArgumentParser(
        description='Rebuild DeepWiki embedding database by forcing regeneration'
    )
    parser.add_argument(
        '--repo-name',
        type=str,
        help='Specific repository database to rebuild (e.g., "AsyncFuncAI_deepwiki-open")'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Skip confirmation prompts'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip creating backup before deletion'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all existing databases'
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_databases()
        return 0
    
    return rebuild_database(
        repo_name=args.repo_name,
        force=args.force,
        no_backup=args.no_backup
    )


if __name__ == "__main__":
    sys.exit(main())