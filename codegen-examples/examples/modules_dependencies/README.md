# Visualize Module Dependencies

This example demonstrates how to use Codegen to automatically analyze and visualize module dependencies in Python codebases. The script creates a directed graph showing relationships between different modules, making it easier to understand code architecture and dependencies.

> [!NOTE]
> This codemod helps developers understand module relationships by creating a visual representation of import dependencies between different parts of the codebase.

## How the Visualization Script Works

The script analyzes module dependencies in several key steps:

1. **Graph Initialization**

   ```python
   G = nx.DiGraph()
   list_apps = ["src/sentry/api", "src/sentry/auth", "src/sentry/flags"]
   for app in list_apps:
       G.add_node(app, metadata={"color": "red"})
   ```

   - Creates a directed graph using NetworkX
   - Initializes nodes for each major application module
   - Sets up metadata for visualization

1. **Import Analysis**

   ```python
   for file in codebase.files:
       if app in file.filepath:
           for import_statement in file.import_statements:
               # Analyze imports and build edges
   ```

   - Scans through all files in specified modules
   - Analyzes import statements
   - Creates edges based on module dependencies

1. **Graph Cleanup**

   ```python
   nodes_to_remove = [node for node, degree in G.degree() if degree == 1]
   G.remove_nodes_from(nodes_to_remove)
   ```

   - Removes isolated nodes
   - Cleans up the graph for better visualization
   - Focuses on meaningful dependencies

## Why This Makes Architecture Analysis Easy

1. **Automated Dependency Detection**

   - Automatically finds module relationships
   - Identifies import patterns
   - No manual tracking needed

1. **Visual Representation**

   - Clear visualization of dependencies
   - Easy to identify clusters
   - Highlights potential architectural issues

1. **Simplified Analysis**

   - Quick overview of codebase structure
   - Helps identify tightly coupled modules
   - Assists in refactoring decisions

## Common Dependency Patterns

### Module Dependencies

```python
# The script will detect dependencies like:
from src.sentry.api import endpoint  # Creates edge from current module to api
from src.sentry.auth import tokens  # Creates edge from current module to auth
```

### Visualization Output

```
DiGraph with n nodes and m edges where:
- Nodes represent major modules
- Edges show import relationships
- Node colors indicate module types
```

## Key Benefits to Note

1. **Better Architecture Understanding**

   - Clear view of module relationships
   - Identifies dependency patterns
   - Helps spot architectural issues

1. **Refactoring Support**

   - Identifies tightly coupled modules
   - Helps plan refactoring
   - Shows impact of changes

1. **Documentation Aid**

   - Visual documentation of architecture
   - Easy to share and discuss
   - Helps onboard new developers

## Running the Visualization

```bash
# Install Codegen and dependencies
pip install codegen networkx

# Run the visualization
python run.py
```

The script will:

1. Initialize the codebase
1. Analyze module dependencies
1. Create a dependency graph
1. Output the visualization through codegen.sh

## Customization Options

You can customize the analysis by:

- Modifying the `list_apps` to include different modules
- Adjusting node metadata and colors
- Adding additional filtering criteria

## Learn More

- [NetworkX Documentation](https://networkx.org/)
- [Python Import System](https://docs.python.org/3/reference/import.html)
- [Codegen Documentation](https://docs.codegen.com)
- [Graph visualization](https://docs.codegen.com/building-with-codegen/codebase-visualization)

## Contributing

Feel free to submit issues and enhancement requests! Contributions to improve the visualization or add new features are welcome.
