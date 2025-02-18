from abc import ABC

from codegen.sdk.core.codebase import PyCodebaseType, TSCodebaseType
from codegen.sdk.core.function import Function
from codegen.sdk.core.import_resolution import Import
from codegen.sdk.core.statements.if_block_statement import IfBlockStatement
from codegen.sdk.python.statements.with_statement import WithStatement
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCasePyFile, SkillTestCaseTSFile

py_feature_flag_def = """
ROLLED_OUT_FLAG_TO_DELETE = False
"""
py_input = """
from dir.enums import ROLLED_OUT_FLAG_TO_DELETE

def main():
    if ROLLED_OUT_FLAG_TO_DELETE:
        print("Feature is enabled")
        print("Does a thing when feature is enabled")
    else:
        print("Feature is disabled")
        print("Does a thing when feature is disabled")

    if not ROLLED_OUT_FLAG_TO_DELETE:
        print("Feature is disabled")
        print("Does a thing when feature is disabled")
    else:
        print("Feature is enabled")
        print("Does a thing when feature is enabled")

    with ROLLED_OUT_FLAG_TO_DELETE:
        print("Feature is enabled")
        print("Does a thing when feature is enabled")
"""
py_output = """
def main():
    print("Feature is enabled")
    print("Does a thing when feature is enabled")

    print("Feature is enabled")
    print("Does a thing when feature is enabled")

    print("Feature is enabled")
    print("Does a thing when feature is enabled")
"""

ts_feature_flag_def = """
export const ROLLED_OUT_FLAG_TO_DELETE = false;
"""
ts_input = """
import { ROLLED_OUT_FLAG_TO_DELETE } from './dir/enums';

function main(): void {
    if (ROLLED_OUT_FLAG_TO_DELETE) {
        console.log("Feature is enabled");
        console.log("Does a thing when feature is enabled");
    } else {
        console.log("Feature is disabled");
        console.log("Does a thing when feature is disabled");
    }

    if (!ROLLED_OUT_FLAG_TO_DELETE) {
        console.log("Feature is disabled");
        console.log("Does a thing when feature is disabled");
    } else {
        console.log("Feature is enabled");
        console.log("Does a thing when feature is enabled");
    }

    if (ROLLED_OUT_FLAG_TO_DELETE) {
        console.log("Feature is enabled");
        console.log("Does a thing when feature is enabled");
    }
}
"""
ts_output = """
function main(): void {
    console.log("Feature is enabled");
    console.log("Does a thing when feature is enabled");

    console.log("Feature is enabled");
    console.log("Does a thing when feature is enabled");

    console.log("Feature is enabled");
    console.log("Does a thing when feature is enabled");
}
"""
py_files = [SkillTestCasePyFile(input=py_input, output=py_output), SkillTestCasePyFile(input=py_feature_flag_def, output=py_feature_flag_def, filepath="dir/enums.py")]
ts_files = [SkillTestCaseTSFile(input=ts_input, output=ts_output), SkillTestCaseTSFile(input=ts_feature_flag_def, output=ts_feature_flag_def, filepath="dir/enums.ts")]


@skill(eval_skill=False, prompt="Delete a fully rolled out feature flag and simplify related code", uid="5f3fe71f-a31f-4c0d-83f8-0f6c49a1c3a8")
class DeleteRolledOutFeatureFlagSkill(Skill, ABC):
    """Locates a fully rolled out feature flag that has changed from a default value of False to True,
    and deletes all uses of the flag assuming the flag value is True. This skill simplifies
    conditional statements and removes unnecessary imports related to the feature flag.
    """

    @staticmethod
    @skill_impl([SkillTestCase(files=py_files)], language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: PyCodebaseType):
        """Implements the feature flag deletion for Python codebases."""
        feature_flag = codebase.get_symbol("ROLLED_OUT_FLAG_TO_DELETE")
        feature_flag_name = feature_flag.name

        # Iterate over all usages of the feature flag import
        for usage_symbol in feature_flag.symbol_usages:
            if isinstance(usage_symbol, Function):
                # Check statements within the function
                for statement in usage_symbol.code_block.get_statements():
                    if isinstance(statement, IfBlockStatement) and feature_flag_name in statement.condition.source:
                        # Simplify the condition of the if statement
                        statement.reduce_condition(bool_condition=feature_flag_name == statement.condition.source)
                    elif isinstance(statement, WithStatement) and feature_flag_name in statement.clause.source:
                        # Unwrap the with statement block
                        statement.code_block.unwrap()
            if isinstance(usage_symbol, Import):
                # Remove the import of the feature flag
                usage_symbol.remove()

    @staticmethod
    @skill_impl([SkillTestCase(files=ts_files)], language=ProgrammingLanguage.TYPESCRIPT)
    def typescript_skill_func(codebase: TSCodebaseType):
        """Implements the feature flag deletion for TypeScript codebases."""
        feature_flag = codebase.get_symbol("ROLLED_OUT_FLAG_TO_DELETE")
        feature_flag_name = feature_flag.name

        # Iterate over all usages of the feature flag import
        for usage_symbol in feature_flag.symbol_usages:
            if isinstance(usage_symbol, Function):
                # Check statements within the function
                for statement in usage_symbol.code_block.get_statements():
                    if isinstance(statement, IfBlockStatement) and feature_flag_name in statement.condition.source:
                        # Simplify the condition of the if statement
                        statement.reduce_condition(bool_condition=feature_flag_name == statement.condition.source)
            elif isinstance(usage_symbol, Import):
                # Remove the import of the feature flag
                usage_symbol.remove()
