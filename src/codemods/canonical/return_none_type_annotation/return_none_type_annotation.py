from codegen.sdk.core.codebase import Codebase
from codegen.sdk.writer_decorators import canonical
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codemods.codemod import Codemod
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill


@skill(
    canonical=True,
    prompt="""Generate a Python codemod that iterates through all functions and methods in a codebase. For each function or method that lacks return statements and
a return type annotation, set the return type to 'None'. Ensure the implementation handles both standalone functions and methods within classes.""",
    uid="fcac16ed-a915-472a-9dfe-1562452d9ab3",
)
@canonical
class ReturnNoneTypeAnnotation(Codemod, Skill):
    """This codemod sets the return type of functions that do not have any return statements"""

    language = ProgrammingLanguage.PYTHON

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.PYTHON)
    def execute(self, codebase: Codebase) -> None:
        # Iterate over all functions in the codebase
        for function in codebase.functions:
            # Look at ones that do not have return statements and no return type annotation
            if len(function.return_statements) == 0 and not function.return_type:
                # Set the return type to None
                function.set_return_type("None")

        # Do the same for methods (have to call it `cls`, not `class`, since `class` is a reserved keyword)
        for cls in codebase.classes:
            for method in cls.methods:
                # Look at ones that do not have return statements and no return type annotation
                if len(method.return_statements) == 0 and not method.return_type:
                    # Set the return type to None
                    method.set_return_type("None")
