import re

from codegen.sdk.core.codebase import TSCodebaseType
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCaseTSFile

# Case 1: all rules disabled in a SINGLE line comment are no longer required - should remove entire comment
ts_case_1_input = """
// eslint-disable-next-line @typescript-eslint/no-explicit-any
"""
ts_case_1_output = """
"""
ts_case_1 = SkillTestCase(name="single_line_comment_all_rules", files=[SkillTestCaseTSFile(input=ts_case_1_input, output=ts_case_1_output)])

# Case 2: some rules disabled in a SINGLE line comment are no longer required - should just remove required rules from comment
ts_case_2_input = """
// eslint-disable-next-line @typescript-eslint/consistent-type-assertions, @typescript-eslint/no-explicit-any
"""
ts_case_2_output = """
// eslint-disable-next-line @typescript-eslint/consistent-type-assertions
"""
ts_case_2 = SkillTestCase(name="single_line_comment_some_rules", files=[SkillTestCaseTSFile(input=ts_case_2_input, output=ts_case_2_output)])

# Case 3: all rules disabled in a MULTI line comment are no longer required - should remove entire comment
ts_case_3_input = """
/* eslint-disable-next-line @typescript-eslint/no-explicit-any */
"""
ts_case_3_output = """
"""
ts_case_3 = SkillTestCase(name="multi_line_comment_all_rules", files=[SkillTestCaseTSFile(input=ts_case_3_input, output=ts_case_3_output)])

# Case 4: some rules disabled in a MULTI line comment are no longer required - should just remove required rules from comment
ts_case_4_input = """
/* eslint-disable-next-line @typescript-eslint/consistent-type-assertions, @typescript-eslint/no-explicit-any */
"""
ts_case_4_output = """
/* eslint-disable-next-line @typescript-eslint/consistent-type-assertions */
"""
ts_case_4 = SkillTestCase(name="multi_line_comment_some_rules", files=[SkillTestCaseTSFile(input=ts_case_3_input, output=ts_case_3_output)])

ts_test_cases = [ts_case_1, ts_case_2, ts_case_3, ts_case_4]


@skill(eval_skill=False, prompt="Remove eslint disable comments in TypeScript", uid="3619c21c-6460-4925-acec-2f8dd4871991")
class EslintCommentSkill(Skill):
    """Remove eslint disable comments for an eslint rule.
    This is useful if a codebase is making an eslint rule either not required or reducing it to warning level.
    If the rule is no longer required/warning level, the disable comments are also no longer required and can be cleaned up.
    """

    @staticmethod
    @skill_impl(ts_test_cases, language=ProgrammingLanguage.TYPESCRIPT)
    def typescript_skill_func(codebase: TSCodebaseType):
        ESLINT_RULE = "@typescript-eslint/no-explicit-any"

        # Iterate over all files in the codebase
        for file in codebase.files:
            # Iterate over all comment statements in the file
            for comment in file.code_block.comments:
                if "eslint-disable" in comment.source:
                    pattern = r"(.*eslint-disable(?:-next-line?)?)(?:\s+([@a-z-\/,\s]+))?(.*)"
                    match = re.search(pattern, comment.source)
                    if not match:
                        continue

                    rules = [r.strip() for r in match.group(2).split(",")]
                    if ESLINT_RULE in rules:
                        # Case: the only rule being disabled is the one being de-activated. Delete whole comment
                        if len(rules) == 1:
                            print(f"Deleting comment: {comment.source}")
                            comment.remove()
                        # Case: multiples rules are being disabled. Remove just ESLINT_RULE from the comment
                        else:
                            print(f"Removing {ESLINT_RULE} from comment: {comment.source}")
                            rules.remove(ESLINT_RULE)
                            new_comment_source = f"{match.group(1)} {', '.join(rules)}{match.group(3)}"
                            comment.edit(new_comment_source)
