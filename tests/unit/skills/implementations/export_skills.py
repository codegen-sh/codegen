from codegen.sdk.core.codebase import TSCodebaseType
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCaseTSFile

ts_input1 = """
export default A = function() {b()};
"""
ts_output1 = """
export const A = function() {b()};
"""
ts_input1_file2 = """
import A from "./foo";
"""
ts_output1_file2 = """
import { A } from "./foo";
"""
ts_input2 = """
function foo(): void {
}
export default foo;
"""
ts_output2 = """
function foo(): void {
}
export { foo };
"""

ts_input2_file2 = """
import foo from "./foo";
"""
ts_output2_file2 = """
import { foo } from "./foo";
"""
ts_input3 = """
function foo(): void {
}
export default foo;
"""
ts_output3 = """
function foo(): void {
}
export { foo };
"""

ts_input3_file2 = """
export { default } from "./foo";
"""
ts_output3_file2 = """
export { foo } from "./foo";
"""
ts_test_cases = [
    SkillTestCase(files=[SkillTestCaseTSFile(input=ts_input1, output=ts_output1, filepath="foo.ts"), SkillTestCaseTSFile(input=ts_input1_file2, output=ts_output1_file2)]),
    SkillTestCase(files=[SkillTestCaseTSFile(input=ts_input2, output=ts_output2, filepath="foo.ts"), SkillTestCaseTSFile(input=ts_input2_file2, output=ts_output2_file2)]),
    SkillTestCase(files=[SkillTestCaseTSFile(input=ts_input3, output=ts_output3, filepath="foo.ts"), SkillTestCaseTSFile(input=ts_input3_file2, output=ts_output3_file2)]),
]


@skill(eval_skill=False, prompt="Convert default exports to named exports in TypeScript", uid="3351e6bb-df30-4552-9768-d908f56e6ed4")
class ExportSkills(Skill):
    """Convert default exports to named exports in TypeScript"""

    @staticmethod
    @skill_impl(ts_test_cases, language=ProgrammingLanguage.TYPESCRIPT)
    def typescript_skill_func(codebase: TSCodebaseType):
        """Convert default exports to named exports in TypeScript"""
        for file in codebase.files:
            for export in file.exports:
                export.make_non_default()
