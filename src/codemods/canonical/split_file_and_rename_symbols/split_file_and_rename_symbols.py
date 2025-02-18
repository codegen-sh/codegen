from codegen.sdk.core.codebase import CodebaseType
from codegen.sdk.writer_decorators import canonical
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codemods.codemod import Codemod
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill


@skill(
    canonical=True,
    prompt="""Generate a Python codemod that splits a file by moving classes containing 'Configuration' to a new file named 'configuration.py'. After moving, commit
the changes to ensure the new classes are recognized. Then, rename all 'Configuration' classes in the new file to 'Config'. Finally, update the
original file's path from 'types.py' to 'schemas.py'.""",
    uid="816415d9-27e8-4228-b284-1b18b3072f0d",
)
@canonical
class SplitFileAndRenameSymbols(Codemod, Skill):
    """Split file and rename moved symbols

    This codemod first moves several symbols to new files and then renames them.

    This requires a codebase.commit() call between the move and the rename step.
    """

    language = ProgrammingLanguage.PYTHON

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.PYTHON)
    def execute(self, codebase: CodebaseType):
        # Get file to split up
        source_file = codebase.get_file("redash/models/types.py", optional=True)
        if source_file is None:
            msg = "[1] The file `redash/models/types.py` was not found."
            raise FileNotFoundError(msg)

        # Get file symbols will be moved to
        configuration_file = codebase.create_file("redash/models/configuration.py")

        # Move all the classes that contain with `Configuration` to the new configuration file
        for cls in source_file.classes:
            # Move the `_filter` functions
            if "Configuration" in cls.name:
                # Move the function to the filters file and rename it
                # move_to_file should also take care of updating the imports of the functions, and bringing over any imports or local references the function needs
                cls.move_to_file(configuration_file, include_dependencies=True, strategy="update_all_imports")

        # Commit is NECESSARY for the codebase graph to be aware of the new classes moved into configuration file
        codebase.commit()

        # re-acquire the configuration file with the latest changes
        configuration_file = codebase.get_file("redash/models/configuration.py")

        # rename all the `Configuration` classes to `Config`
        for cls in configuration_file.classes:
            if cls.name == "Configuration":
                cls.rename("Config")

        # re-acquire the source file with the latest changes
        source_file = codebase.get_file("redash/models/types.py")
        source_file.update_filepath("redash/models/schemas.py")
