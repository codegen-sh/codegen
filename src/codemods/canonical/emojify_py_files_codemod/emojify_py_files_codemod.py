from codegen.sdk.core.codebase import Codebase
from codegen.sdk.writer_decorators import canonical
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codemods.codemod import Codemod
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill


@skill(
    canonical=True,
    prompt="""Generate a Python codemod that iterates over all Python files in a codebase and adds a rainbow emoji comment at the beginning of each file. The
codemod should be implemented in the `execute` function of the `EmojifyPyFilesCodemod` class, which inherits from `Codemod` and `Skill`. Ensure that
the new content for each file starts with the comment '#ð' followed by the original content of the file.""",
    uid="5d8f1994-7f74-42e8-aaa8-0c41ced228ef",
)
@canonical
class EmojifyPyFilesCodemod(Codemod, Skill):
    """Trivial codemod to add a rainbow emoji in a comment at the beginning of all Python files."""

    language = ProgrammingLanguage.PYTHON

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.PYTHON)
    def execute(self, codebase: Codebase) -> None:
        # iterate over files
        for file in codebase.files:
            # add the rainbow emoji to the top of the file
            new_content = "#🌈" + "\n" + file.content
            file.edit(new_content)
