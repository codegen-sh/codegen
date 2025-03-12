from pathlib import Path

from codegen.sdk.core.codebase import Codebase
from codegen.sdk.writer_decorators import canonical
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codemods.codemod import Codemod
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill


@skill(
    canonical=True,
    prompt="""Generate a TypeScript codemod that marks functions as internal by adding the @internal tag to their docstrings. The codemod should check if a function
is only used within the same directory or subdirectory, ensuring it is not exported, re-exported, or overloaded. If the function's docstring does not
already contain the @internal tag, append it appropriately.""",
    uid="fe61add3-ab41-49ec-9c26-c2d13e2647d1",
)
@canonical
class MarkAsInternalCodemod(Codemod, Skill):
    """Mark all functions that are only used in the same directory or subdirectory as an internal function.
    To mark function as internal by adding the @internal tag to the docstring.
    """

    language = ProgrammingLanguage.TYPESCRIPT

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.TYPESCRIPT)
    def execute(self, codebase: Codebase) -> None:
        # Check if the caller and callee are in the same directory
        def check_caller_directory(caller_file: str, callee_file: str) -> bool:
            caller_path = Path(caller_file).resolve()
            callee_path = Path(callee_file).resolve()
            return str(caller_path).startswith(str(callee_path.parent))

        # Iterate over all the functions in the codebase
        for function in codebase.functions:
            # Ignore functions that are exported
            if function.is_exported:
                # Check if all usages of the function are in the same file
                if all([check_caller_directory(caller.file.filepath, function.file.filepath) for caller in function.symbol_usages]):
                    # Check if function is not re-exported
                    if not function.is_reexported and not function.is_overload:
                        # Check if function is not already marked as internal
                        docstring = function.docstring.text if function.docstring else ""
                        if "@internal" not in docstring:
                            # Add @internal to the docstring
                            if function.docstring:
                                function.set_docstring(f"{function.docstring.text}\n\n@internal")
                            else:
                                function.set_docstring("@internal")
