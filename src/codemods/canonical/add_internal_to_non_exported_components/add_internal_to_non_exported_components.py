from codegen.sdk.core.codebase import Codebase
from codegen.sdk.writer_decorators import canonical
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codemods.codemod import Codemod
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill


@skill(
    canonical=True,
    prompt="""Generate a codemod that iterates through a codebase and renames all non-exported React function components by appending 'Internal' to their names. The
codemod should check each function to determine if it is a JSX component and not exported, then rename it accordingly.""",
    uid="302d8f7c-c848-4020-9dea-30e8e622d709",
)
@canonical
class AddInternalToNonExportedComponents(Codemod, Skill):
    """This codemod renames all React function components that are not exported from their file to be suffixed with 'Internal'.

    Example:
    Before:
    ```
        const Inner = () => <div />;
        const Outer = () => <div><InnerComponent /></div>;
        export default Outer;
    ```
    After:
    ```
        const InnerInternal = () => <div />;
        const Outer = () => <div><InnerInternal /></div>;
        export default Outer;
    ```
    """

    language = ProgrammingLanguage.TYPESCRIPT

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.TYPESCRIPT)
    def execute(self, codebase: Codebase) -> None:
        # Iterate over all files
        for file in codebase.files:
            for function in file.functions:
                # Check if the function is a React component and is not exported
                if function.is_jsx and not function.is_exported:
                    # Rename the function to include 'Internal'
                    function.rename(f"{function.name}Internal")
