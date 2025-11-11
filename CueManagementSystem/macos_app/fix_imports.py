#!/usr/bin/env python3
"""
Script to fix absolute imports in CuePi project for PyInstaller bundling.
This converts 'from CueManagementSystem.X import Y' to relative imports.
"""

import os
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """Fix imports in a single Python file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern to match: from CueManagementSystem.something import ...
    pattern = r'from CueManagementSystem\.([^\s]+) import'
    
    # Find all matches
    matches = re.findall(pattern, content)
    
    if not matches:
        return False, "No problematic imports found"
    
    # Replace each match
    for match in matches:
        old_import = f'from CueManagementSystem.{match} import'
        new_import = f'from {match} import'
        content = content.replace(old_import, new_import)
    
    # Write back if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True, f"Fixed {len(matches)} import(s)"
    
    return False, "No changes needed"

def find_and_fix_all_imports(root_dir):
    """Find and fix all Python files with problematic imports"""
    root_path = Path(root_dir)
    fixed_files = []
    
    print(f"Scanning directory: {root_dir}")
    print("-" * 80)
    
    # Find all Python files
    for py_file in root_path.rglob("*.py"):
        try:
            changed, message = fix_imports_in_file(py_file)
            if changed:
                fixed_files.append(str(py_file))
                print(f"✓ {py_file.relative_to(root_path)}: {message}")
        except Exception as e:
            print(f"✗ {py_file.relative_to(root_path)}: Error - {e}")
    
    print("-" * 80)
    print(f"\nTotal files fixed: {len(fixed_files)}")
    
    if fixed_files:
        print("\nFixed files:")
        for f in fixed_files:
            print(f"  - {f}")
    
    return fixed_files

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        project_dir = sys.argv[1]
    else:
        # Default to current directory
        project_dir = "."
    
    print("CuePi Import Fixer")
    print("=" * 80)
    print(f"Target directory: {os.path.abspath(project_dir)}")
    print()
    
    fixed = find_and_fix_all_imports(project_dir)
    
    if fixed:
        print("\n✓ Import fixing complete!")
        print("\nNext steps:")
        print("1. Review the changes (use 'git diff' if using git)")
        print("2. Rebuild the app: ./build_macos_app.sh")
        print("3. Test the app: open /Applications/CuePi.app")
    else:
        print("\n✓ No imports needed fixing!")