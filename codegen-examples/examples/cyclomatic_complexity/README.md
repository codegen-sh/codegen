# Cyclomatic Complexity Analyzer

This example demonstrates how to analyze the cyclomatic complexity of Python codebases using Codegen. The script provides detailed insights into code complexity by analyzing control flow structures and providing a comprehensive report.

> [!NOTE]
> The cyclomatic complexity metric helps identify complex code that might need refactoring. A higher score indicates more complex code with multiple decision points.

## How the Analysis Script Works

The script (`run.py`) performs the complexity analysis in several key steps:

1. **Codebase Loading**

   ```python
   codebase = Codebase.from_repo("fastapi/fastapi")
   ```

   - Loads any Python codebase into Codegen's analysis engine
   - Works with local or remote Git repositories
   - Supports analyzing specific commits

1. **Complexity Calculation**

   ```python
   def calculate_cyclomatic_complexity(code_block):
       complexity = 1  # Base complexity
       for statement in code_block.statements:
           if isinstance(statement, IfBlockStatement):
               complexity += 1 + len(statement.elif_statements)
   ```

   - Analyzes control flow structures (if/elif/else, loops, try/except)
   - Calculates complexity based on decision points
   - Handles nested structures appropriately

1. **Function Analysis**

   ```python
   callables = codebase.functions + [m for c in codebase.classes for m in c.methods]
   for function in callables:
       complexity = calculate_cyclomatic_complexity(function.code_block)
   ```

   - Processes both standalone functions and class methods
   - Calculates complexity for each callable
   - Tracks file locations and function names

1. **Report Generation**

   ```python
   print("\n📊 Cyclomatic Complexity Analysis")
   print(f"  • Total Functions: {total_functions}")
   print(f"  • Average Complexity: {average:.2f}")
   ```

   - Provides comprehensive complexity statistics
   - Shows distribution of complexity across functions
   - Identifies the most complex functions

## Output

```
📊 Cyclomatic Complexity Analysis
============================================================

📈 Overall Stats:
  • Total Functions: 3538
  • Average Complexity: 1.27
  • Total Complexity: 4478

🔍 Top 10 Most Complex Functions:
------------------------------------------------------------
  • jsonable_encoder                16 | fastapi/encoders.py
  • get_openapi                     13 | fastapi/openapi/utils.py
  • __init__                        12 | fastapi/routing.py
  • solve_dependencies              10 | fastapi/dependencies/utils.py
  • main                             9 | scripts/notify_translations.py
  • analyze_param                    9 | fastapi/dependencies/utils.py
  • __init__                         8 | fastapi/params.py
  • __init__                         8 | fastapi/params.py
  • main                             7 | scripts/deploy_docs_status.py
  • create_model_field               7 | fastapi/utils.py

📉 Complexity Distribution:
  • Low (1-5): 3514 functions (99.3%)
  • Medium (6-10): 21 functions (0.6%)
  • High (>10): 3 functions (0.1%)
```

## Complexity Metrics

The analyzer tracks several key metrics:

### Complexity Sources

- If statements (+1)
- Elif statements (+1 each)
- Else statements (+1)
- Loops (while/for) (+1)
- Try-except blocks (+1 per except)

### Complexity Categories

- Low (1-5): Generally clean and maintainable code
- Medium (6-10): Moderate complexity, may need attention
- High (>10): Complex code that should be reviewed

## Running the Analysis

```bash
# Install Codegen
pip install codegen

# Run the analysis
python run.py
```

## Example Output

```
📊 Cyclomatic Complexity Analysis
============================================================

📈 Overall Stats:
  • Total Functions: 150
  • Average Complexity: 3.45
  • Total Complexity: 518

🔍 Top 10 Most Complex Functions:
------------------------------------------------------------
  • validate_response               12 | ...api/endpoints/auth.py
  • process_request                 10 | ...core/middleware.py
  • handle_exception                 9 | ...utils/error_handlers.py

📉 Complexity Distribution:
  • Low (1-5): 105 functions (70.0%)
  • Medium (6-10): 35 functions (23.3%)
  • High (>10): 10 functions (6.7%)
```

## Learn More

- [About Cyclomatic Complexity](https://en.wikipedia.org/wiki/Cyclomatic_complexity)
- [Codegen Documentation](https://docs.codegen.com)

## Contributing

Feel free to submit issues and enhancement requests!
