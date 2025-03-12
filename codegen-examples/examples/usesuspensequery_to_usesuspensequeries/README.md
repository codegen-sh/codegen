# Transform useSuspenseQuery to useSuspenseQueries

This example demonstrates how to use Codegen to automatically convert multiple `useSuspenseQuery` calls to a single `useSuspenseQueries` call in React codebases. The migration script makes this process simple by handling all the tedious manual updates automatically.

> [!NOTE]
> View example transformations created by this codemod on the `deepfence/ThreatMapper` repository [here](codegen.sh/codemod/a433152e-5e8d-4319-8043-19ff2b418869/public/diff).

## How the Migration Script Works

The script automates the entire migration process in a few key steps:

1. **File Detection**

   ```python
   for file in codebase.files:
       if "useSuspenseQuery" not in file.source:
           continue
   ```

   - Automatically identifies files using `useSuspenseQuery`
   - Skips irrelevant files to avoid unnecessary processing
   - Uses Codegen's intelligent code analysis engine

1. **Import Management**

   ```python
   import_str = "import { useQuery, useSuspenseQueries } from '@tanstack/react-query'"
   file.add_import(import_str)
   ```

   - Uses Codegen's import analysis to add required imports
   - Preserves existing import structure
   - Handles import deduplication automatically

1. **Query Transformation**

   ```python
   # Convert multiple queries to single useSuspenseQueries call
   new_query = f"const [{', '.join(results)}] = useSuspenseQueries({{queries: [{', '.join(queries)}]}})"
   ```

   - Collects multiple `useSuspenseQuery` calls
   - Combines them into a single `useSuspenseQueries` call
   - Maintains variable naming and query configurations

## Why This Makes Migration Easy

1. **Zero Manual Updates**

   - Codegen SDK handles all the file searching and updating
   - No tedious copy-paste work

1. **Consistent Changes**

   - Ensures all transformations follow the same patterns
   - Maintains code style consistency

1. **Safe Transformations**

   - Validates changes before applying them
   - Easy to review and revert if needed

## Common Migration Patterns

### Multiple Query Calls

```typescript
// Before
const result1 = useSuspenseQuery(queryConfig1)
const result2 = useSuspenseQuery(queryConfig2)
const result3 = useSuspenseQuery(queryConfig3)

// Automatically converted to:
const [result1, result2, result3] = useSuspenseQueries({
  queries: [queryConfig1, queryConfig2, queryConfig3]
})
```

## Key Benefits to Note

1. **Reduced Re-renders**

   - Single query call instead of multiple separate calls
   - Better React performance

1. **Improved Code Readability**

   - Cleaner, more consolidated query logic
   - Easier to maintain and understand

1. **Network Optimization**

   - Batched query requests
   - Better resource utilization

## Running the Migration

```bash
# Install Codegen
pip install codegen

# Run the migration
python run.py
```

The script will:

1. Initialize the codebase
1. Find files containing `useSuspenseQuery`
1. Apply the transformations
1. Print detailed progress information

## Learn More

- [React Query Documentation](https://tanstack.com/query/latest)
- [useSuspenseQueries API](https://tanstack.com/query/latest/docs/react/reference/useSuspenseQueries)
- [Codegen Documentation](https://docs.codegen.com)

## Contributing

Feel free to submit issues and any enhancement requests!
