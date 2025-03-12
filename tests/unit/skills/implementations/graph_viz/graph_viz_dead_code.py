from abc import ABC

import networkx as nx

from codegen.sdk.core.codebase import CodebaseType
from codegen.sdk.core.function import Function
from codegen.sdk.core.import_resolution import Import
from codegen.sdk.core.symbol import Symbol
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCasePyFile

PyDeadCodeTest = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
# Live code
def used_function():
    return "I'm used!"

class UsedClass:
    def used_method(self):
        return "I'm a used method!"

# Dead code
def unused_function():
    return "I'm never called!"

class UnusedClass:
    def unused_method(self):
        return "I'm never used!"

# Second-order dead code
def second_order_dead():
    unused_function()
    UnusedClass().unused_method()

# More live code
def another_used_function():
    return used_function()

# Main execution
def main():
    print(used_function())
    print(UsedClass().used_method())
    print(another_used_function())

if __name__ == "__main__":
    main()
""",
            filepath="example.py",
        ),
        SkillTestCasePyFile(
            input="""
# This file should be ignored by the DeadCode skill

from example import used_function, UsedClass

def test_used_function():
    assert used_function() == "I'm used!"

def test_used_class():
    assert UsedClass().used_method() == "I'm a used method!"
""",
            filepath="test_example.py",
        ),
        SkillTestCasePyFile(
            input="""
# This file contains a decorated function that should be ignored

from functools import lru_cache

@lru_cache
def cached_function():
    return "I'm cached!"

# This function is dead code but should be ignored due to decoration
@deprecated
def old_function():
    return "I'm old but decorated!"

# This function is dead code and should be detected
def real_dead_code():
    return "I'm really dead!"
""",
            filepath="decorated_functions.py",
        ),
    ],
    graph=True,
)


@skill(
    eval_skill=False,
    prompt="Show me a visualization of the call graph from my_class and filter out test files and include only the methods that have the name post, get, patch, delete",
    uid="ec5e98c9-b57f-43f8-8b3c-af1b30bb91e6",
)
class DeadCode(Skill, ABC):
    """This skill shows a visualization of the dead code in the codebase.
    It iterates through all functions in the codebase, identifying those
    that have no usages and are not in test files or decorated. These functions
    are considered 'dead code' and are added to a directed graph. The skill
    then explores the dependencies of these dead code functions, adding them to
    the graph as well. This process helps to identify not only directly unused code
    but also code that might only be used by other dead code (second-order dead code).
    The resulting visualization provides a clear picture of potentially removable code,
    helping developers to clean up and optimize their codebase.
    """

    @staticmethod
    @skill_impl(test_cases=[PyDeadCodeTest], language=ProgrammingLanguage.PYTHON)
    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType):
        # Create a directed graph to visualize dead and second-order dead code
        G = nx.DiGraph()

        # First, identify all dead code
        dead_code: list[Function] = []

        # Iterate through all functions in the codebase
        for function in codebase.functions:
            # Filter down functions
            if "test" in function.file.filepath:
                continue

            if function.decorators:
                continue

            # Check if the function has no usages
            if not function.symbol_usages:
                # Add the function to the dead code list
                dead_code.append(function)
                # Add the function to the graph as dead code
                G.add_node(function, color="red")

        # # Now, find second-order dead code
        for symbol in dead_code:
            # Get all usages of the dead code symbol
            for dep in symbol.dependencies:
                if isinstance(dep, Import):
                    dep = dep.imported_symbol
                if isinstance(dep, Symbol):
                    if "test" not in dep.name:
                        G.add_node(dep)
                        G.add_edge(symbol, dep, color="red")
                        for usage_symbol in dep.symbol_usages:
                            if isinstance(usage_symbol, Function):
                                if "test" not in usage_symbol.name:
                                    G.add_edge(usage_symbol, dep)

        # Visualize the graph to show dead and second-order dead code
        codebase.visualize(G)
