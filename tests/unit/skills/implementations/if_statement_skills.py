from abc import ABC

from codegen.sdk.core.codebase import PyCodebaseType, TSCodebaseType
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCasePyFile, SkillTestCaseTSFile

py_if_input = """
def foo():
    if condition_to_set:
        print("condition_to_set is True")
    elif some_condition:
        print("some_condition is True")
    else:
        print("neither condition is True")
"""
py_if_output = """
def foo():
    print("condition_to_set is True")
    if some_condition:
        print("some_condition is True")
    else:
        print("neither condition is True")
"""
py_elif_input = """
def foo():
    if some_condition:
        print("some_condition is True")
    elif condition_to_set:
        print("condition_to_set is True")
    else:
        print("neither condition is True")
"""
py_elif_output = """
def foo():
    if some_condition:
        print("some_condition is True")
    print("condition_to_set is True")
"""
py_test_cases = [SkillTestCase(files=[SkillTestCasePyFile(input=py_if_input, output=py_if_output)]), SkillTestCase(files=[SkillTestCasePyFile(input=py_elif_input, output=py_elif_output)])]


ts_input1 = """
function foo(): void {
    if (conditionToSet) {
        console.log("condition_to_set is True");
    } else if (someCondition) {
        console.log("some_condition is True");
    } else {
        console.log("neither condition is True");
    }
}
"""
ts_output1 = """
function foo(): void {
    console.log("condition_to_set is True");
    if (someCondition) {
        console.log("some_condition is True");
    } else {
        console.log("neither condition is True");
    }
}
"""
ts_input2 = """
function foo(): void {
    if (someCondition) {
        console.log("some_condition is True");
    } else if (conditionToSet) {
        console.log("condition_to_set is True");
    } else {
        console.log("neither condition is True");
    }
}
"""
ts_output2 = """
function foo(): void {
    if (someCondition) {
        console.log("some_condition is True");
    }
    console.log("condition_to_set is True");
}
"""

ts_test_cases = [SkillTestCase(files=[SkillTestCaseTSFile(input=ts_input1, output=ts_output1)]), SkillTestCase(files=[SkillTestCaseTSFile(input=ts_input2, output=ts_output2)])]


@skill(eval_skill=False, prompt="Simplify if/else control flow by reducing specific conditions to True", uid="4df2f328-ab40-4298-9141-496293260d88")
class ReduceIfStatementConditionSkill(Skill, ABC):
    """Simplifies the if/else control flow by reducing conditions that are set to a specific value to True.
    This skill works for both Python and TypeScript codebases, with slight variations in the condition naming.
    """

    @staticmethod
    @skill_impl(py_test_cases, language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: PyCodebaseType):
        """Simplifies the if/else control flow by reducing conditions that are `condition_to_set` to True"""
        for file in codebase.files:
            for function in file.functions:
                for statement in function.code_block.if_blocks:
                    if statement.condition == "condition_to_set":
                        statement.reduce_condition(True)
                    for elif_block in statement.elif_statements:
                        if elif_block.condition == "condition_to_set":
                            elif_block.reduce_condition(True)

    @staticmethod
    @skill_impl(ts_test_cases, language=ProgrammingLanguage.TYPESCRIPT)
    def typescript_skill_func(codebase: TSCodebaseType):
        """Simplifies the if/else control flow by reducing conditions that are `conditionToSet` to True"""
        for file in codebase.files:
            for function in file.functions:
                for statement in function.code_block.if_blocks:
                    if statement.condition == "conditionToSet":
                        statement.reduce_condition(True)
                    for elif_block in statement.elif_statements:
                        if elif_block.condition == "conditionToSet":
                            elif_block.reduce_condition(True)
