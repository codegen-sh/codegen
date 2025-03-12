from codegen.sdk.core.codebase import Codebase
from codegen.sdk.writer_decorators import canonical
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codemods.codemod import Codemod
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill


@skill(
    canonical=True,
    prompt="""Generate a Python codemod that moves all enum classes from various files in a codebase to a single file named 'enums.py'. The codemod should check if
'enums.py' already exists in the current directory; if not, it should create it. For each enum class found, the codemod should move the class along
with its dependencies to 'enums.py' and add a back edge import to the original file.""",
    uid="47e9399c-b8d5-4f39-a5cf-fd40c51620b0",
)
@canonical
class MoveEnumsCodemod(Codemod, Skill):
    """Moves all enums to a file called enums.py in current directory if it doesn't already exist"""

    language = ProgrammingLanguage.PYTHON

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.PYTHON)
    def execute(self, codebase: Codebase) -> None:
        for file in codebase.files:
            if not file.name.endswith("enums.py"):
                for cls in file.classes:
                    # check if the class inherits from the Enum class
                    if cls.is_subclass_of("Enum"):
                        # generate the new filename for the enums.py file
                        new_filename = "/".join(file.filepath.split("/")[:-1]) + "/enums.py"

                        # check if the enums.py file exists
                        if not codebase.has_file(new_filename):
                            # if it doesn't exist, create a new file
                            dst_file = codebase.create_file(new_filename, "from enum import Enum\n\n")
                        else:
                            # if it exists, get a reference to the existing file
                            dst_file = codebase.get_file(new_filename)

                        # move the enum class and its dependencies to the enums.py file
                        # add a "back edge" import to the original file
                        cls.move_to_file(dst_file, include_dependencies=True, strategy="add_back_edge")
