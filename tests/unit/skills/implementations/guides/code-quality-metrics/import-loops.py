from abc import ABC

import networkx
from networkx import DiGraph

from codegen.sdk.core.codebase import CodebaseType
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCasePyFile

ImportCycleDetectionAndVisualizationTest = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
from module_b import function_b

def function_a():
    return "Function A"
""",
            filepath="module_a.py",
        ),
        SkillTestCasePyFile(
            input="""
from module_c import function_c

def function_b():
    return "Function B"
""",
            filepath="module_b.py",
        ),
        SkillTestCasePyFile(
            input="""
from module_a import function_a

def function_c():
    return "Function C"
""",
            filepath="module_c.py",
        ),
        SkillTestCasePyFile(
            input="""
from module_d import function_d

def function_x():
    return "Function X"
""",
            filepath="module_x.py",
        ),
        SkillTestCasePyFile(
            input="""
from module_x import function_x

def function_d():
    return "Function D"
""",
            filepath="module_d.py",
        ),
        SkillTestCasePyFile(
            input="""
def standalone_function():
    return "Standalone Function"
""",
            filepath="standalone_module.py",
        ),
    ],
    sanity=True,
)


@skill(
    prompt="""Generate a Python code snippet that analyzes a codebase for import cycles using the NetworkX library.
    The code should create a directed graph to represent the imports, identify strongly connected components (SCCs),
    count the number of cycles, and visualize the cycles in a new graph. Ensure to include comments explaining each
    step, such as iterating over imports, adding edges to the graph, finding SCCs, counting cycles, and visualizing
    the results.""",
    guide=True,
    uid="26b3f1e9-de94-4c4c-85ba-302611139cb9",
)
class ImportCycleDetectionAndVisualization(Skill, ABC):
    """This code snippet analyzes a codebase to identify and visualize import cycles in a directed graph
    representation of file dependencies. It constructs a directed graph using the import relationships between files,
    finds strongly connected components (SCCs) to detect cycles, and counts the number of cycles that involve
    multiple nodes. It then creates a new directed graph specifically for the nodes involved in the detected cycles
    and visualizes this cycle graph.
    """

    @staticmethod
    @skill_impl(test_cases=[ImportCycleDetectionAndVisualizationTest], language=ProgrammingLanguage.PYTHON)
    def skill_func(codebase: CodebaseType):
        ctx: DiGraph = networkx.DiGraph()

        # iterate over all imports
        for pyimport in codebase.imports:
            # Extract to/from files
            if pyimport.from_file and pyimport.to_file:
                # Add nodes and edges to the graph
                ctx.add_edge(pyimport.from_file.file_path, pyimport.to_file.file_path)

        # Find strongly connected components
        strongly_connected_components = list(networkx.strongly_connected_components(ctx))

        # Count the number of cycles (SCCs with more than one node)
        import_cycles = [scc for scc in strongly_connected_components if len(scc) > 1]

        print(f"Found {len(import_cycles)} import cycles")

        # Visualize the import cycles
        # Create a new graph for the cycle nodes
        cycle_graph: DiGraph = networkx.DiGraph()

        # Add nodes involved in cycles to the new graph
        for cycle in networkx.simple_cycles(ctx):
            if len(cycle) > 2:
                # Add nodes to the cycle graph
                for node in cycle:
                    cycle_graph.add_node(node)
                # Add edges between the nodes in the cycle
                for i in range(len(cycle)):
                    cycle_graph.add_edge(cycle[i], cycle[(i + 1) % len(cycle)])  # Connect in a circular manner
                # Depends on the size of the codebase and the number of cycles, this may take a while to run
                # so we break after the first cycle it's found
                break

        codebase.visualize(cycle_graph)
