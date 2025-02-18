from codegen.sdk.core.codebase import Codebase
from codegen.sdk.writer_decorators import canonical
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codemods.codemod import Codemod
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill


@skill(
    canonical=True,
    prompt="""Generate a codemod in TypeScript that wraps all instances of the JSX element <Button /> with <Alert> in a codebase. The codemod should import the
Alert component and ensure that the resulting structure is:<br/><Alert><Button /></Alert>. Iterate through all files and functions in the codebase,
checking for JSX function components and modifying the relevant elements accordingly.""",
    uid="216569d7-5c95-4cf0-bfd8-5b121c1e47cd",
)
@canonical
class WrapWithComponentCodemod(Codemod, Skill):
    """Wraps certain JSX elements with another component. Imports the component symbol.

    In particular, this:
        <Button />

    gets updated to:

        <Alert>
            <Button />
        </Alert>
    """

    language = ProgrammingLanguage.TYPESCRIPT

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.TYPESCRIPT)
    def execute(self, codebase: Codebase) -> None:
        # Get the Alert component
        alert = codebase.get_symbol("Alert")

        # Iterate over all files in the codebase
        for file in codebase.files:
            # Iterate over all functions in the file
            for function in file.functions:
                # Check if this is a JSX function component
                if function.is_jsx:
                    # Iterate over all JSX elements in the function
                    for element in function.jsx_elements:
                        # Check if the JSX element is a Button component
                        if element.name == "Button":
                            # Wrap the Typography component with the Alert component
                            element.edit(f"<Alert>{element.source}</Alert>")

                            # Add an import for the Alert component
                            file.add_symbol_import(alert)
