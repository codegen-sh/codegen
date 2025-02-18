from codegen.sdk.core.codebase import PyCodebaseType
from codegen.sdk.core.symbol_groups.dict import Dict
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCasePyFile

test_cases = [
    SkillTestCase(files=[SkillTestCasePyFile(input='a={"foo": "bar"}', output="a=Schema(foo=bar)")]),
    SkillTestCase(files=[SkillTestCasePyFile(input="a={}", output="a=Schema()")]),
    SkillTestCase([SkillTestCasePyFile(input='a={"foo": "bar", "baz":"hi"}', output="a=Schema(foo=bar, baz=hi)")]),
]


@skill(prompt="Please write a codemod that converts all dictionaries to Schema objects", uid="6ef2ffa5-94c3-42a1-84dd-da56ea41021b")
class DictToSchema(Skill):
    """Converts a dictionary into a Schema object. Converts the key value pairs into arguments for the constructor"""

    @staticmethod
    @skill_impl(test_cases, language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: PyCodebaseType):
        """Converts a dictionary into a Schema object. Converts the key value pairs into arguments for the constructor"""
        # iterate over all global vars
        for v in codebase.global_vars:
            # if the variable is a dictionary
            if isinstance(v.value, Dict):
                # convert it to a Schema object
                v.set_value(f"Schema({', '.join(f'{k}={v}' for k, v in v.value.items())})")
