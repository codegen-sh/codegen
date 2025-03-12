# Code Statistics and Attributions

This example demonstrates how to use Codegen's attribution extension to analyze the impact of AI on your codebase. You'll learn how to identify which parts of your code were written by AI tools like GitHub Copilot, Devin, or other AI assistants.

## Overview

The attribution extension analyzes git history to:

1. Identify which symbols (functions, classes, etc.) were authored or modified by AI tools
2. Calculate the percentage of AI contributions in your codebase
3. Find high-impact AI-written code (code that many other parts depend on)
4. Track the evolution of AI contributions over time

## How It Works

This example:

1. Loads a codebase (either the current directory or a sample repository)
2. Runs the AI impact analysis to gather attribution data
3. Demonstrates how to access attribution information for symbols
4. Prints detailed information about the most used symbols, including:
   - Last editor
   - Editor history
   - Whether the symbol was authored by AI

## Running the Example

You can run this example with:

```bash
python symbol_attribution.py
```

The script will:
1. Initialize a codebase from the current directory (if it's a git repository) or use a sample repository
2. Run the AI impact analysis
3. Print attribution information for the most used symbols in the codebase

## Code Walkthrough

### Setting Up the Codebase

```python
# Use current directory if it's a git repository
if os.path.exists(".git"):
    print("Using current directory as repository...")
    repo_path = os.getcwd()
    repo_config = RepoConfig.from_repo_path(repo_path)
    repo_operator = RepoOperator(repo_config=repo_config)

    project = ProjectConfig.from_repo_operator(
        repo_operator=repo_operator, 
        programming_language=ProgrammingLanguage.PYTHON
    )
    codebase = Codebase(projects=[project])
else:
    # Use from_repo method for a well-known repository
    print("Using a sample repository...")
    codebase = Codebase.from_repo(
        repo_full_name="codegen-sh/codegen",
        language="python",
    )
```

### Running the Analysis

```python
# Run the AI impact analysis
run(codebase)
```

### Accessing Attribution Information

```python
# Define which authors are considered AI
ai_authors = ["devin[bot]", "codegen[bot]", "github-actions[bot]"]
add_attribution_to_symbols(codebase, ai_authors)

# Access attribution information on symbols
for symbol in codebase.symbols:
    if hasattr(symbol, 'last_editor'):
        print(f"Last editor: {symbol.last_editor}")
    
    if hasattr(symbol, 'editor_history'):
        print(f"Editor history: {symbol.editor_history}")
    
    if hasattr(symbol, 'is_ai_authored'):
        print(f"AI authored: {'Yes' if symbol.is_ai_authored else 'No'}")
```

## Key Insights

By running this example, you can:

- Identify which parts of your codebase were authored by AI
- Track the adoption of AI coding assistants in your team
- Identify areas where AI is most effective
- Ensure appropriate review of AI-generated code
- Measure the impact of AI on developer productivity

## Further Reading

For more advanced usage, check out the [API reference](https://docs.codegen.sh/api-reference/extensions/attribution) for the attribution extension.