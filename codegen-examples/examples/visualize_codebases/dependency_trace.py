import codegen
import networkx as nx
from codegen import Codebase
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.import_resolution import Import
from codegen.sdk.core.symbol import Symbol

G = nx.DiGraph()

IGNORE_EXTERNAL_MODULE_CALLS = True
IGNORE_CLASS_CALLS = False
MAX_DEPTH = 10

COLOR_PALETTE = {
    "StartFunction": "#9cdcfe",  # Light blue for the starting function
    "PyFunction": "#a277ff",  # Purple for Python functions
    "PyClass": "#ffca85",  # Orange for Python classes
    "ExternalModule": "#f694ff",  # Pink for external module references
}

# Dictionary to track visited nodes and prevent cycles
visited = {}


def create_dependencies_visualization(symbol: Symbol, depth: int = 0):
    """Creates a visualization of symbol dependencies in the codebase

    Recursively traverses the dependency tree of a symbol (function, class, etc.)
    and creates a directed graph representation. Dependencies can be either direct
    symbol references or imports.

    Args:
        symbol (Symbol): The starting symbol whose dependencies will be mapped
        depth (int): Current depth in the recursive traversal
    """
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


@codegen.function("visualize-symbol-dependencies")
def run(codebase: Codebase):
    """Generate a visualization of symbol dependencies in a codebase.

    This codemod:
    1. Creates a directed graph of symbol dependencies starting from a target function
    2. Tracks relationships between functions, classes, and imports
    3. Generates a visual representation of the dependency hierarchy
    """
    global G
    G = nx.DiGraph()

    target_func = codebase.get_function("get_query_runner")
    G.add_node(target_func, color=COLOR_PALETTE.get("StartFunction"))

    create_dependencies_visualization(target_func)

    print(G)
    print("Use codegen.sh to visualize the graph!")


if __name__ == "__main__":
    print("Initializing codebase...")
    codebase = Codebase.from_repo("codegen-oss/posthog", commit="b174f2221ea4ae50e715eb6a7e70e9a2b0760800", language="python")
    print(f"Codebase with {len(codebase.files)} files and {len(codebase.functions)} functions.")
    print("Creating graph...")

    run(codebase)
