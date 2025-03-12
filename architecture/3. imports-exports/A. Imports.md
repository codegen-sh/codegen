# Import Resolution

Import resolution follows AST construction in the code analysis pipeline. It identifies dependencies between modules and builds a graph of relationships across the codebase.

> NOTE: This is an actively evolving part of Codegen SDK, so some details here may be imcomplete, outdated, or incorrect.

## Purpose

The import resolution system serves these purposes:

1. **Dependency Tracking**: Maps relationships between files by resolving import statements.
1. **Symbol Resolution**: Connects imported symbols to their definitions.
1. **Module Graph Construction**: Builds a directed graph of module dependencies.
1. **(WIP) Cross-Language Support**: Provides implementations for different programming languages.

## Core Components

### ImportResolution Class

The `ImportResolution` class represents the outcome of resolving an import statement. It contains:

- The source file containing the imported symbol
- The specific symbol being imported (if applicable)
- Whether the import references an entire file/module

### Import Base Class

The `Import` class is the foundation for language-specific import implementations. It:

- Stores metadata about the import (module path, symbol name, alias)
- Provides the abstract `resolve_import()` method
- Adds symbol resolution edges to the codebase graph

### Language-Specific Implementations

#### Python Import Resolution

The `PyImport` class extends the base `Import` class with Python-specific logic:

- Handles relative imports
- Supports module imports, named imports, and wildcard imports
- Resolves imports using configurable resolution paths and `sys.path`
- Handles special cases like `__init__.py` files

#### TypeScript Import Resolution

The `TSImport` class implements TypeScript-specific resolution:

- Supports named imports, default imports, and namespace imports
- Handles type imports and dynamic imports
- Resolves imports using TSConfig path mappings
- Supports file extension resolution

## Implementation

After file and directory parse, we loop through all import nodes and perform `add_symbol_resolution_edge`. This then invokes the language-specific `resolve_import` method that converts the import statement into a resolvable `ImportResolution` object (or None if the import cannot be resolved). This import symbol and the `ImportResolution` object are then used to add a symbol resolution edge to the graph, where it can then be used in future steps to resolve symbols.

## Next Step

After import resolution, the system analyzes [Export Analysis](./B.%20Exports.md) and handles [TSConfig Support](./C.%20TSConfig.md) for TypeScript projects. This is followed by [Type Analysis](../4.%20type-analysis/A.%20Type%20Analysis.md).
