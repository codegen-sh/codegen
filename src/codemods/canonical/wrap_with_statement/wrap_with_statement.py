from codegen.sdk.core.codebase import Codebase
from codegen.sdk.writer_decorators import canonical
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codemods.codemod import Codemod
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill


@skill(
    canonical=True,
    prompt="""Generate a Python codemod that wraps the code blocks of all internally marked functions (those starting with an underscore) in a codebase with a
'with' statement using 'before_execute() as before'. The codemod should iterate through all Python files in the codebase and apply the wrapping to the
relevant functions.""",
    uid="345deafc-ac72-4537-8d13-ff27ac6e67f1",
)
@canonical
class WrapWithStatement(Codemod, Skill):
    """Wraps code blocks (that meet certain criteria) with a with statement.

    Before:

        def _table_name_from_select_element(elt):
            t = elt.forms[0]
            return t.name

    After:

        def _table_name_from_select_element(elt):
            with before_execute() as before:
                t = elt.forms[0]
                return t.name
    """

    language = ProgrammingLanguage.PYTHON

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.PYTHON)
    def execute(self, codebase: Codebase) -> None:
        # Iterate over all Python files in the codebase
        for file in codebase.files:
            # Search for specific function calls that need to be refactored
            for function in file.functions:
                # Find any internally marked function
                if function.name.startswith("_"):
                    function.code_block.wrap(before_src="with before_execute() as before:")
