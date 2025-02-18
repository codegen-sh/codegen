# Automated Function Documentation Generator

This example demonstrates how to use Codegen to automatically generate comprehensive docstrings for functions by analyzing their dependencies and usage patterns within a codebase.

## Overview

The script uses Codegen's symbol analysis capabilities to:

1. Identify functions without docstrings
1. Analyze their dependencies and usages up to N degrees deep
1. Generate contextually aware docstrings using AI

## Key Features

### Recursive Context Collection

The script recursively collects both dependencies and usages to provide comprehensive context for docstring generation:

```python
def get_extended_context(symbol: Symbol, degree: int) -> tuple[set[Symbol], set[Symbol]]:
    """Recursively collect dependencies and usages up to the specified degree."""
    dependencies = set()
    usages = set()

    if degree > 0:
        for dep in symbol.dependencies:
            if isinstance(dep, Import):
                dep = hop_through_imports(dep)
            if isinstance(dep, Symbol):
                dependencies.add(dep)
                # Recursively collect nested context
                dep_deps, dep_usages = get_extended_context(dep, degree - 1)
                dependencies.update(dep_deps)
                usages.update(dep_usages)
```

### Import Resolution

The script intelligently resolves imports to find the actual symbol definitions:

```python
def hop_through_imports(imp: Import) -> Symbol | ExternalModule:
    """Finds the root symbol for an import"""
    if isinstance(imp.imported_symbol, Import):
        return hop_through_imports(imp.imported_symbol)
    return imp.imported_symbol
```

## Running the Conversion

```bash
# Install Codegen
pip install codegen

# Run the conversion
python run.py
```

The script will:

- Process each function in the codebase
- Skip functions that already have docstrings
- Generate contextually aware docstrings for undocumented functions
- Commit changes incrementally for safe early termination

## Example Output

The script provides detailed progress information:

```
[1/150] Skipping my_function - already has docstring
[2/150] Generating docstring for process_data at src/utils.py
  ✓ Generated docstring
[3/150] Generating docstring for validate_input at src/validation.py
  ✗ Failed to generate docstring
```

## Features

- **Intelligent Context Collection**: Analyzes both dependencies and usages to understand function purpose
- **Import Resolution**: Follows import chains to find actual symbol definitions
- **Incremental Commits**: Saves progress after each function for safe interruption
- **Progress Tracking**: Detailed logging of processing status
- **Existing Docstring Preservation**: Skips functions that are already documented

## Use Cases

- Documenting legacy codebases
- Maintaining documentation standards in large projects
- Onboarding new team members with better code documentation
- Preparing codebases for public release

## Learn More

- [Creating Documentation](https://docs.codegen.com/tutorials/creating-documentation#creating-documentation)
- [Codegen Documentation](https://docs.codegen.com)

## Contributing

Feel free to submit issues and enhancement requests!
