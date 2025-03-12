from abc import ABC

import networkx as nx

from codegen.sdk.core.codebase import CodebaseType
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCasePyFile

PyRepoDirTreeTest = SkillTestCase(
    [
        SkillTestCasePyFile(input="# Root level file", filepath="README.md"),
        SkillTestCasePyFile(input="# Configuration file", filepath="config.yaml"),
        SkillTestCasePyFile(
            input="""
def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
""",
            filepath="src/main.py",
        ),
        SkillTestCasePyFile(
            input="""
class User:
    def __init__(self, name):
        self.name = name
""",
            filepath="src/models/user.py",
        ),
        SkillTestCasePyFile(
            input="""
from src.models.user import User

def create_user(name):
    return User(name)
""",
            filepath="src/services/user_service.py",
        ),
        SkillTestCasePyFile(
            input="""
import unittest
from src.models.user import User

class TestUser(unittest.TestCase):
    def test_user_creation(self):
        user = User("Alice")
        self.assertEqual(user.name, "Alice")
""",
            filepath="tests/test_user.py",
        ),
        SkillTestCasePyFile(
            input="""
{
  "name": "my-project",
  "version": "1.0.0",
  "description": "A sample project"
}
""",
            filepath="package.json",
        ),
        SkillTestCasePyFile(
            input="""
node_modules/
*.log
.DS_Store
""",
            filepath=".gitignore",
        ),
    ],
    graph=True,
)


@skill(eval_skill=False, prompt="Show me the directory structure of this codebase", uid="ef9a5a54-d793-4749-992d-63ea3958056b")
class RepoDirTree(Skill, ABC):
    """This skill displays the directory or repository tree structure of a codebase. It analyzes the file paths within the codebase and constructs a hierarchical
    representation of the directory structure. The skill creates a visual graph where each node represents a directory or file, and edges represent the parent-child
    relationships between directories. This visualization helps developers understand the overall organization of the codebase, making it easier to navigate and
    manage large projects. Additionally, it can be useful for identifying potential structural issues or inconsistencies in the project layout.
    """

    @staticmethod
    @skill_impl(test_cases=[PyRepoDirTreeTest], language=ProgrammingLanguage.PYTHON)
    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType):
        # Create a directed graph
        G = nx.DiGraph()

        # Iterate over all files in the codebase
        for file in codebase.files:
            # Get the full filepath
            filepath = file.filepath
            # Split the filepath into parts
            parts = filepath.split("/")

            # Add nodes and edges to the graph
            for i in range(len(parts)):
                # Create a path from the root to the current part
                path = "/".join(parts[: i + 1])
                # Add the node for the current directory
                G.add_node(path)
                # If it's not the root, add an edge from the parent directory to the current directory
                if i > 0:
                    parent_path = "/".join(parts[:i])
                    G.add_edge(parent_path, path)

        codebase.visualize(G)
