# Github Checks

This application is a GitHub integration that analyzes import cycles in Python codebases. It automatically runs when a pull request is labeled and checks for potentially problematic import patterns in the modified codebase.

## Features

- Analyzes import relationships in Python codebases
- Detects circular import dependencies
- Identifies problematic cycles with mixed static and dynamic imports
- Automatically comments on pull requests with detailed analysis

## How It Works

1. The app creates a directed graph representing import relationships in the codebase

   ```python
   for imp in codebase.imports:
       if imp.from_file and imp.to_file:
           G.add_edge(
               imp.to_file.filepath,
               imp.from_file.filepath,
               color="red" if getattr(imp, "is_dynamic", False) else "black",
               label="dynamic" if getattr(imp, "is_dynamic", False) else "static",
               is_dynamic=getattr(imp, "is_dynamic", False),
           )
   ```

1. It identifies strongly connected components (cycles) in the import graph

   ```python
   cycles = [scc for scc in nx.strongly_connected_components(G) if len(scc) > 1]
   ```

1. It specifically flags cycles that contain both static and dynamic imports

   ```python
   dynamic_count = sum(1 for e in edges.values() if e["color"] == "red")
       static_count = sum(1 for e in edges.values() if e["color"] == "black")

       if dynamic_count > 0 and static_count > 0:
           mixed_imports[(from_file, to_file)] = {
               "dynamic": dynamic_count,
               "static": static_count,
               "edges": edges,
           }
   ```

1. Results are posted as a comment on the pull request

   ```python
    if problematic_loops:
       message.append("\n### ⚠️ Problematic Import Cycles")
       message.append("(Cycles with mixed static and dynamic imports)")
       for i, cycle in enumerate(problematic_loops, 1):
           message.append(f"\n#### Problematic Cycle #{i}")
           message.append("Mixed imports:")
           for (from_file, to_file), imports in cycle["mixed_imports"].items():
               message.append(f"\nFrom: `{from_file}`")
               message.append(f"To: `{to_file}`")
               message.append(f"- Static imports: {imports['static']}")
               message.append(f"- Dynamic imports: {imports['dynamic']}")

   create_pr_comment(codebase, event.pull_request, number, "\n".join(message))
   ```

## Setup

1. Ensure you have the following dependencies:

   - Python 3.13
   - Modal
   - Codegen
   - NetworkX
   - python-dotenv

1. Set up your environment variables in a `.env` file

   - `GITHUB_TOKEN`: Your GitHub token, configured with `repo` and `workflow` scopes

1. Deploy the app using Modal:

   ```bash
   modal deploy app.py
   ```

## Technical Details

The application uses Codegen to parse the codebase and a combination of NetworkX and Codegen to analyze the import relationships. The app is structured as a Modal App with a FastAPI server.
The analysis runs when a pull request is labeled (`pull_request:labeled` event).

## Output Format

The analysis results are posted as a markdown-formatted comment on the pull request, including:

- Summary statistics
- Detailed cycle information
- Warning indicators for problematic import patterns

## Learn More

- [Codegen Documentation](https://docs.codegen.com)
- [Detecting Import Loops](https://docs.codegen.com/blog/fixing-import-loops)

## Contributing

Feel free to submit issues and enhancement requests!
