# Delete Dead Code

This example demonstrates how to identify and remove dead code from a codebase using Codegen. The script efficiently cleans up unused functions and variables, helping maintain a lean and efficient codebase.

> [!NOTE]
> Dead code refers to code that is not being used or referenced anywhere in your codebase. However, some code might appear unused but should not be deleted, such as test files, functions with decorators, public API endpoints, and event handlers.

## How the Dead Code Removal Script Works

The script (`run.py`) performs the dead code removal in several key steps:

1. **Codebase Loading**

   ```python
   codebase = Codebase.from_repo("tox-dev/tox", language="python")
   ```

   - Loads a codebase using the `Codebase.from_repo` method
   - This example uses the `tox-dev/tox` repository because it is mostly self-contained

1. **Function Removal**

   ```python
   for function in codebase.functions:
       if "test" in function.file.filepath:
           continue
       if function.decorators:
           continue
       if not function.usages and not function.call_sites:
           print(f"🗑️ Removing unused function: {function.name}")
           function.remove()
   ```

   - Skips test files and decorated functions
   - Removes functions with no usages or call sites

1. **Variable Cleanup**

   ```python
   for func in codebase.functions:
       for var_assignments in func.code_block.local_var_assignments:
           if not var_assignments.local_usages:
               print(f"🧹 Removing unused variable: {var_assignments.name}")
               var_assignments.remove()
   ```

   - Iterates through local variable assignments
   - Removes variables with no local usages

## Running the Script

```bash
# Install Codegen
pip install codegen

# Run the script
python run.py
```

## Example Output

```
� Deleting dead code...

🗑️ Removing unused function: _get_parser_doc
🧹 Removing unused variable: decoded
🧹 Removing unused variable: shebang_line
...
🧹 Removing unused variable: _

🔧 Total functions removed: 2
📦 Total variables removed: 240
```

## Learn More

- [Deleting Dead Code](https://docs.codegen.com/tutorials/deleting-dead-code)
- [Codegen Documentation](https://docs.codegen.com)

## Contributing

Feel free to submit issues and enhancement requests!
