# Export Analysis

Some languages contain additional metadata on "exported" symbols, specifying which symbols are made available to other modules. Export analysis follows import resolution in the code analysis pipeline. It identifies and processes exported symbols from modules, enabling the system to track what each module makes available to others.

## Core Components

### Export Base Class

The `Export` class serves as the foundation for language-specific export implementations. It:

- Stores metadata about the export (symbol name, is default, etc.)
- Tracks the relationship between the export and its declared symbol
- Adds export edges to the codebase graph

### TypeScript Export Implementation

The `TSExport` class implements TypeScript-specific export handling:

- Supports various export styles (named exports, default exports, re-exports)
- Handles export declarations with and without values
- Processes wildcard exports (`export * from 'module'`)
- Manages export statements with multiple exports

#### Export Types and Symbol Resolution

The TypeScript implementation handles several types of exports:

1. **Declaration Exports**

   - Function declarations (including generators)
   - Class declarations
   - Interface declarations
   - Type alias declarations
   - Enum declarations
   - Namespace declarations
   - Variable/constant declarations

1. **Value Exports**

   - Object literals with property exports
   - Arrow functions and function expressions
   - Classes and class expressions
   - Assignment expressions
   - Primitive values and expressions

1. **Special Export Forms**

   - Wildcard exports (`export * from 'module'`)
   - Named re-exports (`export { name as alias } from 'module'`)
   - Default exports with various value types

#### Symbol Tracking and Dependencies

The export system:

- Maintains relationships between exported symbols and their declarations
- Validates export names match their declared symbols
- Tracks dependencies through the codebase graph
- Handles complex scenarios like:
  - Shorthand property exports in objects
  - Nested function and class declarations
  - Re-exports from other modules

#### Integration with Type System

Exports are tightly integrated with the type system:

- Exported type declarations are properly tracked
- Symbol resolution considers both value and type exports
- Re-exports preserve type information
- Export edges in the codebase graph maintain type relationships

## Next Step

After export analysis is complete, for TypeScript projects, the system processes [TSConfig Support](./C.%20TSConfig.md) configurations. Then it moves on to [Type Analysis](../4.%20type-analysis/A.%20Type%20Analysis.md) to build a complete understanding of types and symbols.
