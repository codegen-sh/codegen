# Remove Default Exports in TypeScript

This codemod demonstrates how to automatically convert default exports to named exports in your TypeScript codebase. The migration script makes this process simple by handling all the tedious manual updates automatically.

## How the Migration Script Works

The script automates the entire migration process in a few key steps:

1. **File Detection and Analysis**

   ```python
   codebase = Codebase("./")
   for file in codebase.files:
       if "/shared/" not in file.filepath:
           continue
   ```

   - Automatically identifies shared TypeScript files
   - Analyzes export structures
   - Determines necessary export modifications

1. **Export Conversion**

   ```python
   for export in file.exports:
       if export.is_default_export():
           export.make_non_default()
   ```

   - Converts default exports to named exports
   - Ensures corresponding non-shared files are updated
   - Preserves existing export configurations

## Common Migration Patterns

### Default Export Conversion

```typescript
// Before
export default function myFunction() {}

// After
export function myFunction() {}
```

### Re-export Conversion

```typescript
// Before
export { default } from './module';

// After
export { myFunction } from './module';
```

## Running the Migration

```bash
# Install Codegen
pip install codegen
# Run the migration
python run.py
```

## Learn More

- [TypeScript Documentation](https://www.typescriptlang.org/docs/)
- [Codegen Documentation](https://docs.codegen.com)

## Contributing

Feel free to submit issues and enhancement requests!
