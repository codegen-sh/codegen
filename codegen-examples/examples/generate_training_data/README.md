# Generate Codebase Pre-Training Data

[![Documentation](https://img.shields.io/badge/docs-docs.codegen.com-blue)](https://docs.codegen.com/tutorials/generate-training-data)

This example demonstrates how to use Codegen to generate training data for large-scale LLM pre-training by extracting function implementations along with their dependencies and usages. The approach is inspired by node2vec, leveraging code graphs for learning.

## What This Example Does

The script analyzes your codebase and generates training data by:

1. **Finding All Functions**

   - Scans the entire codebase to identify function definitions
   - Filters out trivial functions (less than 2 lines)

1. **Capturing Implementation Context**

   ```python
   {"implementation": {"source": "def process_data():\n    ...", "filepath": "src/process.py"}}
   ```

1. **Extracting Dependencies**

   ```python
   {"dependencies": [{"source": "def helper_function():\n    ...", "filepath": "src/helpers.py"}]}
   ```

1. **Recording Usages**

   ```python
   {"usages": [{"source": "result = process_data()", "filepath": "src/main.py"}]}
   ```

## Running the Example

```bash
# Install Codegen
pip install codegen

# Run the data generation
python run.py
```

The script will analyze your codebase and output a `training_data.json` file containing the structured training data.

## Understanding the Code

- `run.py` - The main script that generates the training data
  - Uses `get_function_context()` to extract implementation, dependencies, and usages
  - Processes each function and builds a comprehensive context graph
  - Outputs structured JSON data with metadata about the processing

## Output Format

The generated `training_data.json` follows this structure:

```json
{
  "functions": [
    {
      "implementation": {
        "source": "...",
        "filepath": "..."
      },
      "dependencies": [
        {
          "source": "...",
          "filepath": "..."
        }
      ],
      "usages": [
        {
          "source": "...",
          "filepath": "..."
        }
      ]
    }
  ],
  "metadata": {
    "total_functions": 100,
    "total_processed": 85,
    "avg_dependencies": 2.5,
    "avg_usages": 3.2
  }
}
```

## Learn More

- [Full Tutorial](https://docs.codegen.com/tutorials/generate-training-data)
- [Code Model Pre-training](https://docs.codegen.com/concepts/code-model-training)
- [Codegen Documentation](https://docs.codegen.com)
