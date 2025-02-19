import codegen
import networkx as nx
from codegen import Codebase
from codegen.sdk.core.dataclasses.usage import Usage
from codegen.sdk.python.function import PyFunction
from codegen.sdk.python.symbol import PySymbol

# Create a directed graph for visualizing relationships between code elements
G = nx.DiGraph()

# Maximum depth to traverse in the call graph to prevent infinite recursion
MAX_DEPTH = 5

# Define colors for different types of nodes in the visualization
COLOR_PALETTE = {
    "StartFunction": "#9cdcfe",  # Starting function (light blue)
    "PyFunction": "#a277ff",  # Python functions (purple)
    "PyClass": "#ffca85",  # Python classes (orange)
    "ExternalModule": "#f694ff",  # External module imports (pink)
    "HTTP_METHOD": "#ffca85",  # HTTP method handlers (orange)
}

# List of common HTTP method names to identify route handlers
HTTP_METHODS = ["get", "put", "patch", "post", "head", "delete"]


def generate_edge_meta(usage: Usage) -> dict:
    """
    Generate metadata for graph edges based on a usage relationship.

    Args:
        usage: A Usage object representing how a symbol is used

    Returns:
        dict: Edge metadata including source location and symbol info
    """
    return {"name": usage.match.source, "file_path": usage.match.filepath, "start_point": usage.match.start_point, "end_point": usage.match.end_point, "symbol_name": usage.match.__class__.__name__}


def is_http_method(symbol: PySymbol) -> bool:
    """
    Check if a symbol represents an HTTP method handler.

    Args:
        symbol: A Python symbol to check

    Returns:
        bool: True if symbol is an HTTP method handler
    """
    if isinstance(symbol, PyFunction) and symbol.is_method:
        return symbol.name in HTTP_METHODS
    return False


def create_blast_radius_visualization(symbol: PySymbol, depth: int = 0):
    """
    Recursively build a graph visualization showing how a symbol is used.
    Shows the "blast radius" - everything that would be affected by changes.

    Args:
        symbol: Starting symbol to analyze
        depth: Current recursion depth
    """
    # Stop recursion if we hit max depth
    if depth >= MAX_DEPTH:
        return

    # Process each usage of the symbol
    for usage in symbol.usages:
        usage_symbol = usage.usage_symbol

        # Determine node color based on symbol type
        if is_http_method(usage_symbol):
            color = COLOR_PALETTE.get("HTTP_METHOD")
        else:
            color = COLOR_PALETTE.get(usage_symbol.__class__.__name__, "#f694ff")

        # Add node and edge to graph
        G.add_node(usage_symbol, color=color)
        G.add_edge(symbol, usage_symbol, **generate_edge_meta(usage))

        # Recurse to process usages of this symbol
        create_blast_radius_visualization(usage_symbol, depth + 1)


@codegen.function("visualize-function-blast-radius")
def run(codebase: Codebase):
    """
    Generate a visualization showing the blast radius of changes to a function.

    This codemod:
    1. Identifies all usages of a target function
    2. Creates a graph showing how the function is used throughout the codebase
    3. Highlights HTTP method handlers and different types of code elements
    """
    global G
    G = nx.DiGraph()

    # Get the target function to analyze
    target_func = codebase.get_function("export_asset")

    # Add starting function to graph with special color
    G.add_node(target_func, color=COLOR_PALETTE.get("StartFunction"))

    # Build the visualization starting from target function
    create_blast_radius_visualization(target_func)

    print(G)
    print("Use codegen.sh to visualize the graph!")


if __name__ == "__main__":
    print("Initializing codebase...")
    codebase = Codebase.from_repo("codegen-oss/posthog", commit="b174f2221ea4ae50e715eb6a7e70e9a2b0760800", language="python")
    print(f"Codebase with {len(codebase.files)} files and {len(codebase.functions)} functions.")
    print("Creating graph...")

    run(codebase)
