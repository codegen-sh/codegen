from codegen.sdk.core.codebase import CodebaseType
from codegen.sdk.writer_decorators import canonical
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codemods.codemod import Codemod
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill


@skill(
    canonical=True,
    prompt="""Generate a Python codemod that iterates through all classes in a codebase, identifies subclasses of Enum, and moves them to a designated enums.py
file. Ensure that the codemod checks if the class is already in the correct file, flags it for movement if necessary, and creates the enums.py file if
it does not exist.""",
    uid="55bc76e5-15d2-4da6-bac1-59b408a59be7",
)
@canonical
class EnumMover(Codemod, Skill):
    """This codemod moves all enums (Enum subclasses) to a designated enums.py file within the same directory of the
    file they're defined in. It ensures that the enums are moved to the correct file and creates the enums.py file if
    it does not exist. Furthermore, it flags the class for movement which is necessary for splitting up the
    modifications into separate pull requests.
    """

    language = ProgrammingLanguage.PYTHON

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.PYTHON)
    def execute(self, codebase: CodebaseType):
        # Iterate over all classes in the codebase
        for cls in codebase.classes:
            # Check if the class is a subclass of Enum
            if cls.is_subclass_of("Enum"):
                # Determine the target file path for enums.py
                target_filepath = "/".join(cls.file.filepath.split("/")[:-1]) + "/enums.py"

                # Check if the current class is already in the correct enums.py file
                if cls.file.filepath.endswith("enums.py"):
                    continue

                # Flag the class for potential movement
                flag = codebase.flag_instance(symbol=cls)
                if codebase.should_fix(flag):
                    # Check if the enums.py file exists, if not, create it
                    if not codebase.has_file(target_filepath):
                        enums_file = codebase.create_file(target_filepath, "")
                    else:
                        enums_file = codebase.get_file(target_filepath)

                    # Move the enum class to the enums.py file
                    cls.move_to_file(enums_file)
