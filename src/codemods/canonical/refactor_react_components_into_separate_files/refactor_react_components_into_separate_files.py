from codegen.sdk.core.codebase import Codebase
from codegen.sdk.writer_decorators import canonical
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codemods.codemod import Codemod
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill


@skill(
    canonical=True,
    prompt="""Generate a Python function that refactors React components in a codebase. The function should iterate through all files, identify React function
components, and separate non-default exported components into new files. Ensure that the new files are named after the components and that all imports
are updated accordingly. Include necessary error handling and commit changes to the codebase after each move.""",
    uid="b64406f4-a670-4d65-8356-c6db25c4f4b7",
)
@canonical
class RefactorReactComponentsIntoSeparateFiles(Codemod, Skill):
    """This codemod breaks up JSX/TSX files by moving components that aren't exported by default
    into separate files.
    """

    language = ProgrammingLanguage.TYPESCRIPT

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.TYPESCRIPT)
    def execute(self, codebase: Codebase) -> None:
        # Iterate over all files in the codebase
        for file in codebase.files:
            # Find all React function components in the file
            react_components = [func for func in file.functions if func.is_jsx and func.name is not None]

            # Identify the default exported component
            default_component = next((comp for comp in react_components if comp.is_exported and comp.export.is_default_export()), None)
            if default_component is None:
                continue

            # Move non-default components to new files
            for component in react_components:
                if component != default_component and component in file.symbols:
                    # Create a new file for the component
                    new_file_path = "/".join(file.filepath.split("/")[:-1]) + "/" + component.name + ".tsx"
                    if not codebase.has_file(new_file_path):
                        new_file = codebase.create_file(new_file_path)

                        # Move the component to the new file and update all imports
                        component.move_to_file(new_file, strategy="update_all_imports")

                        # Commit is NECESSARY since subsequent steps depend on current symbol locations
                        codebase.commit()
