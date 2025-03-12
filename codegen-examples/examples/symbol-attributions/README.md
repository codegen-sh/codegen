# Symbol Attributions

This example demonstrates how to analyze and track attribution information for symbols in a codebase, including identifying AI vs human contributions and tracking edit history.

## What it does

This script performs several key functions:

1. **Codebase Analysis**
   - Loads and parses all Python files in the repository
   - Builds a dependency graph of symbols (classes, functions, etc.)
   - Analyzes import relationships and dependencies

```python
  from codegen import Codebase

  # Initialize codebase object from directory
  codebase = Codebase.from_repo("your-org/your-repo", language="python")
```

2. **AI Impact Analysis**
   - Identifies commits made by AI bots vs human contributors
   - Calculates statistics on AI contributions:
     - Percentage of AI commits
     - Files with significant AI contribution
     - Number of AI-touched symbols
   - Identifies high-impact AI-written code

```python
  ai_authors = ["devin[bot]", "codegen[bot]", "github-actions[bot]"]
  add_attribution_to_symbols(codebase, ai_authors)
```

3. **Symbol Attribution**
   - Tracks edit history for each symbol in the codebase
   - Records:
     - Last editor of each symbol
     - Complete editor history
     - Whether the symbol was AI-authored
   - Provides detailed attribution for most-used symbols

```python
  symbols_with_usages = []
  for symbol in codebase.symbols:
      if hasattr(symbol, "usages") and len(symbol.usages) > 0:
          symbols_with_usages.append((symbol, len(symbol.usages)))
```

## Example Output

The script provides detailed analytics including:

- Repository statistics (files, symbols, contributors)
- AI contribution summary (% of commits, impacted files)
- Top contributors list
- Detailed attribution for most-used symbols, showing:
  - Symbol name and type
  - File location
  - Usage count
  - Last editor
  - Editor history
  - AI authorship status

## Usage

Run the script in your repository:

```bash
python run.py
```

The script will automatically:

- Use the current directory if it's a git repository
- Fall back to a sample repository if not in a git repo
- Generate comprehensive attribution analysis
- Save detailed results to `ai_impact_analysis.json`

## Requirements

- A Git repository
- Python codebase
- `codegen` installed

## Learn More

- [Codegen Symbols](https://docs.codegen.com/api-reference/core/Symbol#symbol)
- [Codegen Documentation](https://docs.codegen.com)

## Contributing

Feel free to submit issues and enhancement requests!
