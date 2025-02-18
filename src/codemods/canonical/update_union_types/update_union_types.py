from codegen.sdk.core.codebase import Codebase
from codegen.sdk.writer_decorators import canonical
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codemods.codemod import Codemod
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill


@skill(
    canonical=True,
    prompt="""Generate a Python codemod that updates type annotations from the old Union[x, y] syntax to the new x | y syntax for migration from Python 3.9 to
Python 3.10. The codemod should iterate through all files in a codebase, check for imports of Union from typing, and replace occurrences of Union in
both generic type and subscript forms. Ensure that the new syntax is correctly formatted, handling cases with multiple types and removing any empty
strings from trailing commas.""",
    uid="7637d11a-b907-4716-a09f-07776f81a359",
)
@canonical
class UpdateUnionTypes(Codemod, Skill):
    """This updates the Union [ x , y ] syntax for x | y for migrations for python 3.9 to python 3.10"""

    language = ProgrammingLanguage.PYTHON

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.PYTHON)
    def execute(self, codebase: Codebase) -> None:
        for file in codebase.files:
            # Check if the file imports Union from typing
            if "Union" in [imp.name for imp in file.imports]:
                # Search for Union type annotations in the file
                for editable in file.find("Union["):
                    if editable.ts_node_type == "generic_type":
                        new_type = editable.source.replace("Union[", "").replace("]", "", 1).replace(", ", " | ")
                        editable.replace(editable.source, new_type)
                    elif editable.ts_node_type == "subscript":
                        # Handle subscript case (like TypeAlias = Union[...])
                        types = editable.source[6:-1].split(",")
                        # Remove any empty strings that might result from trailing commas
                        types = [t.strip() for t in types if t.strip()]
                        new_type = " | ".join(types)
                        if len(types) > 1:
                            new_type = f"({new_type})"
                        editable.replace(editable.source, new_type)
