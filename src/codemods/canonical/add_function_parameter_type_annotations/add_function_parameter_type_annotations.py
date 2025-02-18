from codegen.sdk.core.codebase import Codebase
from codegen.sdk.writer_decorators import canonical
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codemods.codemod import Codemod
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill


@skill(
    canonical=True,
    prompt="""Generate a Python codemod that adds type annotations for function parameters named 'db' to be of type 'SessionLocal' from 'app.db'. The codemod should
also ensure that the necessary import statement is added if it is not already present. Include examples of the code before and after the
transformation.""",
    uid="d62a3590-14ef-4759-853c-39c5cf755ce5",
)
@canonical
class AddFunctionParameterTypeAnnotations(Codemod, Skill):
    """Adds type annotation for function parameters that takes in a 'db' parameter, which is a `SessionLocal` from `app.db`.
    It also adds the necessary import if not already present.

    Before:
    ```
        def some_function(db):
            pass
    ```

    After:
    ```
        from app.db import SessionLocal

        def some_function(db: SessionLocal):
            pass
    ```
    """

    language = ProgrammingLanguage.PYTHON

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.PYTHON)
    def execute(self, codebase: Codebase) -> None:
        # Iterate over all functions in the codebase
        for function in codebase.functions:
            # Check each parameter of the function
            for param in function.parameters:
                # Identify parameters named 'db'
                if param.name == "db":
                    # Change the type annotation to 'SessionLocal'
                    param.set_type_annotation("SessionLocal")
                    # Ensure the necessary import is present
                    file = function.file
                    if "SessionLocal" not in [imp.name for imp in file.imports]:
                        file.add_import_from_import_string("from app.db import SessionLocal")
