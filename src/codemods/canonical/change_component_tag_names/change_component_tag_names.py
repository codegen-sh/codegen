from codegen.sdk.core.codebase import Codebase
from codegen.sdk.writer_decorators import canonical
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codemods.codemod import Codemod
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill


@skill(
    canonical=True,
    prompt="""Generate a codemod that updates all instances of the JSX element <PrivateRoute> to <PrivateRoutesContainer> within React components in a TypeScript
codebase. Ensure that the new component is imported if it is not already present. The codemod should check for the existence of the
<PrivateRoutesContainer> component and raise an error if it is not found.""",
    uid="ab5879e3-e3ea-4231-b928-b756473f290d",
)
@canonical
class ChangeJSXElementName(Codemod, Skill):
    """This codemod updates specific JSX elements inside of React components

    In particular, this:
        <>
            <PrivateRoute>test</PrivateRoute>
            <PrivateRoute />
        </>

    gets updated to:
        <>
            <PrivateRoutesContainer>test</PrivateRoutesContainer>
            <PrivateRoutesContainer />
        </>

    Inside of all React components in the codebase.
    """

    language = ProgrammingLanguage.TYPESCRIPT

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.TYPESCRIPT)
    def execute(self, codebase: Codebase):
        # Grab the NewName component
        PrivateRoutesContainer = codebase.get_symbol("PrivateRoutesContainer", optional=True)
        if PrivateRoutesContainer is None or not PrivateRoutesContainer.is_jsx:
            msg = "PrivateRoutesContainer component not found in codebase"
            raise ValueError(msg)

        # Iterate over all functions in the codebase
        for file in codebase.files:
            # Iterate over each function in the file
            for function in file.functions:
                # Check if the function is a React component
                if function.is_jsx:
                    # Iterate over all JSXElements in the React component
                    for element in function.jsx_elements:
                        # Check if the element named improperly
                        if element.name == "PrivateRoute":
                            # Update the JSXElement's name
                            element.set_name("PrivateRoutesContainer")
                            # Add the import if it doesn't exist
                            if not file.has_import("PrivateRoutesContainer"):
                                file.add_symbol_import(PrivateRoutesContainer)
