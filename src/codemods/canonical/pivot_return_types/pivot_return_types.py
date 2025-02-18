from codegen.sdk.core.codebase import Codebase
from codegen.sdk.writer_decorators import canonical
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codemods.codemod import Codemod
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill


@skill(
    canonical=True,
    prompt="""Generate a Python codemod that transforms all functions returning a string type to return a custom FastStr type instead. The codemod should iterate
through the codebase, check for functions with a return type of 'str', update the return type to 'FastStr', add the necessary import statement for
FastStr, and modify all return statements to wrap the returned value in the FastStr constructor.""",
    uid="a357f5c4-2ff0-4fb2-a5c6-be051428604a",
)
@canonical
class PivotReturnTypes(Codemod, Skill):
    """This codemod allows us to take all functions that return str and safely convert it to a custom FastStr type.
    It does so by wrapping the return statement value in the CustomStr constructor and update the return type annotation.

    def f() -> str:
        ...
        return content

    Becomes

    def f() -> FastStr:
        ...
        return FastStr(str=content)
    """

    language = ProgrammingLanguage.PYTHON

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.PYTHON)
    def execute(self, codebase: Codebase) -> None:
        # Iterate over all functions in the codebase
        for function in codebase.functions:
            # Check if the function's return type annotation is 'str'
            if (return_type := function.return_type) and return_type.source == "str":
                # Update the return type to 'FastStr'
                function.set_return_type("FastStr")

                # Add import for 'FastStr' if it doesn't exist
                function.file.add_import_from_import_string("from app.models.fast_str import FastStr")

                # Modify all return statements within the function
                for return_stmt in function.code_block.return_statements:
                    # Wrap return statements with FastStr constructor
                    return_stmt.set_value(f"FastStr(str={return_stmt.value})")
