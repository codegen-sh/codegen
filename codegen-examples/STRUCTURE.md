# Structuring Codegen Examples

This guide explains how to structure examples for the Codegen library. A well-structured example helps both humans and AI understand the code's purpose and how to use it effectively.

## Core Principles

1. **Single Responsibility**: Each example should demonstrate one clear use case
1. **Self-Contained**: Examples should work independently with minimal setup
1. **Clear Structure**: Follow a consistent file organization pattern
1. **Good Documentation**: Include README.md with clear explanations and examples

## Standard File Structure

```
example-name/
├── README.md        # Documentation and usage examples
├── run.py          # Main implementation
└── input_repo/    # (Optional) Sample code for transformation
```

## Code Organization in `run.py`

Your `run.py` should follow this structure, demonstrated well in the `generate_training_data` example:

1. **Imports at the top**

   ```python
   import codegen
   from codegen import Codebase
   from codegen.sdk.core import Function
   # ... other imports
   ```

1. **Utility functions with clear docstrings**

   ```python
   def hop_through_imports(imp: Import) -> Symbol | ExternalModule:
       """Finds the root symbol for an import"""
       # Implementation...
   ```

1. **Main Codegen function with decorator**

   ```python
   @codegen.function("your-function-name")
   def run(codebase: Codebase):
       """Clear docstring explaining what the function does.

       Include:
       1. Purpose of the function
       2. Key steps or transformations
       3. Expected output
       """
       # Implementation...
   ```

1. **Entry point at bottom**

   ```python
   if __name__ == "__main__":
       # Initialize codebase
       # Run transformation
       # Save/display results
   ```

## Working with Codebases

Prefer using public repositories for examples when possible. However, sometimes you need a specific code structure to demonstrate a concept clearly. Here's how to handle both cases:

```python
# Preferred: Use a well-known public repo that demonstrates the concept well
codebase = Codebase.from_repo("fastapi/fastapi")

# Alternative: Create a minimal example repo when you need specific code structure
# 1. Create an input_repo/ directory in your example
# 2. Add minimal code that clearly demonstrates the transformation
codebase = Codebase("./input_repo")
```

For example:

```
example-name/
├── README.md
├── run.py
└── input_repo/     # Your minimal example code
    ├── app.py
    └── utils.py
```

Choose between these approaches based on:

1. Can you find a public repo that clearly shows the concept?
1. Is the transformation specific enough that a custom example would be clearer?
1. Would a minimal example be more educational than a complex real-world one?

## Best Practices

1. **Function Decorator**

   - Always use `@codegen.function()` with a descriptive name
   - Name should match the example's purpose

1. **Utility Functions**

   - Break down complex logic into smaller, focused functions
   - Each utility should demonstrate one clear concept
   - Include type hints and docstrings

1. **Main Function**

   - Name it `run()` for consistency
   - Include comprehensive docstring explaining the transformation
   - Return meaningful data that can be used programmatically

1. **Entry Point**

   - Include a `__name__ == "__main__"` block
   - Show both initialization and execution
   - Add progress messages for better UX

1. **Error Handling**

   - Include appropriate error handling for common cases
   - Provide clear error messages

## Example Reference Implementation

The `generate_training_data` example demonstrates these principles well:

```python
# Focused utility function
def get_function_context(function) -> dict:
    """Get the implementation, dependencies, and usages of a function."""
    # Clear, focused implementation...


# Main transformation with decorator
@codegen.function("generate-training-data")
def run(codebase: Codebase):
    """Generate training data using a node2vec-like approach...

    This codemod:
    1. Finds all functions...
    2. For each function...
    3. Outputs structured JSON...
    """
    # Clear implementation with good structure...


# Clean entry point
if __name__ == "__main__":
    print("Initializing codebase...")
    codebase = Codebase.from_repo("fastapi/fastapi")
    run(codebase)
    # ... rest of execution
```

## Documentation Requirements

Every example should include:

1. **README.md**
   - Clear explanation of purpose
   - Explains key syntax and program function
   - Code examples showing the transformation (before/after)
   - If using `input_repo/`, explain its structure and contents
   - Output format (if applicable)
   - Setup and running instructions

## Testing Your Example

Before submitting:

1. Test with a fresh environment
1. Verify all dependencies are listed
1. Ensure the example runs with minimal setup
1. Check that documentation is clear and accurate

Remember: Your example might be used by both humans and AI to understand Codegen's capabilities. Clear structure and documentation help everyone use your code effectively.
