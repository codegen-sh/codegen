from codegen.sdk.core.codebase import CodebaseType, PyCodebaseType
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCasePyFile

########################################################################################################################
# Py test cases
########################################################################################################################
py_file_1 = """
from dataclasses import dataclass

@dataclass
class Employee:
    name: str
    id: int
    team: str
    salary: float


# Example usage
if __name__ == "__main__":
    emp = Employee(name="John Doe", id=1234, team="Development", salary=75000.00)
    print(emp)
"""

py_file_1_output = """
from dataclasses import Employee
from dataclasses import dataclass


# Example usage
if __name__ == "__main__":
    emp = Employee(name="John Doe", id=1234, team="Development", salary=75000.00)
    print(emp)
"""

py_file_2_output = """from dataclasses import dataclass


@dataclass
class Employee:
    name: str
    id: int
    team: str
    salary: float"""

py_test_cases = [
    SkillTestCase(
        files=[
            SkillTestCasePyFile(input=py_file_1, output=py_file_1_output),
            SkillTestCasePyFile(filepath="dataclasses.py", input="", output=py_file_2_output),
        ]
    ),
]


@skill(eval_skill=False, prompt="Moves all classes decorated with @dataclasses into a dedicated directory", uid="98450421-bb3b-4605-9f94-f169e4ae0f23")
class MoveDataclassesSkills(Skill):
    """Moves all classes decorated with @dataclasses into a dedicated directory"""

    @staticmethod
    @skill_impl(py_test_cases, language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: PyCodebaseType):
        """Moves the dataclasses and adds a back edge to the moved symbol in the original file"""
        # Iterate over all files in the codebase
        for file in codebase.files:
            # Check if the file is not a dataclasses file
            if "dataclasses" not in file.filepath and "dataclasses" not in file.name:
                for cls in file.classes:
                    # Check if the class is a dataclass
                    if "@dataclass" in cls.source:
                        # Get a new filename
                        # Note: extension is included in the file name
                        new_filename = "dataclasses.py"

                        # Ensure the file exists
                        if not codebase.has_file(new_filename):
                            dst_file = codebase.create_file(new_filename, "")
                        else:
                            dst_file = codebase.get_file(new_filename)

                        # Move the symbol and it's dependencies, adding a "back edge" import to the original file
                        cls.move_to_file(dst_file, include_dependencies=True, strategy="add_back_edge")

    @staticmethod
    @skill_impl([], language=ProgrammingLanguage.TYPESCRIPT, ignore=True)
    def typescript_skill_func(codebase: CodebaseType):
        """Dataclasses is only available in Python"""
        ...
