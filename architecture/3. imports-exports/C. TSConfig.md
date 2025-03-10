# TSConfig Support

TSConfig support is a critical component for TypeScript projects in the import resolution system. It processes TypeScript configuration files (tsconfig.json) to correctly resolve module paths and dependencies.

## Purpose

The TSConfig support system serves these purposes:

1. **Path Mapping**: Resolves custom module path aliases defined in the tsconfig.json file.
1. **Base URL Resolution**: Handles non-relative module imports using the baseUrl configuration.
1. **Project References**: Manages dependencies between TypeScript projects using the references field.
1. **Directory Structure**: Respects rootDir and outDir settings for maintaining proper directory structures.

## Core Components

### TSConfig Class

The `TSConfig` class represents a parsed TypeScript configuration file. It:

- Parses and stores the configuration settings from tsconfig.json
- Handles inheritance through the "extends" field
- Provides methods for translating between import paths and absolute file paths
- Caches computed values for performance optimization

## Configuration Processing

### Configuration Inheritance

TSConfig files can extend other configuration files through the "extends" field:

1. Base configurations are loaded and parsed first
1. Child configurations inherit and can override settings from their parent
1. Path mappings, base URLs, and other settings are merged appropriately

### Path Mapping Resolution

The system processes the "paths" field in tsconfig.json to create a mapping between import aliases and file paths:

1. Path patterns are normalized (removing wildcards, trailing slashes)
1. Relative paths are converted to absolute paths
1. Mappings are stored for efficient lookup during import resolution

### Project References

The "references" field defines dependencies between TypeScript projects:

1. Referenced projects are identified and loaded
1. Their configurations are analyzed to determine import paths
1. Import resolution can cross project boundaries using these references

## Import Resolution Process

### Path Translation

When resolving an import path in TypeScript:

1. Check if the path matches any path alias in the tsconfig.json
1. If a match is found, translate the path according to the mapping
1. Apply baseUrl resolution for non-relative imports
1. Handle project references for cross-project imports

### Optimization Techniques

The system employs several optimizations:

1. Caching computed values to avoid redundant processing
1. Early path checking for common patterns (e.g., paths starting with "@" or "~")
1. Hierarchical resolution that respects the configuration inheritance chain

## Integration with Import Resolution

The TSConfig support integrates with the broader import resolution system:

1. Each TypeScript file is associated with its nearest tsconfig.json
1. Import statements are processed using the file's associated configuration
1. Path mappings are applied during the module resolution process
1. Project references are considered when resolving imports across project boundaries

## Next Step

After TSConfig processing is complete, the system proceeds to [Type Analysis](../4.%20type-analysis/A.%20Type%20Analysis.md) where it builds a complete understanding of types, symbols, and their relationships.
