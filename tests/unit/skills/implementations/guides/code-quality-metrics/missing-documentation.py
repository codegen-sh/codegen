from abc import ABC

from codegen.sdk.core.codebase import CodebaseType
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCasePyFile

AutoDocstringGeneratorTest = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
def function_with_docstring():
    '''This function already has a docstring.'''
    return "Hello, World!"

def function_without_docstring():
    return "This function needs a docstring."

class ExampleClass:
    def method_with_docstring(self):
        '''This method already has a docstring.'''
        pass

    def method_without_docstring(self):
        pass

def complex_function(a, b, c):
    '''This function has a docstring but complex logic.'''
    result = 0
    for i in range(a):
        for j in range(b):
            result += i * j * c
    return result

def another_function_without_docstring(x, y):
    return x + y

print("Start of output")
""",
            filepath="example.py",
        ),
        SkillTestCasePyFile(
            input="""
def standalone_function():
    # This function is in a separate file and needs a docstring
    return "I'm standalone!"
""",
            filepath="standalone.py",
        ),
    ],
    sanity=True,
)


@skill(
    prompt="""Generate a Python code snippet that iterates over all functions in a codebase, checks if each function
    has a docstring, and if not, generates a docstring using an AI model. The code should keep track of the number of
    functions that were missing docstrings and print the total count at the end.""",
    guide=True,
    uid="9bee4333-5465-4aaf-8865-a6da2cae3ec7",
)
class AutoDocstringGenerator(Skill, ABC):
    """This code snippet iterates over all functions in a codebase to check for missing docstrings. If a function is
    found without a docstring, it generates a new docstring using an AI model based on the function's source code and
    sets it for the function. The snippet also counts the number of functions that were missing docstrings and prints
    the total count after processing.
    """

    @staticmethod
    @skill_impl(test_cases=[AutoDocstringGeneratorTest], skip_test=True, language=ProgrammingLanguage.PYTHON)
    def skill_func(codebase: CodebaseType):
        functions_without_docstring = 0
        # Iterate over all functions in the codebase
        for function in codebase.functions:
            # Check if the function has a docstring
            if function.docstring is None:
                # Generate a docstring for the function
                new_docstring = codebase.ai(f"Generate a docstring for the function {function.name} with the following content:\n{function.source}", target=function)
                function.set_docstring(new_docstring)
                functions_without_docstring += 1

        print(f"Found and fixed {functions_without_docstring} functions without a docstring")
