from abc import ABC

from codegen.sdk.core.codebase import CodebaseType
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCasePyFile, SkillTestCaseTSFile

CountLargeFilesPyTest = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="\n".join([f"# Line {i}" for i in range(1, 1002)]),
            filepath="large_file1.py",
        ),
        SkillTestCasePyFile(
            input="\n".join([f"# Line {i}" for i in range(1, 1501)]),
            filepath="large_file2.py",
        ),
        SkillTestCasePyFile(
            input="\n".join([f"# Line {i}" for i in range(1, 501)]),
            filepath="small_file1.py",
        ),
        SkillTestCasePyFile(
            input="\n".join([f"# Line {i}" for i in range(1, 1000)]),
            filepath="edge_case_file.py",
        ),
        SkillTestCasePyFile(
            input="# Single line file",
            filepath="single_line_file.py",
        ),
    ],
    sanity=True,
)

CountLargeFilesTSTest = SkillTestCase(
    [
        SkillTestCaseTSFile(
            input="\n".join([f"// Line {i}" for i in range(1, 1201)]),
            filepath="large_file.ts",
        ),
        SkillTestCaseTSFile(
            input="\n".join([f"// Line {i}" for i in range(1, 801)]),
            filepath="medium_file.ts",
        ),
        SkillTestCaseTSFile(
            input="\n".join([f"// Line {i}" for i in range(1, 1001)]),
            filepath="edge_case_file.ts",
        ),
        SkillTestCaseTSFile(
            input="// Single line file",
            filepath="single_line_file.ts",
        ),
    ],
    sanity=True,
)


@skill(
    prompt="""Create a dictionary mapping file paths to their respective line
    counts from a codebase. The code should then count how many files exceed a specified line threshold (set to 1000)
    and print the number of large files.""",
    guide=True,
    uid="af988874-e349-4711-88a7-e7e2fa968cc6",
)
class CountLargeFiles(Skill, ABC):
    """Counts the number of files in a codebase that exceed a specified line threshold. It creates a dictionary
    mapping file paths to their respective line counts, then sums the number of files that have more lines than the
    defined threshold (1000 lines). Finally, it prints the total count of large files.
    """

    @staticmethod
    @skill_impl(test_cases=[CountLargeFilesPyTest], language=ProgrammingLanguage.PYTHON)
    @skill_impl(test_cases=[CountLargeFilesTSTest], language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType):
        file_to_lines = {}
        for file in codebase.files:
            file_to_lines[file.filepath] = file.end_point[0]

        LINE_THRESHOLD = 1000
        large_file_count = sum(1 for lines in file_to_lines.values() if lines > LINE_THRESHOLD)

        print(f"Number of large files: {large_file_count}")
