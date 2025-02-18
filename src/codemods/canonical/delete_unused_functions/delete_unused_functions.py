from codegen.sdk.core.codebase import Codebase
from codegen.sdk.writer_decorators import canonical
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codemods.codemod import Codemod
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill


@skill(
    canonical=True,
    prompt="""Generate a Python codemod that deletes all unused functions from a codebase. The codemod should iterate through each file in the codebase, check for
top-level functions, and remove any function that has no usages or call-sites. Ensure that the implementation follows best practices for identifying
unused functions.""",
    uid="4024ceb5-54de-49de-b8f5-122ca2d3a6ee",
)
@canonical
class DeleteUnusedFunctionsCodemod(Codemod, Skill):
    """This Codemod deletes all functions that are not used in the codebase (no usages).
    In general, when deleting unused things, it's good practice to check both usages and call-sites, even though
    call-sites should be basically a subset of usages (every call-site should correspond to a usage).
    This is not always the case, however, so it's good to check both.
    """

    language = ProgrammingLanguage.PYTHON

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.PYTHON)
    def execute(self, codebase: Codebase) -> None:
        for file in codebase.files:
            # Iterate over top-level functions in the file
            for function in file.functions:
                # Check conditions: function has no usages/call-sites
                if not function.usages:
                    # Remove the function from the codebase when it has no call sites
                    function.remove()
