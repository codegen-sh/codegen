import json
from pathlib import Path
from typing import Any

DEFAULT_CELLS = [
    {
        "cell_type": "code",
        "source": """from codegen.sdk.core.codebase import Codebase

# Initialize codebase
codebase = Codebase('../../')

# Print out stats
print("🔍 Codebase Analysis")
print("=" * 50)
print(f"📚 Total Files: {len(codebase.files)}")
print(f"⚡ Total Functions: {len(codebase.functions)}")
print(f"🔄 Total Imports: {len(codebase.imports)}")""".strip(),
    }
]

DEMO_CELLS = [
    ##### [ CODEGEN DEMO ] #####
    {
        "cell_type": "markdown",
        "source": """# Graph-sitter Demo: FastAPI

Welcome to [Codegen](https://graph-sitter.com)!

This demo notebook will walk you through some features of Graph-sitter applied to [FastAPI](https://github.com/fastapi/fastapi).

See the [getting started](https://graph-sitter.com/introduction/getting-started) guide to learn more.""".strip(),
    },
    {
        "cell_type": "code",
        "source": """from codegen.sdk.core.codebase import Codebase

# Initialize FastAPI codebase
print('Cloning and parsing FastAPI to /tmp/codegen/fastapi...')
codebase = Codebase.from_repo('fastapi/fastapi', commit="eab0653a346196bff6928710410890a300aee4ae")

# To initialize a local codebase, use this constructor
# codebase = Codebase("path/to/git/repo")""".strip(),
    },
    ##### [ CODEBASE ANALYSIS ] #####
    {
        "cell_type": "markdown",
        "source": """# Codebase Analysis

Let's do a quick codebase analysis!

- Grab codebase content with [codebase.functions](https://graph-sitter.com/building-with-graph-sitter/symbol-api) et al.
- View inheritance hierarchies with [inhertance APIs](https://graph-sitter.com/building-with-graph-sitter/class-api#working-with-inheritance)
- Identify recursive functions by looking at [FunctionCalls](https://graph-sitter.com/building-with-graph-sitter/function-calls-and-callsites)""".strip(),
    },
    {
        "cell_type": "code",
        "source": """# Print overall stats
print("🔍 FastAPI Analysis")
print("=" * 50)
print(f"📚 Total Classes: {len(codebase.classes)}")
print(f"⚡ Total Functions: {len(codebase.functions)}")
print(f"🔄 Total Imports: {len(codebase.imports)}")

# Find class with most inheritance
if codebase.classes:
    deepest_class = max(codebase.classes, key=lambda x: len(x.superclasses))
    print(f"\\n🌳 Class with most inheritance: {deepest_class.name}")
    print(f"   📊 Chain Depth: {len(deepest_class.superclasses)}")
    print(f"   ⛓️ Chain: {' -> '.join(s.name for s in deepest_class.superclasses)}")

# Find first 5 recursive functions
recursive = [f for f in codebase.functions
            if any(call.name == f.name for call in f.function_calls)][:5]
if recursive:
    print(f"\\n🔄 Recursive functions:")
    for func in recursive:
        print(f"  - {func.name} ({func.file.filepath})")""".strip(),
    },
    ##### [ TEST DRILL DOWN ] #####
    {
        "cell_type": "markdown",
        "source": """# Drilling Down on Tests

Let's specifically drill into large test files, which can be cumbersome to manage:""".strip(),
    },
    {
        "cell_type": "code",
        "source": """from collections import Counter

# Filter to all test functions and classes
test_functions = [x for x in codebase.functions if x.name.startswith('test_')]

print("🧪 Test Analysis")
print("=" * 50)
print(f"📝 Total Test Functions: {len(test_functions)}")
print(f"📊 Tests per File: {len(test_functions) / len(codebase.files):.1f}")

# Find files with the most tests
print("\\n📚 Top Test Files by Count")
print("-" * 50)
file_test_counts = Counter([x.file for x in test_functions])
for file, num_tests in file_test_counts.most_common()[:5]:
    print(f"🔍 {num_tests} test functions: {file.filepath}")
    print(f"   📏 File Length: {len(file.source.split('\\n'))} lines")
    print(f"   💡 Functions: {len(file.functions)}")""".strip(),
    },
    ##### [ TEST SPLITTING ] #####
    {
        "cell_type": "markdown",
        "source": """# Splitting Up Large Test Files

Lets split up the largest test files into separate modules for better organization.

This uses Codegen's [codebase.move_to_file(...)](https://graph-sitter.com/building-with-graph-sitter/moving-symbols), which will:
- update all imports
- (optionally) move depenencies
- do so very fast ⚡️

While maintaining correctness.""",
    },
    ##### [ TEST SPLITTING ] #####
    {
        "cell_type": "code",
        "source": """filename = 'tests/test_path.py'
print(f"📦 Splitting Test File: {filename}")
print("=" * 50)

# Grab a file
file = codebase.get_file(filename)
base_name = filename.replace('.py', '')

# Group tests by subpath
test_groups = {}
for test_function in file.functions:
    if test_function.name.startswith('test_'):
        test_subpath = '_'.join(test_function.name.split('_')[:3])
        if test_subpath not in test_groups:
            test_groups[test_subpath] = []
        test_groups[test_subpath].append(test_function)

# Print and process each group
for subpath, tests in test_groups.items():
    print(f"\\n{subpath}/")
    new_filename = f"{base_name}/{subpath}.py"

    # Create file if it doesn't exist
    if not codebase.has_file(new_filename):
        new_file = codebase.create_file(new_filename)
    file = codebase.get_file(new_filename)

    # Move each test in the group
    for test_function in tests:
        print(f"    - {test_function.name}")
        test_function.move_to_file(new_file, strategy="add_back_edge")

# Commit changes to disk
codebase.commit()""".strip(),
    },
    ##### [ RESET ] #####
    {
        "cell_type": "markdown",
        "source": """## View Changes

You can now view changes by `cd /tmp/codegen/fastapi && git diff`

Enjoy!

# Reset

Reset your codebase to it's initial state, discarding all changes

Learn more in [commit and reset](https://graph-sitter.com/building-with-graph-sitter/commit-and-reset).""".strip(),
    },
    {
        "cell_type": "code",
        "source": """codebase.reset()""".strip(),
    },
]


def create_cells(cells_data: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Convert cell data into Jupyter notebook cell format."""
    return [
        {
            "cell_type": cell["cell_type"],
            "source": cell["source"],
            "metadata": {},
            "execution_count": None,
            "outputs": [] if cell["cell_type"] == "code" else None,
        }
        for cell in cells_data
    ]


def create_notebook(jupyter_dir: Path, demo: bool = False) -> Path:
    """Create a new Jupyter notebook if it doesn't exist.

    Args:
        jupyter_dir: Directory where the notebook should be created
        demo: Whether to create a demo notebook with FastAPI example code

    Returns:
        Path to the created or existing notebook
    """
    notebook_path = jupyter_dir / ("demo.ipynb" if demo else "tmp.ipynb")
    if not notebook_path.exists():
        cells = create_cells(DEMO_CELLS if demo else DEFAULT_CELLS)
        notebook_content = {
            "cells": cells,
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
            "nbformat": 4,
            "nbformat_minor": 4,
        }
        notebook_path.write_text(json.dumps(notebook_content, indent=2))
    return notebook_path
