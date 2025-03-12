import codegen
import networkx as nx
from codegen import Codebase
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.detached_symbols.function_call import FunctionCall
from codegen.sdk.core.external_module import ExternalModule
from codegen.sdk.core.function import Function

G = nx.DiGraph()

IGNORE_EXTERNAL_MODULE_CALLS = True
IGNORE_CLASS_CALLS = False
MAX_DEPTH = 10

# Color scheme for different types of nodes in the visualization
# Each node type has a distinct color for better visual differentiation
COLOR_PALETTE = {
    "StartFunction": "#9cdcfe",  # Base purple - draws attention to the root node
    "PyFunction": "#a277ff",  # Mint green - complementary to purple
    "PyClass": "#ffca85",  # Warm peach - provides contrast
    "ExternalModule": "#f694ff",  # Light pink - analogous to base purple
}


def generate_edge_meta(call: FunctionCall) -> dict:
    """Generate metadata for graph edges representing function calls

    Args:
        call (FunctionCall): Object containing information about the function call

    Returns:
        dict: Metadata including name, file path, and location information
    """
    return {"name": call.name, "file_path": call.filepath, "start_point": call.start_point, "end_point": call.end_point, "symbol_name": "FunctionCall"}


def create_downstream_call_trace(src_func: Function, depth: int = 0):
    """Creates call graph for parent function by recursively traversing all function calls

    This function builds a directed graph showing all downstream function calls,
    up to MAX_DEPTH levels deep. Each node represents a function and edges
    represent calls between functions.

    Args:
        src_func (Function): The function for which a call graph will be created
        depth (int): Current depth in the recursive traversal
    """
    # Stop recursion if max depth reached
    if MAX_DEPTH <= depth:
        return
    # Stop if the source is an external module
    if isinstance(src_func, ExternalModule):
        return

    # Examine each function call made by the source function
    for call in src_func.function_calls:
        # Skip recursive calls
        if call.name == src_func.name:
            continue

        # Get the function definition being called
        func = call.function_definition

        # Skip if function definition not found
        if not func:
            continue
        # Apply filtering based on configuration flags
        if isinstance(func, ExternalModule) and IGNORE_EXTERNAL_MODULE_CALLS:
            continue
        if isinstance(func, Class) and IGNORE_CLASS_CALLS:
            continue

        # Generate the display name for the function
        # For methods, include the class name
        if isinstance(func, (Class, ExternalModule)):
            func_name = func.name
        elif isinstance(func, Function):
            func_name = f"{func.parent_class.name}.{func.name}" if func.is_method else func.name

        # Add node and edge to the graph with appropriate metadata
        G.add_node(func, name=func_name, color=COLOR_PALETTE.get(func.__class__.__name__))
        G.add_edge(src_func, func, **generate_edge_meta(call))

        # Recursively process called function if it's a regular function
        if isinstance(func, Function):
            create_downstream_call_trace(func, depth + 1)


@codegen.function("visualize-function-call-relationships")
def run(codebase: Codebase):
    """Generate a visualization of function call relationships in a codebase.

    This codemod:
    1. Creates a directed graph of function calls starting from a target method
    2. Tracks relationships between functions, classes, and external modules
    3. Generates a visual representation of the call hierarchy
    """
    global G
    G = nx.DiGraph()

    target_class = codebase.get_class("SharingConfigurationViewSet")
    target_method = target_class.get_method("patch")

    # Generate the call graph starting from the target method
    create_downstream_call_trace(target_method)

    # Add the root node (target method) to the graph
    G.add_node(target_method, name=f"{target_class.name}.{target_method.name}", color=COLOR_PALETTE.get("StartFunction"))

    print(G)
    print("Use codegen.sh to visualize the graph!")


if __name__ == "__main__":
    print("Initializing codebase...")
    codebase = Codebase.from_repo("codegen-oss/posthog", commit="b174f2221ea4ae50e715eb6a7e70e9a2b0760800", language="python")
    print(f"Codebase with {len(codebase.files)} files and {len(codebase.functions)} functions.")
    print("Creating graph...")

    run(codebase)
