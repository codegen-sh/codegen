from abc import ABC

from codegen.sdk.core.codebase import CodebaseType
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCasePyFile, SkillTestCaseTSFile

# Test cases for appending to list
test_cases_append_py = [
    SkillTestCase(files=[SkillTestCasePyFile(input="a=[1]", output="a=[1, 2]")]),
    SkillTestCase(files=[SkillTestCasePyFile(input="a=[1, 3]", output="a=[1, 3, 2]")]),
    SkillTestCase(files=[SkillTestCasePyFile(input="a=[]", output="a=[2]")]),
]

test_cases_append_ts = [
    SkillTestCase(files=[SkillTestCaseTSFile(input="const a = [1];", output="const a = [1, 2];")]),
    SkillTestCase(files=[SkillTestCaseTSFile(input="const a = [];", output="const a = [2];")]),
    SkillTestCase(files=[SkillTestCaseTSFile(input="const a = [0, 1];", output="const a = [0, 1, 2];")]),
]


@skill(prompt="Append 2 to the assignment value of the global var a (which is a list)", uid="7eee6ffb-1e2a-488a-8a3e-fddee5d600b5")
class AppendToGlobalList(Skill, ABC):
    """Skill to append 2 to global list variable 'a'."""

    @staticmethod
    @skill_impl(test_cases_append_py, language=ProgrammingLanguage.PYTHON)
    @skill_impl(test_cases_append_ts, language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType):
        """Append 2 to the global list variable 'a' in Python."""
        a = codebase.get_symbol("a")
        a.value.append("2")


# Test cases for removing from list
test_cases_remove_py = [
    SkillTestCase(files=[SkillTestCasePyFile(input="a=[1]", output="a=[1]")]),
    SkillTestCase(files=[SkillTestCasePyFile(input="a=[1, 3, 2]", output="a=[1, 3]")]),
    SkillTestCase(files=[SkillTestCasePyFile(input="a=[1, 2, 3]", output="a=[1, 3]")]),
    SkillTestCase(files=[SkillTestCasePyFile(input="a=[]", output="a=[]")]),
    SkillTestCase(files=[SkillTestCasePyFile(input="a=[2]", output="a=[]")]),
]

test_cases_remove_ts = [
    SkillTestCase(files=[SkillTestCaseTSFile(input="const a = [1];", output="const a = [1];")]),
    SkillTestCase(files=[SkillTestCaseTSFile(input="const a = [1, 3, 2];", output="const a = [1, 3];")]),
    SkillTestCase(files=[SkillTestCaseTSFile(input="const a = [1, 2, 3];", output="const a = [1, 3];")]),
    SkillTestCase(files=[SkillTestCaseTSFile(input="const a = [];", output="const a = [];")]),
    SkillTestCase(files=[SkillTestCaseTSFile(input="const a = [2];", output="const a = [];")]),
]


@skill(prompt="Remove 2 from the assignment value of the global var a (which is a list)", uid="1d184606-7efb-4f29-84f8-5af3ad923a57")
class RemoveFromGlobalList(Skill, ABC):
    """Skill to remove 2 from global list variable 'a'."""

    @staticmethod
    @skill_impl(test_cases_remove_py, language=ProgrammingLanguage.PYTHON)
    @skill_impl(test_cases_remove_ts, language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType):
        """Remove 2 from the global list variable 'a'"""
        a = codebase.get_symbol("a", optional=True)
        assert a, "Symbol 'a' not found"
        new_value = [int(val.source) for val in a.value if val.source != "2"]
        a.set_value(str(new_value))


# Test cases for clearing the list
test_cases_clear_py = [
    SkillTestCase(files=[SkillTestCasePyFile(input="a=[1]", output="a=[]")]),
    SkillTestCase(files=[SkillTestCasePyFile(input="a=[1, 3, 2]", output="a=[]")]),
    SkillTestCase(files=[SkillTestCasePyFile(input="a=[]", output="a=[]")]),
]

test_cases_clear_ts = [
    SkillTestCase(files=[SkillTestCaseTSFile(input="const a = [1];", output="const a = [];")]),
    SkillTestCase(files=[SkillTestCaseTSFile(input="const a = [1, 3, 2];", output="const a = [];")]),
    SkillTestCase(files=[SkillTestCaseTSFile(input="const a = [];", output="const a = [];")]),
]


@skill(prompt="Clear the list stored in a symbol named `a`", uid="16ace5eb-b66c-43ef-8ed5-5726f0e02001")
class ClearGlobalList(Skill, ABC):
    """Skill to clear global list variable 'a'."""

    @staticmethod
    @skill_impl(test_cases_clear_py, language=ProgrammingLanguage.PYTHON)
    @skill_impl(test_cases_clear_ts, language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType):
        """Clear the global list variable 'a'"""
        a = codebase.get_symbol("a")
        a.value.clear()
