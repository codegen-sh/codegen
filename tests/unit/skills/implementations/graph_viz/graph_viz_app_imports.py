from abc import ABC

from codegen.sdk.core.codebase import CodebaseType
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCasePyFile

FileAppImportGraphTest = SkillTestCase(
    [
        SkillTestCasePyFile(input="from file1 import foo\nfrom file2 import bar", filepath="path/to/file.py"),
        SkillTestCasePyFile("def foo():\n    pass", filepath="file1.py"),
        SkillTestCasePyFile("def bar():\n    pass", filepath="file2.py"),
    ],
    graph=True,
)


@skill(eval_skill=False, prompt="Show me all the apps imported by the file path/to/file.py", uid="fda3c38a-5cf8-46cf-93bd-80fd19ae04e2")
class FileAppImportGraph(Skill, ABC):
    """This skill visualizes the import relationships for a specific file in the codebase.
    It creates a directed graph where nodes represent the target file and its imported modules.
    Edges in the graph indicate the import relationships, pointing from the file to its imports.
    The skill focuses on a particular file ('path/to/file.py') and analyzes its import statements to construct the graph.
    This visualization helps developers understand the dependencies and structure of imports within the specified file, which can be useful
    for code organization and dependency management.
    """

    @staticmethod
    @skill_impl(test_cases=[FileAppImportGraphTest], language=ProgrammingLanguage.PYTHON)
    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType):
        import networkx as nx

        # Create a directed graph
        G = nx.DiGraph()

        # Get the specific file
        file = codebase.get_file("path/to/file.py")

        # Add a node for the file
        G.add_node(file.filepath)

        # Iterate over all imports in the file
        for imp in file.imports:
            # Add a node for the imported module
            G.add_node(imp.import_statement.source)
            # Create an edge from the file to the imported module
            G.add_edge(file.filepath, imp.import_statement.source)

        # Visualize the graph
        codebase.visualize(G)
