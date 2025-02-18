from codegen.sdk.core.codebase import Codebase
from codegen.sdk.writer_decorators import canonical
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codemods.codemod import Codemod
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill


@skill(
    canonical=True,
    prompt="""Generate a TypeScript codemod that converts all `className='...'` props in JSX elements to use backticks. The codemod should iterate through all files
in a codebase, identify JSX components, and for each JSX element, check its props. If a prop is named `className` and its value is not already wrapped
in curly braces, replace the quotes with backticks, updating the prop value accordingly.""",
    uid="bf22f4d7-a93a-458f-be78-470c24487d4c",
)
@canonical
class ClassNamesToBackTick(Codemod, Skill):
    """This Codemod converts all `classNames="..."` props in JSX elements to use backticks.

    Example:
    Before:
        <div className="text-red-500" />

    After:
        <div className={`text-red-500`} />

    """

    language = ProgrammingLanguage.TYPESCRIPT

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.TYPESCRIPT)
    def execute(self, codebase: Codebase) -> None:
        # Iterate over all files in the codebase
        for file in codebase.files:
            # Check if the file is likely to contain JSX elements (commonly in .tsx files)
            for function in file.functions:
                # Check if the function is a JSX component
                if function.is_jsx:
                    # Iterate over all JSX elements in the function
                    for element in function.jsx_elements:
                        # Access the props of the JSXElement
                        for prop in element.props:
                            # Check if the prop is named 'className'
                            if prop.name == "className":
                                # Get the current value of the prop
                                if not prop.value.startswith("{"):
                                    # Replace single or double quotes with backticks
                                    new_value = "{`" + prop.value.strip("\"'") + "`}"
                                    # Update the attribute value
                                    prop.set_value(new_value)
