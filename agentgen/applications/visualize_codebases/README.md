# Codebase Relationship Visualizations

This set of examples demonstrates four different approaches to visualizing code relationships using Codegen. Each visualization script creates a graph to help developers understand different aspects of code structure and dependencies.

## Visualization Types

### 1. Function Call Relationships (`call_trace.py`)

Traces downstream function call relationships from a target method. This visualization is particularly useful for understanding the flow of execution and identifying complex call chains that might need optimization or refactoring.

> [!NOTE]
> View the graph-based visualization created by this script on the `PostHog/posthog` repository [here](https://www.codegen.sh/codemod/6a34b45d-c8ad-422e-95a8-46d4dc3ce2b0/public/diff).

```python
def create_downstream_call_trace(src_func: Function, depth: int = 0):
    """Creates call graph for parent function by recursively traversing all function calls"""
    if MAX_DEPTH <= depth:
        return
    if isinstance(src_func, ExternalModule):
        return

    for call in src_func.function_calls:
        # Skip recursive calls
        if call.name == src_func.name:
            continue

        func = call.function_definition
        if not func:
            continue

        # Add node and edge to graph with metadata
        G.add_node(func, name=func_name, color=COLOR_PALETTE.get(func.__class__.__name__))
        G.add_edge(src_func, func, **generate_edge_meta(call))

        # Recurse for nested calls
        if isinstance(func, Function):
            create_downstream_call_trace(func, depth + 1)
```

### 2. Symbol Dependencies (`dependency_trace.py`)

Maps symbol dependencies throughout the codebase. This helps developers identify tightly coupled components and understand the impact of modifying shared dependencies, making it easier to plan architectural changes.

> [!NOTE]
> View the graph-based visualization created by this script on the `PostHog/posthog` repository [here](codegen.sh/codemod/f6c63e40-cc20-4b91-a6c7-e5cbd736ce0d/public/diff).

```python
def create_dependencies_visualization(symbol: Symbol, depth: int = 0):
    """Creates a visualization of symbol dependencies in the codebase"""
    if depth >= MAX_DEPTH:
        return

    for dep in symbol.dependencies:
        dep_symbol = None
        if isinstance(dep, Symbol):
            dep_symbol = dep
        elif isinstance(dep, Import):
            dep_symbol = dep.resolved_symbol if dep.resolved_symbol else None

        if dep_symbol:
            G.add_node(dep_symbol, color=COLOR_PALETTE.get(dep_symbol.__class__.__name__, "#f694ff"))
            G.add_edge(symbol, dep_symbol)

            if not isinstance(dep_symbol, Class):
                create_dependencies_visualization(dep_symbol, depth + 1)
```

### 3. Function Blast Radius (`blast_radius.py`)

Shows the impact radius of potential changes. This visualization is invaluable for risk assessment before refactoring, as it reveals all the code paths that could be affected by modifying a particular function or symbol.

> [!NOTE]
> View the graph-based visualization created by this script on the `PostHog/posthog` repository [here](codegen.sh/codemod/02f11ebe-6a3a-4687-b31d-2d6bc6a04f3c/public/diff).

```python
def create_blast_radius_visualization(symbol: PySymbol, depth: int = 0):
    """Recursively build a graph visualization showing how a symbol is used"""
    if depth >= MAX_DEPTH:
        return

    for usage in symbol.usages:
        usage_symbol = usage.usage_symbol

        # Color code HTTP methods specially
        if is_http_method(usage_symbol):
            color = COLOR_PALETTE.get("HTTP_METHOD")
        else:
            color = COLOR_PALETTE.get(usage_symbol.__class__.__name__, "#f694ff")

        G.add_node(usage_symbol, color=color)
        G.add_edge(symbol, usage_symbol, **generate_edge_meta(usage))

        create_blast_radius_visualization(usage_symbol, depth + 1)
```

### 4. Class Method Relationships (`method_relationships.py`)

Creates a comprehensive view of class method interactions. This helps developers understand class cohesion, identify potential god classes, and spot opportunities for breaking down complex classes into smaller, more manageable components.

> [!NOTE]
> View the graph-based visualization created by this script on the `modal-labs/modal-client` repository [here](https://www.codegen.sh/codemod/66e2e195-ceec-4935-876a-ed4cfc1731c7/public/diff).

```python
def graph_class_methods(target_class: Class):
    """Creates a graph visualization of all methods in a class and their call relationships"""
    G.add_node(target_class, color=COLOR_PALETTE["StartClass"])

    # Add all methods as nodes
    for method in target_class.methods:
        method_name = f"{target_class.name}.{method.name}"
        G.add_node(method, name=method_name, color=COLOR_PALETTE["StartMethod"])
        visited.add(method)
        G.add_edge(target_class, method)

    # Create call traces for each method
    for method in target_class.methods:
        create_downstream_call_trace(method)
```

## Common Features

All visualizations share these characteristics:

1. **Configurable Depth**

   - MAX_DEPTH setting controls recursion
   - Prevents infinite loops in circular references

1. **Color Coding**

   ```python
   COLOR_PALETTE = {
       "StartFunction": "#9cdcfe",  # Entry point
       "PyFunction": "#a277ff",  # Regular functions
       "PyClass": "#ffca85",  # Classes
       "ExternalModule": "#f694ff",  # External calls
   }
   ```

1. **Edge Metadata**

   - Tracks file paths
   - Creates data object for visualization

## Running the Visualizations

```bash
# Install dependencies
pip install codegen networkx

# Run any visualization script
python call_trace.py      # Function call relationships
python dependency_trace.py # Symbol dependencies
python blast_radius.py    # Function blast radius
python method_relationships.py  # Class method relationships
```

Each script will:

1. Initialize the codebase
1. Create the appropriate graph for the relationship
1. Generate visualization data

## View Results

After running a script, you'll get a graph object containing node and edge relationships. You can view an interactive visualization of the graph through the links above pointing to codegen.sh.

## Learn More

- [Codebase Visualization Documentation](https://docs.codegen.com/tutorials/codebase-visualization)
- [Codegen Documentation](https://docs.codegen.com)

## Contributing

Feel free to submit issues and any enhancement requests!
