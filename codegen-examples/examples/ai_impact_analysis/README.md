# AI Impact Analysis

This script analyzes a codebase to measure and report the impact of AI-generated code contributions. It provides detailed insights about AI vs human contributions, helping teams understand the role of AI in their development process.

## Features

- **Repository Analysis**: Automatically detects and analyzes git repositories:

  - Uses current directory if it's a git repo

  - Searches parent directories for a git repo

  - Falls back to cloning a specified repository if needed

  ```python
  # Basic repository setup
  repo_path = os.getcwd()
  repo_config = RepoConfig.from_repo_path(repo_path)
  repo_operator = RepoOperator(repo_config=repo_config)
  project = ProjectConfig.from_repo_operator(repo_operator=repo_operator, programming_language=ProgrammingLanguage.PYTHON)
  codebase = Codebase(projects=[project])
  ```

- **Comprehensive Statistics**:

  - Total number of commits and AI vs human contribution percentages
  - Files with significant AI contribution (>50%)
  - AI-touched symbols and their impact
  - Detailed contributor breakdown (human and AI contributors)

  ```python
  # Run the analysis
  ai_authors = ["github-actions[bot]", "dependabot[bot]"]
  results = analyze_ai_impact(codebase, ai_authors)

  # Access statistics
  stats = results["stats"]
  print(f"Total commits: {stats['total_commits']}")
  print(f"AI commits: {stats['ai_commits']} ({stats['ai_percentage']:.1f}%)")
  print(f"Files with >50% AI: {stats['ai_file_count']} of {stats['total_file_count']}")

  # View contributors
  for author, count in results["contributors"]:
      is_ai = any(ai_name in author for ai_name in ai_authors)
      print(f"{'🤖' if is_ai else '👤'} {author}: {count} commits")
  ```

- **High-Impact Code Detection**:

  - Identifies AI-written code that is heavily used by other parts of the codebase
  - Shows dependency relationships for AI-contributed code

  ```python
  # Access high-impact AI symbols
  for symbol in results["high_impact_symbols"]:
      print(f"Symbol: {symbol['name']} ({symbol['filepath']})")
      print(f"Used by {symbol['usage_count']} other symbols")
      print(f"Last edited by: {symbol['last_editor']}")

  # View top AI-contributed files
  for file_path, percentage in stats["top_ai_files"]:
      print(f"{file_path}: {percentage:.1f}% AI contribution")
  ```

- **Detailed Attribution**:

  - Maps symbols to git history
  - Tracks last editor and complete editor history for each symbol
  - Flags AI-authored symbols

  ```python
  # Get attribution information for a specific symbol
  symbol = codebase.get_symbol("path/to/file.py:MyClass.my_method")

  # Access attribution data
  print(f"Last editor: {symbol.last_editor}")
  print(f"Editor history: {symbol.editor_history}")
  print(f"AI authored: {symbol.is_ai_authored}")

  # Find all AI-authored symbols
  ai_symbols = [s for s in codebase.get_symbols() if s.is_ai_authored]
  for symbol in ai_symbols:
      print(f"AI symbol: {symbol.name}")
  ```

## Output

The script generates:

1. Console output with summary statistics
1. Detailed analysis in `ai_impact_analysis.json`
1. Attribution information added to codebase symbols

## Usage

```bash
python run.py
```

The script will automatically:

1. Initialize and analyze the codebase
1. Process git history
1. Generate attribution information
1. Output detailed statistics

You can also visualize the AI impact analysis results using a dashboard. For setup and usage instructions, please see the documentation in the `/dashboard` subdirectory.

## Symbol Attribution

After running the analysis, symbols in the codebase will have the following attribution information:

- `symbol.last_editor`: The last person who edited the symbol
- `symbol.editor_history`: List of all editors who have touched the symbol
- `symbol.is_ai_authored`: Boolean indicating if the symbol was authored by AI

## Learn More

- [Attributions](https://docs.codegen.com/tutorials/attributions)
- [Codegen Documentation](https://docs.codegen.com)

## Contributing

Feel free to submit issues and enhancement requests!
