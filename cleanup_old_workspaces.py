#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utility script to clean up old workspace directories.
Removes all workspace directories created during agent execution.
"""

import os
import sys
import shutil
import time

# Fix Unicode encoding on Windows
if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def cleanup_workspaces():
    """Remove all workspace directories and old workspace backups."""
    print("Cleaning up old workspace directories...")
    
    # Get current directory
    current_dir = os.getcwd()
    
    # Find all workspace directories
    workspace_dirs = []
    for item in os.listdir(current_dir):
        if item.startswith("workspace"):
            full_path = os.path.join(current_dir, item)
            if os.path.isdir(full_path):
                workspace_dirs.append(item)
    
    if not workspace_dirs:
        print("✅ No workspace directories found to clean")
        return
    
    print(f"📋 Found {len(workspace_dirs)} workspace directory(ies):")
    for ws_dir in sorted(workspace_dirs):
        print(f"   - {ws_dir}")
    
    # Remove each workspace directory
    cleaned = 0
    failed = 0
    
    for ws_dir in workspace_dirs:
        full_path = os.path.join(current_dir, ws_dir)
        try:
            # Try robust cleanup for Windows
            if sys.platform == "win32":
                for attempt in range(3):
                    try:
                        shutil.rmtree(full_path)
                        break
                    except (PermissionError, OSError):
                        if attempt < 2:
                            time.sleep(0.5)
                        else:
                            # Rename as last resort
                            timestamp = int(time.time())
                            backup_name = f"{ws_dir}_cleanup_{timestamp}"
                            os.rename(full_path, backup_name)
                            print(f"⚠️  Could not delete {ws_dir} - renamed to {backup_name}")
                            failed += 1
                            return
            else:
                shutil.rmtree(full_path)
            
            print(f"✅ Cleaned: {ws_dir}")
            cleaned += 1
        except Exception as e:
            print(f"❌ Failed to clean {ws_dir}: {e}")
            failed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 Cleanup Summary")
    print(f"{'='*60}")
    print(f"✅ Cleaned: {cleaned} directory(ies)")
    if failed > 0:
        print(f"❌ Failed: {failed} directory(ies)")
    print(f"{'='*60}\n")
    
    if failed == 0:
        print("✅ All workspaces cleaned successfully!")
    else:
        print("⚠️  Some workspaces could not be cleaned")

if __name__ == "__main__":
    cleanup_workspaces()

