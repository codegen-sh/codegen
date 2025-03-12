from abc import ABC

from codegen.sdk.core.codebase import CodebaseType
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCasePyFile

CountUnnamedKeywordArgumentsTest = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
def function_with_kwargs(**kwargs):
    pass

def function_with_args_and_kwargs(*args, **kwargs):
    pass

def regular_function(a, b, c):
    pass

# Function calls with unnamed kwargs
function_with_kwargs(1, 2, 3)
function_with_args_and_kwargs(1, 2, x=3, y=4)
regular_function(1, 2, 3)

# Function calls with named kwargs
function_with_kwargs(a=1, b=2, c=3)
function_with_args_and_kwargs(1, 2, x=3, y=4)
regular_function(a=1, b=2, c=3)

# Mixed function calls
function_with_kwargs(1, b=2, c=3)
function_with_args_and_kwargs(1, 2, 3, x=4, y=5)
""",
            filepath="test_kwargs.py",
        ),
        SkillTestCasePyFile(
            input="""
def another_function(x, y, **kwargs):
    pass

# More function calls
another_function(1, 2, 3, 4, z=5)
another_function(x=1, y=2, a=3, b=4)
""",
            filepath="more_kwargs.py",
        ),
        SkillTestCasePyFile(
            input="""
class TestClass:
    def method_with_kwargs(self, **kwargs):
        pass

    def method_with_args_and_kwargs(self, *args, **kwargs):
        pass

# Instance creation and method calls
obj = TestClass()
obj.method_with_kwargs(1, 2, c=3)
obj.method_with_args_and_kwargs(1, 2, x=3, y=4)
""",
            filepath="class_kwargs.py",
        ),
    ],
    sanity=True,
)


@skill(
    prompt="""Generate a Python code snippet that counts the total number of unnamed keyword arguments (kwargs) in a
    codebase. The code should initialize a counter for unnamed kwargs, iterate through all files in the codebase,
    and for each file, iterate through all function calls. For each function call, check if any arguments are unnamed
    and update the counter accordingly. Finally, print the total count of unnamed kwargs.""",
    guide=True,
    uid="ed6b65ef-f92c-4c31-a8c9-9aac5a7df9e0",
)
class CountUnnamedKeywordArguments(Skill, ABC):
    """Counts the total number of unnamed keyword arguments in all function calls across all files in the codebase.
    It iterates through each file and each function call, checking for arguments that are not named, and accumulates
    the count. Finally, it prints the total number of unnamed keyword arguments found.
    """

    @staticmethod
    @skill_impl(test_cases=[CountUnnamedKeywordArgumentsTest], language=ProgrammingLanguage.PYTHON)
    def skill_func(codebase: CodebaseType):
        unnamed_kwargs_count = 0

        # Iterate through all files in the codebase
        for file in codebase.files:
            # Iterate through all function calls in the file
            for call in file.function_calls:
                # Check if the call has unnamed kwargs
                unnamed_kwargs_count += sum(1 for arg in call.args if arg.is_named is False)

        print(f"Total number of unnamed kwargs: {unnamed_kwargs_count}")
