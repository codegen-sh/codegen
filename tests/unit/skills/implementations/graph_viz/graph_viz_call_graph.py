from abc import ABC

import networkx as nx

from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.codebase import CodebaseType
from codegen.sdk.core.detached_symbols.function_call import FunctionCall
from codegen.sdk.core.external_module import ExternalModule
from codegen.sdk.core.function import Function
from codegen.sdk.core.interfaces.callable import Callable
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCasePyFile

CallGraphFromNodeTest = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
def function_to_trace():
    Y()
    Z()

def Y():
    A()

def Z():
    B()

def A():
    pass

def B():
    C()

def C():
    pass
""",
            filepath="example.py",
        )
    ],
    graph=True,
)


@skill(eval_skill=False, prompt="Show me a visualization of the call graph from X", uid="81e8fbb7-a00a-4e74-b9c2-24f79d24d389")
class CallGraphFromNode(Skill, ABC):
    """This skill creates a directed call graph for a given function. Starting from the specified function, it recursively iterates
    through its function calls and the functions called by them, building a graph of the call paths to a maximum depth. The root of the directed graph
    is the starting function, each node represents a function call, and edge from node A to node B indicates that function A calls function B. In its current form,
    it ignores recursive calls and external modules but can be modified trivially to include them. Furthermore, this skill can easily be adapted to support
    creating a call graph for a class method. In order to do this one simply needs to replace

    `function_to_trace = codebase.get_function("function_to_trace")`

    with

    `function_to_trace = codebase.get_class("class_of_method_to_trace").get_method("method_to_trace")`
    """

    @staticmethod
    @skill_impl(test_cases=[CallGraphFromNodeTest], language=ProgrammingLanguage.PYTHON)
    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType):
        # Create a directed graph
        G = nx.DiGraph()

        # ===== [ Whether to Graph External Modules] =====
        GRAPH_EXERNAL_MODULE_CALLS = False

        # ===== [ Maximum Recursive Depth ] =====
        MAX_DEPTH = 5

        def create_downstream_call_trace(parent: FunctionCall | Function | None = None, depth: int = 0):
            """Creates call graph for parent

            This function recurses through the call graph of a function and creates a visualization

            Args:
                parent (FunctionCallDefinition| Function): The function for which a call graph will be created.
                depth (int): The current depth of the recursive stack.

            """
            # if the maximum recursive depth has been exceeded return
            if MAX_DEPTH <= depth:
                return
            if isinstance(parent, FunctionCall):
                src_call, src_func = parent, parent.function_definition
            else:
                src_call, src_func = parent, parent
            # Iterate over all call paths of the symbol
            for call in src_func.function_calls:
                # the symbol being called
                func = call.function_definition

                # ignore direct recursive calls
                if func.name == src_func.name:
                    continue

                # if the function being called is not from an external module
                if not isinstance(func, ExternalModule):
                    # add `call` to the graph and an edge from `src_call` to `call`
                    G.add_node(call)
                    G.add_edge(src_call, call)

                    # recursive call to function call
                    create_downstream_call_trace(call, depth + 1)
                elif GRAPH_EXERNAL_MODULE_CALLS:
                    # add `call` to the graph and an edge from `src_call` to `call`
                    G.add_node(call)
                    G.add_edge(src_call, call)

        # ===== [ Function To Be Traced] =====
        function_to_trace = codebase.get_function("function_to_trace")

        # Set starting node
        G.add_node(function_to_trace, color="yellow")

        # Add all the children (and sub-children) to the graph
        create_downstream_call_trace(function_to_trace)

        # Visualize the graph
        codebase.visualize(G)


CallGraphFilterTest = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
class MyClass:
    def get(self):
        self.helper_method()
        return "GET request"

    def post(self):
        self.helper_method()
        return "POST request"

    def patch(self):
        return "PATCH request"

    def delete(self):
        return "DELETE request"

    def helper_method(self):
        pass

    def other_method(self):
        self.helper_method()
        return "This method should not be included"

def external_function():
    instance = MyClass()
    instance.get()
    instance.post()
    instance.other_method()
""",
            filepath="path/to/file.py",
        ),
        SkillTestCasePyFile(
            input="""
from path.to.file import MyClass

def function_to_trace():
    instance = MyClass()
    assert instance.get() == "GET request"
    assert instance.post() == "POST request"
    assert instance.patch() == "PATCH request"
    assert instance.delete() == "DELETE request"
""",
            filepath="path/to/file1.py",
        ),
    ],
    graph=True,
)


@skill(
    eval_skill=False,
    prompt="Show me a visualization of the call graph from MyClass and filter out test files and include only the methods that have the name post, get, patch, delete",
    uid="fc1f3ea0-46e7-460a-88ad-5312d4ca1a12",
)
class CallGraphFilter(Skill, ABC):
    """This skill shows a visualization of the call graph from a given function or symbol.
    It iterates through the usages of the starting function and its subsequent calls,
    creating a directed graph of function calls. The skill filters out test files and class declarations
    and includes only methods with specific names (post, get, patch, delete).
    The call graph uses red for the starting node, yellow for class methods,
    and can be customized based on user requests. The graph is limited to a specified depth
    to manage complexity. In its current form, it ignores recursive calls and external modules
    but can be modified trivially to include them
    """

    @staticmethod
    @skill_impl(test_cases=[CallGraphFilterTest], language=ProgrammingLanguage.PYTHON)
    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType):
        # Create a directed graph
        G = nx.DiGraph()

        # Get the symbol for my_class
        func_to_trace = codebase.get_function("function_to_trace")

        # Add the main symbol as a node
        G.add_node(func_to_trace, color="red")

        # ===== [ Maximum Recursive Depth ] =====
        MAX_DEPTH = 5

        SKIP_CLASS_DECLARATIONS = True

        cls = codebase.get_class("MyClass")

        # Define a recursive function to traverse function calls
        def create_filtered_downstream_call_trace(parent: FunctionCall | Function, current_depth, max_depth):
            if current_depth > max_depth:
                return

            # if parent is of type Function
            if isinstance(parent, Function):
                # set both src_call, src_func to parent
                src_call, src_func = parent, parent
            else:
                # get the first callable of parent
                src_call, src_func = parent, parent.function_definition

            # Iterate over all call paths of the symbol
            for call in src_func.function_calls:
                # the symbol being called
                func = call.function_definition

                if SKIP_CLASS_DECLARATIONS and isinstance(func, Class):
                    continue

                # if the function being called is not from an external module and is not defined in a test file
                if not isinstance(func, ExternalModule) and not func.file.filepath.startswith("test"):
                    # add `call` to the graph and an edge from `src_call` to `call`
                    metadata = {}
                    if isinstance(func, Function) and func.is_method and func.name in ["post", "get", "patch", "delete"]:
                        name = f"{func.parent_class.name}.{func.name}"
                        metadata = {"color": "yellow", "name": name}
                    G.add_node(call, **metadata)
                    G.add_edge(src_call, call, symbol=cls)  # Add edge from current to successor

                    # Recursively add successors of the current symbol
                    create_filtered_downstream_call_trace(call, current_depth + 1, max_depth)

        # Start the recursive traversal
        create_filtered_downstream_call_trace(func_to_trace, 1, MAX_DEPTH)

        # Visualize the graph
        codebase.visualize(G)


CallPathsBetweenNodesTest = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
def start_func():
    intermediate_func()
def intermediate_func():
    end_func()

def end_func():
    pass
""",
            filepath="example.py",
        )
    ],
    graph=True,
)


@skill(eval_skill=False, prompt="Show me a visualization of the call paths between start_class and end_class", uid="aa3f70c3-ac1c-4737-a8b8-7ba89e3c5671")
class CallPathsBetweenNodes(Skill, ABC):
    """This skill generates and visualizes a call graph between two specified functions.
    It starts from a given function and iteratively traverses through its function calls,
    building a directed graph of the call paths. The skill then identifies all simple paths between the
    start and end functions, creating a subgraph that includes only the nodes in these paths.

    By default, the call graph uses blue for the starting node and red for the ending node, but these
    colors can be customized based on user preferences. The visualization provides a clear representation
    of how functions are interconnected, helping developers understand the flow of execution and
    dependencies between different parts of the codebase.

    In its current form, it ignores recursive calls and external modules but can be modified trivially to include them
    """

    @staticmethod
    @skill_impl(test_cases=[CallPathsBetweenNodesTest], language=ProgrammingLanguage.PYTHON)
    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType):
        # Create a directed graph
        G = nx.DiGraph()

        # ===== [ Maximum Recursive Depth ] =====
        MAX_DEPTH = 5

        # Define a recursive function to traverse usages
        def create_downstream_call_trace(parent: FunctionCall | Function, end: Callable, current_depth, max_depth):
            if current_depth > max_depth:
                return

            # if parent is of type Function
            if isinstance(parent, Function):
                # set both src_call, src_func to parent
                src_call, src_func = parent, parent
            else:
                # get the first callable of parent
                src_call, src_func = parent, parent.function_definition

            # Iterate over all call paths of the symbol
            for call in src_func.function_calls:
                # the symbol being called
                func = call.function_definition

                # ignore direct recursive calls
                if func.name == src_func.name:
                    continue

                # if the function being called is not from an external module
                if not isinstance(func, ExternalModule):
                    # add `call` to the graph and an edge from `src_call` to `call`
                    G.add_node(call)
                    G.add_edge(src_call, call)

                    if func == end:
                        G.add_edge(call, end)
                        return
                    # recursive call to function call
                    create_downstream_call_trace(call, end, current_depth + 1, max_depth)

        # Get the start and end function
        start = codebase.get_function("start_func")
        end = codebase.get_function("end_func")

        # Set starting node as blue
        G.add_node(start, color="blue")
        # Set ending node as red
        G.add_node(end, color="red")

        # Start the recursive traversal
        create_downstream_call_trace(start, end, 1, MAX_DEPTH)

        # Find all the simple paths between start and end
        all_paths = nx.all_simple_paths(G, source=start, target=end)

        # Collect all nodes that are part of these paths
        nodes_in_paths = set()
        for path in all_paths:
            nodes_in_paths.update(path)

        # Create a new subgraph with only the nodes in the paths
        G = G.subgraph(nodes_in_paths)

        # Visualize the graph
        codebase.visualize(G)
