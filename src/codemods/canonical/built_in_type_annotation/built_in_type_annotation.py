from codegen.sdk.core.codebase import Codebase
from codegen.sdk.writer_decorators import canonical
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codemods.codemod import Codemod
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill


@skill(
    canonical=True,
    prompt="""Generate a Python codemod that replaces type annotations from the typing module with their corresponding built-in types. The codemod should iterate
through all files in a codebase, check for imports from the typing module, remove those imports, and replace any usages of typing.List, typing.Dict,
typing.Set, and typing.Tuple with list, dict, set, and tuple respectively.""",
    uid="b2cd98af-d3c5-4e45-b396-e7abf06df924",
)
@canonical
class BuiltInTypeAnnotation(Codemod, Skill):
    """Replaces type annotations using typing module with builtin types.

    Examples:
        typing.List -> list
        typing.Dict -> dict
        typing.Set -> set
        typing.Tuple -> tuple
    """

    language = ProgrammingLanguage.PYTHON

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.PYTHON)
    def execute(self, codebase: Codebase) -> None:
        import_replacements = {"List": "list", "Dict": "dict", "Set": "set", "Tuple": "tuple"}
        # Iterate over all files in the codebase
        for file in codebase.files:
            # Iterate over all imports in the file
            for imported in file.imports:
                # Check if the import is from the typing module and is a builtin type
                if imported.module == "typing" and imported.name in import_replacements:
                    # Remove the type import
                    imported.remove()
                    # Iterate over all symbols that use this imported module
                    for usage in imported.usages:
                        # Replace the usage with the builtin type
                        if usage.match.source == imported.name:
                            usage.match.edit(import_replacements[imported.name])
