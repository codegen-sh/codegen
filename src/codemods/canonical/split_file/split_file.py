from codegen.sdk.core.codebase import Codebase
from codegen.sdk.writer_decorators import canonical
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codemods.codemod import Codemod
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill


@skill(
    canonical=True,
    prompt="""Generate a Python codemod that splits a large file by moving all subclasses of 'Enum' from 'sqlglot/optimizer/scope.py' to a new file named
'sqlglot/optimizer/enums.py'. The codemod should check if the large file exists, raise a FileNotFoundError if it does not, and then create the new
file before iterating through the classes in the large file to move the relevant subclasses.""",
    uid="a7c7388d-f473-4a37-b316-e881079fe093",
)
@canonical
class SplitFile(Codemod, Skill):
    """This codemod moves symbols from one large to a new file with the goal of breaking up a large file."""

    language = ProgrammingLanguage.PYTHON

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.PYTHON)
    def execute(self, codebase: Codebase):
        # Grab large file to split
        file = codebase.get_file("sqlglot/optimizer/scope.py", optional=True)
        if file is None:
            msg = "The file `sqlglot/optimizer/scope.py` was not found."
            raise FileNotFoundError(msg)

        # Create a new file for storing all our 'Enum' classes
        new_file = codebase.create_file("sqlglot/optimizer/enums.py")

        # iterate over all classes
        for cls in file.classes:
            # Check inheritance
            if cls.is_subclass_of("Enum"):
                # Move symbol
                cls.move_to_file(new_file)
