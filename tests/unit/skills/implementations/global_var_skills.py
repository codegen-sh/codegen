from abc import ABC

from codegen.sdk.core.codebase import PyCodebaseType, TSCodebaseType
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCasePyFile, SkillTestCaseTSFile

########################################################################################################################
# Py test cases
########################################################################################################################
py_file_1 = """
from app.utils.logger import get_logger

logger = get_logger(__name__)
"""

py_file_1_output = """
from app.utils.logger import get_logger

"""

py_file_2 = """
from app.utils.logger import get_logger

logger = get_logger(__name__)
logger.info("Hello, World!")
"""

py_file_2_output = """
from app.utils.logger import get_logger

logger = get_logger(__name__)
logger.info("Hello, World!")
"""

py_test_cases = [
    SkillTestCase(
        files=[
            SkillTestCasePyFile(filepath="test_1.py", input=py_file_1, output=py_file_1_output),
            SkillTestCasePyFile(filepath="test_2.py", input=py_file_2, output=py_file_2_output),
        ]
    ),
]


########################################################################################################################
# TS test cases
########################################################################################################################

ts_file_1 = """
import { getLogger } from "./logger";

const logger = getLogger();
"""

ts_file_1_output = """
import { getLogger } from "./logger";

"""

ts_file_2 = """
import { getLogger } from "./logger";

const logger = getLogger();
logger.info("Hello, World!");
"""

ts_file_2_output = """
import { getLogger } from "./logger";

const logger = getLogger();
logger.info("Hello, World!");
"""

ts_test_cases = [
    SkillTestCase(
        files=[
            SkillTestCaseTSFile(filepath="test_1.ts", input=ts_file_1, output=ts_file_1_output),
            SkillTestCaseTSFile(filepath="test_2.ts", input=ts_file_2, output=ts_file_2_output),
        ]
    ),
]


@skill(eval_skill=False, prompt="Remove unused logger variables from the codebase", uid="b7afa336-744f-4a97-8ffa-dc0b331433e5")
class DeleteUnusedLoggerSkill(Skill, ABC):
    """Removes all global variables that are defined as logger instances if they are unused.
    This skill works for both Python and TypeScript codebases, with slight variations in the
    logger initialization pattern.
    """

    @staticmethod
    @skill_impl(py_test_cases, language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: PyCodebaseType):
        """Remove all global variables that are defined as `logger = get_logger(__name__)` if they are unused"""
        for file in codebase.files:
            for var in file.global_vars:
                if var.name == "logger" and var.value == "get_logger(__name__)" and not var.usages:
                    var.remove()

    @staticmethod
    @skill_impl(ts_test_cases, language=ProgrammingLanguage.TYPESCRIPT)
    def typescript_skill_func(codebase: TSCodebaseType):
        """Remove all global variables that are defined as `logger = getLogger()` if they are unused"""
        for file in codebase.files:
            for var in file.global_vars:
                if var.name == "logger" and var.value == "getLogger()" and not var.usages:
                    var.remove()
