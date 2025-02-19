import codegen
import networkx as nx
from codegen import Codebase
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.detached_symbols.function_call import FunctionCall
from codegen.sdk.core.external_module import ExternalModule
from codegen.sdk.core.function import Function

G = nx.DiGraph()

# Configuration Settings
IGNORE_EXTERNAL_MODULE_CALLS = False
IGNORE_CLASS_CALLS = True
MAX_DEPTH = 100

# Track visited nodes to prevent duplicate processing
visited = set()

COLOR_PALETTE = {
    "StartMethod": "#9cdcfe",  # Light blue for root/entry point methods
    "PyFunction": "#a277ff",  # Purple for regular Python functions
    "PyClass": "#ffca85",  # Warm peach for class definitions
    "ExternalModule": "#f694ff",  # Pink for external module calls
    "StartClass": "#FFE082",  # Yellow for the starting class
}


def graph_class_methods(target_class: Class):
    """Creates a graph visualization of all methods in a class and their call relationships"""
    G.add_node(target_class, color=COLOR_PALETTE["StartClass"])

    for method in target_class.methods:
        method_name = f"{target_class.name}.{method.name}"
        G.add_node(method, name=method_name, color=COLOR_PALETTE["StartMethod"])
        visited.add(method)
        G.add_edge(target_class, method)

    for method in target_class.methods:
        create_downstream_call_trace(method)


def generate_edge_meta(call: FunctionCall) -> dict:
    """Generate metadata for graph edges representing function calls"""
    return {"name": call.name, "file_path": call.filepath, "start_point": call.start_point, "end_point": call.end_point, "symbol_name": "FunctionCall"}


def create_downstream_call_trace(src_func: Function, depth: int = 0):
    """Creates call graph for parent function by recursively traversing all function calls"""
    if MAX_DEPTH <= depth or isinstance(src_func, ExternalModule):
        return

    for call in src_func.function_calls:
        if call.name == src_func.name:
            continue

        func = call.function_definition
        if not func:
            continue

        if isinstance(func, ExternalModule) and IGNORE_EXTERNAL_MODULE_CALLS:
            continue
        if isinstance(func, Class) and IGNORE_CLASS_CALLS:
            continue

        if isinstance(func, (Class, ExternalModule)):
            func_name = func.name
        elif isinstance(func, Function):
            func_name = f"{func.parent_class.name}.{func.name}" if func.is_method else func.name

        if func not in visited:
            G.add_node(func, name=func_name, color=COLOR_PALETTE.get(func.__class__.__name__, None))
            visited.add(func)

        G.add_edge(src_func, func, **generate_edge_meta(call))

        if isinstance(func, Function):
            create_downstream_call_trace(func, depth + 1)


@codegen.function("visualize-class-method-relationships")
def run(codebase: Codebase):
    """Generate a visualization of method call relationships within a class.

    This codemod:
    1. Creates a directed graph with the target class as the root node
    2. Adds all class methods and their downstream function calls
    3. Generates a visual representation of the call hierarchy
    """
    global G, visited
    G = nx.DiGraph()
    visited = set()

    target_class = codebase.get_class("_Client")
    graph_class_methods(target_class)

    print(G)
    print("Use codegen.sh to visualize the graph!")


if __name__ == "__main__":
    print("Initializing codebase...")
    codebase = Codebase.from_repo("codegen-oss/modal-client", commit="00bf226a1526f9d775d2d70fc7711406aaf42958", language="python")
    print(f"Codebase with {len(codebase.files)} files and {len(codebase.functions)} functions.")
    print("Creating graph...")

    run(codebase)
