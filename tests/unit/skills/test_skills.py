import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from tests.shared.skills.skill_implementation import SkillImplementation
from tests.shared.skills.skill_test import SkillTestCase
from tests.shared.skills.utils import get_all_skill_implementations
from tests.shared.skills.verify_skill_output import verify_skill_output

skill_implementations = get_all_skill_implementations()
cases = [(skill, test_case, idx) for skill in skill_implementations for idx, test_case in enumerate(skill.test_cases) if not skill.external]


# @pytest.pytestmark.skip(reason="AI skill testing")
@pytest.mark.parametrize("skill, test_case", [(skill, case) for skill, case, _ in cases], ids=[skill.name + f"-{skill.language.name}-case-{case.name or idx}" for skill, case, idx in cases])
def test_all_example_skills(tmpdir, skill: SkillImplementation, test_case: SkillTestCase, snapshot):
    with get_codebase_session(tmpdir=tmpdir, programming_language=skill.language, files=test_case.to_input_dict(), verify_output=False, verify_input=False) as codebase:
        skill._skill_func(codebase)
        codebase.commit()
        verify_skill_output(codebase, skill, test_case, get_diff=False, snapshot=snapshot)
