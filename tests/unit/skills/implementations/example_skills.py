from abc import ABC

from codegen.sdk.core.codebase import CodebaseType
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCasePyFile

########################################################################################################################
# GLOBAL VARS
########################################################################################################################

test_cases = [
    SkillTestCase(files=[SkillTestCasePyFile(input="x = 1", output="x = 2")]),
    SkillTestCase([SkillTestCasePyFile(input="y = 1", output="y = 2")]),
]


@skill(eval_skill=False, prompt="Set the value of all global variables to 2 if their current assigned literal is 1", uid="917e6632-2a65-4879-8dcf-566645a65262")
class SetGlobalVarValueSkill(Skill, ABC):
    """This skill modifies the values of all global variables in the codebase, setting them to 2 if their current assigned value is 1."""

    @staticmethod
    @skill_impl(test_cases, language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: CodebaseType):
        """Set the value of all global variables to 2 if their current assigned literal is 1"""
        for file in codebase.files:
            for v in file.global_vars:
                if v.value == "1":
                    v.set_value("2")

    @staticmethod
    @skill_impl([], ignore=True)
    def typescript_skill_func(codebase: CodebaseType):
        """Not implemented for TypeScript"""
        ...


test_cases = [
    SkillTestCase(files=[SkillTestCasePyFile(input="x = 1", output="y = 1")]),
    SkillTestCase([SkillTestCasePyFile(input="y = 1", output="y = 1")]),
]


@skill(eval_skill=False, prompt="Rename all global variables named 'x' to 'y'", uid="540d32c1-223b-4b66-bebd-94ebbcd5dcb7")
class RenameGlobalVarSkill(Skill, ABC):
    """Renames all global variables named 'x' to 'y' across the codebase."""

    @staticmethod
    @skill_impl(test_cases, language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: CodebaseType):
        """Rename all global variables named 'x' to 'y'."""
        for file in codebase.files:
            for v in file.global_vars:
                if v.name == "x":
                    v.set_name("y")

    @staticmethod
    @skill_impl([], ignore=True)
    def typescript_skill_func(codebase: CodebaseType):
        """Not implemented for TypeScript"""
        ...


########################################################################################################################
# SKIP TESTS
########################################################################################################################

test_cases = [
    SkillTestCase(
        files=[
            SkillTestCasePyFile(
                input="""
def test_example():
    assert True

def not_a_test():
    pass

def test_another_example():
    assert 1 + 1 == 2
""",
                output="""import pytest

@pytest.mark.skip(reason="This is a test")
def test_example():
    assert True

def not_a_test():
    pass

@pytest.mark.skip(reason="This is a test")
def test_another_example():
    assert 1 + 1 == 2
""",
            )
        ]
    ),
    SkillTestCase(
        files=[
            SkillTestCasePyFile(
                input="""
class TestClass:
    def test_method(self):
        assert True

    def helper_method(self):
        pass

def test_function():
    assert False
""",
                output="""import pytest

class TestClass:
    @pytest.mark.skip(reason="This is a test")
    def test_method(self):
        assert True

    def helper_method(self):
        pass

@pytest.mark.skip(reason="This is a test")
def test_function():
    assert False
""",
            )
        ]
    ),
]


@skill(eval_skill=False, prompt="Add pytest.mark.skip decorator to all test functions with reason='This is a test'", uid="8a1da729-ba4c-4d2f-8f85-0d3a5477775e")
class SkipAllTests(Skill, ABC):
    """This skill adds a decorator to all test functions in the codebase, marking them to be skipped during test execution with a specified reason."""

    @staticmethod
    @skill_impl(test_cases, language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: CodebaseType):
        """Adds pytest.mark.skip decorator to all test functions with reason="This is a test"."""
        for file in codebase.files:
            for function in file.functions:
                if function.name.startswith("test_"):
                    file.add_import_from_import_string("import pytest")
                    function.add_decorator('@pytest.mark.skip(reason="This is a test")')

            for cls in file.classes:
                for method in cls.methods:
                    if method.name.startswith("test_"):
                        file.add_import_from_import_string("import pytest")
                        method.add_decorator('@pytest.mark.skip(reason="This is a test")')

    @staticmethod
    @skill_impl([], ignore=True)
    def typescript_skill_func(codebase: CodebaseType):
        """Not implemented for TypeScript"""
        ...


########################################################################################################################
# TYPE HINTS
########################################################################################################################

test_cases = [
    SkillTestCase(files=[SkillTestCasePyFile(input="def func(x):\n    print(x)", output="from typing import Any\ndef func(x: Any) -> None:\n    print(x)")]),
    SkillTestCase(files=[SkillTestCasePyFile(input="def greet(name):\n    return f'Hello, {name}'", output="from typing import Any\ndef greet(name: str) -> Any:\n    return f'Hello, {name}'")]),
]


@skill(eval_skill=False, prompt="Add trivial type hints to function parameters and return values", uid="ecc14909-a28d-4a53-88f0-a2e7bbb4c72c")
class AddTypeHintsSkill(Skill, ABC):
    """This skill adds type hints to function parameters and return values in a codebase, enhancing type safety and improving code readability."""

    @staticmethod
    @skill_impl(test_cases, language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: CodebaseType):
        """Adds type hints to function parameters and return values."""
        for function in codebase.functions:
            if not function.return_type:
                if len(function.return_statements) == 0:
                    function.set_return_type("None")
                else:
                    function.set_return_type("Any")
                    function.file.add_import_from_import_string("from typing import Any")

            for param in function.parameters:
                if not param.is_typed:
                    if param.name == "self" or param.name == "cls":
                        continue
                    elif param.name == "name":
                        param.set_type_annotation("str")
                    else:
                        param.set_type_annotation("Any")
                        function.file.add_import_from_import_string("from typing import Any")

    @staticmethod
    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.TYPESCRIPT)
    def typescript_skill_func(codebase: CodebaseType):
        """Not implemented for TypeScript"""
        """Adds type hints to function parameters and return values."""
        for function in codebase.functions:
            if not function.return_type:
                if len(function.return_statements) == 0:
                    function.set_return_type("null")
                else:
                    function.set_return_type("Any")

            for param in function.parameters:
                if not param.is_typed:
                    param.set_type_annotation("Any")


########################################################################################################################
# RENAMING
########################################################################################################################

old_file = """
class OldName:
    pass

def func(x):
    return OldName()
"""

new_file = """
class NewName:
    pass

def func(x):
    return NewName()
"""

test_cases = [
    SkillTestCase(files=[SkillTestCasePyFile(input=old_file, output=new_file)]),
]


@skill(eval_skill=False, prompt="Rename the class OldName to NewName", uid="5867f33c-436a-4f16-a3e2-70203798d8f5")
class RenameClassSkill(Skill, ABC):
    """Renames a specified class in the codebase from an old name to a new name."""

    @staticmethod
    @skill_impl(test_cases, language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: CodebaseType):
        """Rename the class OldName => NewName"""
        old_name = "OldName"
        new_name = "NewName"
        for file in codebase.files:
            for cls in file.classes:
                if cls.name == old_name:
                    cls.rename(new_name)

    @staticmethod
    @skill_impl([], ignore=True)
    def typescript_skill_func(codebase: CodebaseType):
        """Not implemented for TypeScript"""
        ...


########################################################################################################################
# REMOVING DEBUG PRINTS
########################################################################################################################

# TODO: this is broken!
# test_cases = [
#     SkillTestCase(files=[SkillTestCaseFile(input="print('debug')\nx = 5\nprint('debug')", output="x = 5")]),
#     SkillTestCase(files=[SkillTestCaseFile(input="print('debug: start')\nresult = compute()\nprint('debug: end')", output="result = compute()")]),
# ]
#
#
# @skill(test_cases)
# def remove_debug_prints_skill(codebase: CodebaseType):
#     """Removes all print statements that contain the word 'debug'."""
#     for file in codebase.files:
#         for function in file.functions:
#             calls = function.fucntion_calls
#             for call in calls:
#                 print(call)
#             statements_to_remove = []
#             for statement in function.code_block.statements:
#                 if isinstance(statement, FunctionCall) and statement.name == "print":
#                     for arg in statement.args:
#                         if "debug" in arg.value.lower():
#                             statements_to_remove.append(statement)
#                             break
#
#             for statement in statements_to_remove:
#                 statement.remove()


########################################################################################################################
# WRAPPING FUNCTIONS
########################################################################################################################

test_cases = [
    SkillTestCase(files=[SkillTestCasePyFile(input="def old_func():\n    pass", output="def old_func():\n    pass\n\ndef new_old_func():\n    return old_func()")]),
    SkillTestCase(
        files=[
            SkillTestCasePyFile(
                input="class MyClass:\n    def method(self):\n        pass",
                output="class MyClass:\n    def method(self):\n        pass\n    def new_method(self):\n        return self.method()",
            )
        ]
    ),
]


@skill(eval_skill=False, prompt="Add a trivial wrapper function called `new_{function.name}` around each function and class method", uid="f9478659-3fe4-4855-85b2-bb2a39ec4a47")
class AddWrapperFunctionSkill(Skill, ABC):
    """Adds a trivial wrapper function around each function and class method, creating a new function that simply calls the original function."""

    @staticmethod
    @skill_impl(test_cases, language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: CodebaseType):
        """Add a trivial wrapper function called `new_{function.name}` around each function and class method that just calls the original function."""
        for file in codebase.files:
            for function in file.functions:
                wrapper_name = f"new_{function.name}"
                wrapper_code = f"def {wrapper_name}():\n    return {function.name}()"
                file.add_symbol_from_source(wrapper_code)

            for cls in file.classes:
                for method in cls.methods:
                    wrapper_name = f"new_{method.name}"
                    wrapper_code = f"def {wrapper_name}(self):\n        return self.{method.name}()"
                    cls.add_source(wrapper_code)

    @staticmethod
    @skill_impl([], ignore=True)
    def typescript_skill_func(codebase: CodebaseType):
        """Not implemented for TypeScript"""
        ...


########################################################################################################################
# REMOVE UNUSED IMPORTS
########################################################################################################################

test_cases = [
    SkillTestCase(
        files=[
            SkillTestCasePyFile(
                input="""
import os
import sys

def foo():
    print("Hello, World!")
""",
                output="""
def foo():
    print("Hello, World!")
""",
            )
        ]
    )
]


@skill(eval_skill=False, prompt="Remove unused import statements from the code", uid="b1fbed63-1932-4434-854d-182202e74c70")
class RemoveUnusedImportsSkill(Skill, ABC):
    """Removes all unused import statements from the codebase, ensuring that only necessary imports are retained in each file."""

    @staticmethod
    @skill_impl(test_cases, language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: CodebaseType):
        """Removes unused import statements from the code."""
        for file in codebase.files:
            for imp in file.imports:
                if len(imp.usages) == 0:
                    imp.remove()

    @staticmethod
    @skill_impl([], ignore=True)
    def typescript_skill_func(codebase: CodebaseType):
        """Not implemented for TypeScript"""
        ...


########################################################################################################################
# ADD DOCSTRING
########################################################################################################################

test_cases = [
    SkillTestCase(
        files=[
            SkillTestCasePyFile(
                input="""
def foo():
    pass
""",
                output="""
def foo():
    \"\"\"This function does something.\"\"\"
    pass
""",
            )
        ]
    )
]


@skill(eval_skill=False, prompt="Add docstrings to all functions and methods", uid="bea814b1-b834-43a0-a6f5-bab146d1fd38")
class AddDocstringsSkill(Skill, ABC):
    """This skill adds docstrings to all functions and methods in a codebase, ensuring that each function has a descriptive comment explaining its purpose and functionality."""

    @staticmethod
    @skill_impl(test_cases, language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: CodebaseType):
        """Adds docstrings to all functions and methods."""
        for file in codebase.files:
            for function in file.functions:
                if function.docstring is None:
                    docstring = '"""This function does something."""'
                    function.set_docstring(docstring)

    @staticmethod
    @skill_impl([], ignore=True)
    def typescript_skill_func(codebase: CodebaseType):
        """Not implemented for TypeScript"""
        ...
