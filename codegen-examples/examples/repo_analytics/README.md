# Repository Analytics

This example demonstrates how to use Codegen to analyze repository metrics and generate comprehensive codebase analytics. For a complete walkthrough, check out our [tutorial](https://docs.codegen.com/tutorials/codebase-analytics-dashboard).

## How the Analytics Script Works

The script calculates four main categories of metrics:

1. **Line Metrics**

   ```python
   def count_lines(source: str):
       """Count different types of lines in source code."""
       lines = [line.strip() for line in source.splitlines()]
       loc = len(lines)
       sloc = len([line for line in lines if line])
       # ... additional line counting logic ...
       return loc, lloc, sloc, comments
   ```

   - Lines of Code (LOC): Total lines including blanks and comments
   - Logical Lines (LLOC): Lines containing functional statements
   - Source Lines (SLOC): Non-blank lines of code
   - Comment Density: Percentage of comments relative to total lines

1. **Cyclomatic Complexity**

   ```python
   def calculate_cyclomatic_complexity(function):
       def analyze_statement(statement):
           complexity = 0
           if isinstance(statement, IfBlockStatement):
               complexity += 1
               if hasattr(statement, "elif_statements"):
                   complexity += len(statement.elif_statements)
           # ... additional complexity calculations ...
           return complexity

       return 1 + analyze_block(function.code_block)
   ```

   - Measures number of code paths through the program
   - Higher values indicate more complex control flow
   - Helps identify functions that may need refactoring

1. **Halstead Volume**

   ```python
   def calculate_halstead_volume(operators, operands):
       n1 = len(set(operators))  # unique operators
       n2 = len(set(operands))  # unique operands
       N1 = len(operators)  # total operators
       N2 = len(operands)  # total operands
       N = N1 + N2
       n = n1 + n2
       # ... volume calculation ...
       return volume, N1, N2, n1, n2
   ```

   - Measures program size based on vocabulary and length
   - Uses distinct operators and operands to calculate volume
   - Indicates cognitive load and program understanding effort

1. **Depth of Inheritance**

   ```python
   def calculate_doi(cls):
       """Calculate the depth of inheritance for a given class."""
       return len(cls.superclasses)
   ```

   - Length of inheritance chain for classes

1. **Maintainability Index**

   ```python
   def calculate_maintainability_index(halstead_volume: float, cyclomatic_complexity: float, loc: int) -> int:
       """Calculate the normalized maintainability index for a given function."""
       raw_mi = 171 - 5.2 * math.log(max(1, halstead_volume)) - 0.23 * cyclomatic_complexity - 16.2 * math.log(max(1, loc))
       normalized_mi = max(0, min(100, raw_mi * 100 / 171))
       return int(normalized_mi)
   ```

   - Normalized score (0-100) based on complexity, volume, and size
   - Higher scores indicate better maintainability

## Running the Analysis

```bash
# Install Codegen
pip install codegen

# Run the analysis
python run.py
```

The script will output a detailed report including:

- Basic repository statistics
- Line metrics and comment density
- Complexity measurements
- Object-oriented metrics
- Overall maintainability scores

## Example Output

```
📊 Repository Analysis Report 📊
==================================================
📁 Repository: codegen-sh/codegen
📝 Description: [Repository description from GitHub]

📈 Basic Metrics:
  • Files: 42
  • Functions: 156
  • Classes: 23

📏 Line Metrics:
  • Lines of Code: 4,521
  • Logical Lines: 2,845
  • Source Lines: 3,892
  • Comments: 629
  • Comment Density: 13.9%

🔄 Complexity Metrics:
  • Average Cyclomatic Complexity: 3.2
  • Average Maintainability Index: 72
  • Average Depth of Inheritance: 1.4
  • Total Halstead Volume: 52,436
  • Average Halstead Volume: 336
```

## Learn More

- [Analytics Tutorial](https://docs.codegen.com/tutorials/codebase-analytics-dashboard)
- [Codegen Documentation](https://docs.codegen.com)

## Contributing

Feel free to submit issues and enhancement requests!
