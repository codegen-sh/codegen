from abc import ABC

from codegen.sdk.core.codebase import PyCodebaseType, TSCodebaseType
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCasePyFile, SkillTestCaseTSFile

py_function_input = """
def foo(a: int):
    pass
"""
py_function_output = """
def foo(a: int, b: int):
    pass
"""
py_function_empty_input = """
def foo():
    pass
"""
py_function_empty_output = """
def foo(b: int):
    pass
"""
py_test_cases = [
    SkillTestCase(files=[SkillTestCasePyFile(input=py_function_input, output=py_function_output)]),
    SkillTestCase(files=[SkillTestCasePyFile(input=py_function_empty_input, output=py_function_empty_output)]),
]

ts_function_input = """
function foo(a: number): void {
}
"""
ts_function_output = """
function foo(a: number, b: number): void {
}
"""
ts_function_empty_input = """
function foo(): void {
}
"""
ts_function_empty_output = """
function foo(b: number): void {
}
"""
ts_test_cases = [
    SkillTestCase(files=[SkillTestCaseTSFile(input=ts_function_input, output=ts_function_output)]),
    SkillTestCase(files=[SkillTestCaseTSFile(input=ts_function_empty_input, output=ts_function_empty_output)]),
]


@skill(eval_skill=False, prompt="Append a parameter to a function signature", uid="22cafc5b-c837-4f1a-836e-7fada2fe88d8")
class AppendParameterSkill(Skill, ABC):
    """Appends a parameter to the signature of a specified function in both Python and TypeScript codebases."""

    @staticmethod
    @skill_impl(py_test_cases, language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: PyCodebaseType):
        """Append a parameter to the function signature in Python"""
        foo = codebase.get_symbol("foo")
        foo.parameters.append("b: int")

    @staticmethod
    @skill_impl(ts_test_cases, language=ProgrammingLanguage.TYPESCRIPT)
    def typescript_skill_func(codebase: TSCodebaseType):
        """Append a parameter to the function signature in TypeScript"""
        foo = codebase.get_symbol("foo")
        foo.parameters.append("b: number")
