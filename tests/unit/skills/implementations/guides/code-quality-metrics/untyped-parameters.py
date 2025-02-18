from abc import ABC

from codegen.sdk.core.codebase import CodebaseType
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCasePyFile

CountUntypedParametersTest = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
def function_with_all_untyped(a, b, c):
    return a + b + c

def function_with_mixed_types(x: int, y, z: str):
    return f"{x}{y}{z}"

def function_with_all_typed(p: int, q: str, r: float):
    return f"{p}{q}{r}"

def function_with_no_params():
    return "No parameters"

class TestClass:
    def method_with_untyped(self, a, b):
        return a + b

    def method_with_typed(self, x: int, y: int):
        return x + y

def function_with_default_values(a, b=2, c: int = 3):
    return a + b + c

def function_with_args_kwargs(*args, **kwargs):
    pass
""",
            filepath="test_functions.py",
        ),
        SkillTestCasePyFile(
            input="""
from typing import List, Dict

def complex_function(a: int, b: List[str], c, d: Dict[str, int], e):
    return a, b, c, d, e

class AnotherClass:
    def __init__(self, x, y: float):
        self.x = x
        self.y = y

    def method(self, z):
        return z
""",
            filepath="more_functions.py",
        ),
    ],
    sanity=True,
)


@skill(
    prompt="""Generate a Python code snippet that counts the number of untyped parameters in all functions across all
    files in a codebase. The code should initialize a counter to zero, iterate through each file in the codebase,
    and for each file, iterate through its functions. For each function, it should check the parameters and increment
    the counter for each parameter that is not typed. Finally, the code should print the total count of untyped
    parameters found.""",
    guide=True,
    uid="aa884b82-0da2-4126-a7b9-64dcc5bb35ba",
)
class CountUntypedParameters(Skill, ABC):
    """Counts the number of untyped parameters across all functions in the codebase. It iterates through each file
    and each function, summing up the parameters that lack type annotations. Finally, it prints the total count of
    untyped parameters found.
    """

    @staticmethod
    @skill_impl(test_cases=[CountUntypedParametersTest], language=ProgrammingLanguage.PYTHON)
    def skill_func(codebase: CodebaseType):
        untitled_parameters_count = 0

        # Iterate through all files in the codebase
        for file in codebase.files:
            # Iterate through all functions in the file
            for function in file.functions:
                # Count the number of parameters that are not typed
                untitled_parameters_count += sum(1 for param in function.parameters if not param.is_typed)

        print(f"Found {untitled_parameters_count} untyped parameters in the codebase.")
