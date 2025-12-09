#!/usr/bin/env python3
"""Standalone script to find and remove empty object parameters from usePresenter calls.

This script searches for all usages of the usePresenter function in a codebase
and removes the second parameter when it's an empty object ({}).

Usage:
    python scripts/standalone/remove_empty_presenter_params.py [--dry-run]

Options:
    --dry-run    Only print the changes without modifying files
"""

import argparse
import os
import re
from pathlib import Path

# Regular expressions to match different forms of empty objects
EMPTY_OBJECT_PATTERNS = [
    r"\{\s*\}",  # {}
    r"\{\s*\/\*.*?\*\/\s*\}",  # { /* comment */ }
    r"\{\s*\/\/.*?\n\s*\}",  # { // comment \n }
]

# Combined pattern for any empty object
EMPTY_OBJECT_REGEX = "|".join(f"({pattern})" for pattern in EMPTY_OBJECT_PATTERNS)

# Pattern to match usePresenter calls with a second parameter
# This handles various forms of the function call
USE_PRESENTER_REGEX = re.compile(r"(usePresenter\s*\(\s*[^,)]+\s*,\s*)(" + EMPTY_OBJECT_REGEX + r")(\s*[,)])", re.MULTILINE | re.DOTALL)


def find_js_ts_files(root_dir: str) -> list[Path]:
    """Find all JavaScript and TypeScript files in the given directory."""
    extensions = [".js", ".jsx", ".ts", ".tsx"]
    files = []

    for ext in extensions:
        for path in Path(root_dir).rglob(f"*{ext}"):
            # Skip node_modules and other common directories to ignore
            if "node_modules" not in str(path) and ".git" not in str(path):
                files.append(path)

    return files


def process_file(file_path: Path, dry_run: bool = False) -> tuple[int, list[str]]:
    """Process a single file to find and modify usePresenter calls.

    Args:
        file_path: Path to the file to process
        dry_run: If True, don't modify the file, just report changes

    Returns:
        Tuple of (number of changes, list of changes)
    """
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Find all matches
    matches = list(USE_PRESENTER_REGEX.finditer(content))
    if not matches:
        return 0, []

    # Track changes
    changes = []
    new_content = content
    offset = 0

    for match in matches:
        # Extract the parts of the match
        before_obj = match.group(1)  # usePresenter(arg1,
        empty_obj = match.group(2)  # {}
        after_obj = match.group(3)  # ) or , arg3)

        # Determine the replacement
        if after_obj.strip() == ")":
            # If this is the last parameter, remove the comma and the empty object
            replacement = before_obj.rstrip(",") + after_obj
        else:
            # If there are more parameters, just remove the empty object
            replacement = before_obj + after_obj.lstrip(",")

        # Calculate positions with offset adjustment
        start = match.start() + offset
        end = match.end() + offset

        # Apply the replacement
        new_content = new_content[:start] + replacement + new_content[end:]

        # Update offset for future replacements
        offset += len(replacement) - (end - start)

        # Record the change
        line_num = content.count("\n", 0, match.start()) + 1
        changes.append(f"Line {line_num}: Removed empty object parameter")

    # Write changes if not in dry run mode
    if not dry_run and changes:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

    return len(changes), changes


def main():
    parser = argparse.ArgumentParser(description="Remove empty object parameters from usePresenter calls")
    parser.add_argument("--dry-run", action="store_true", help="Only print changes without modifying files")
    args = parser.parse_args()

    # Get the current directory as the root
    root_dir = os.getcwd()

    print(f"Searching for JavaScript and TypeScript files in {root_dir}...")
    files = find_js_ts_files(root_dir)
    print(f"Found {len(files)} files to process")

    total_changes = 0
    modified_files = 0

    for file_path in files:
        num_changes, changes = process_file(file_path, args.dry_run)
        if num_changes > 0:
            modified_files += 1
            rel_path = file_path.relative_to(root_dir)
            print(f"\nModified {rel_path} ({num_changes} changes):")
            for change in changes:
                print(f"  - {change}")

        total_changes += num_changes

    print(f"\nSummary: Modified {modified_files} files with {total_changes} changes")
    if args.dry_run:
        print("Note: This was a dry run. No files were actually modified.")


if __name__ == "__main__":
    main()
