# Transform Module Re-exports Organization

This example demonstrates how to use Codegen to automatically analyze and reorganize TypeScript module re-exports through shared directories. The script makes this process simple by handling all the tedious manual updates automatically.

> [!NOTE]
> This codemod helps maintain clean module boundaries and improves code organization by centralizing shared exports.

## How the Migration Script Works

The script automates the entire reorganization process in a few key steps:

1. **Export Analysis**

   ```python
   for export_stmt in file.export_statements:
       for export in export_stmt.exports:
           if export.is_reexport() and not export.is_external_export:
               all_reexports.append(export)
   ```

   - Automatically identifies re-exports in shared directories
   - Analyzes export patterns and dependencies
   - Uses Codegen's intelligent code analysis engine

1. **Shared File Management**

   ```python
   resolved_public_file = export.resolved_symbol.filepath.replace("src/", "src/shared/")
   if not codebase.has_file(resolved_public_file):
       target_file = codebase.create_file(resolved_public_file, sync=True)
   ```

   - Creates or updates shared export files
   - Maintains proper file structure
   - Handles path resolution automatically

1. **Import Updates**

   ```python
   # Updates imports to use new shared paths
   new_path = usage.file.ts_config.translate_import_path(resolved_public_file)
   new_import = f'import {{ {name} }} from "{new_path}"'
   ```

   - Updates all import statements to use new paths
   - Maintains proper TypeScript path resolution
   - Handles different import types (normal, type)

## Why This Makes Organization Easy

1. **Zero Manual Updates**

   - Codegen SDK handles all file creation and updates
   - No tedious export management

1. **Consistent Structure**

   - Ensures all shared exports follow the same pattern
   - Maintains clean module boundaries

1. **Safe Transformations**

   - Validates changes before applying them
   - Preserves existing functionality

## Common Re-export Patterns

### Module to Shared Exports

```typescript
// Before: Direct module import
import { validateEmail } from '../module_a/src/functions';

// After: Import through shared
import { validateEmail } from '../module_a/src/shared';
```

### Export Consolidation

```typescript
// Before: Multiple export files
export { foo } from './foo';
export { bar } from './bar';

// After: Consolidated in shared
export * from '../functions';
```

## Key Benefits to Note

1. **Better Module Boundaries**

   - Clear public API for each module
   - Centralized shared functionality

1. **Improved Maintainability**

   - Easier to track dependencies
   - Simplified import paths

1. **Code Organization**

   - Consistent export structure
   - Reduced import complexity

The script will:

1. 🎯 Start the reexport organization
1. 📁 Analyze shared directories
1. 🔄 Process and update exports
1. ✨ Create shared export files
1. 🧹 Clean up redundant exports

## Learn More

- [TypeScript Modules](https://www.typescriptlang.org/docs/handbook/modules.html)
- [Export/Import Documentation](https://www.typescriptlang.org/docs/handbook/modules.html#export)
- [Codegen Documentation](https://docs.codegen.com)
- [Tutorial on Analyzing and Organizing Re-exports](https://docs.codegen.com/tutorials/managing-typescript-exports)
- [More on exports ](https://docs.codegen.com/building-with-codegen/exports)

## Contributing

Feel free to submit issues and enhancement requests!
