from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.external_module import ExternalModule
from codegen.sdk.python.class_definition import PyClass
from codegen.sdk.writer_decorators import canonical
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codemods.codemod import Codemod
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill


@skill(
    canonical=True,
    prompt="""Generate a Python codemod that converts all function calls in a codebase to use named keyword arguments if they have two or more positional arguments.
The codemod should iterate through all files and functions, checking each function call to determine if it meets the criteria for conversion. Ensure
that the conversion is skipped if all arguments are already named, if there are fewer than two arguments, if the function definition cannot be found,
if the function is a class without a constructor, or if the function is part of an external module.""",
    uid="1a4b9e66-1df5-4ad1-adbb-034976add8e0",
)
@canonical
class UseNamedKwargs(Codemod, Skill):
    """Converts all functions to use named kwargs if there are more than >= 2 args being used.

    In general you can use FunctionCall.convert_args_to_kwargs() once you have filtered properly
    """

    language = ProgrammingLanguage.PYTHON

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.PYTHON)
    def execute(self, codebase: Codebase) -> None:
        # Iterate over all files
        for file in codebase.files:
            # TODO: doesn't handle global function calls
            # Iterate over all functions
            for function in file.functions:
                # look at the function calls
                for call in function.function_calls:
                    # Skip if all args are already named
                    if all(arg.is_named for arg in call.args):
                        continue

                    # Skip if call sites has < 2 args
                    if len(call.args) < 2:
                        continue

                    # Skip if we can't find the def of the function
                    function_def = call.function_definition
                    if not function_def:
                        continue

                    # Skip if function_def is a class and the class has no constructor
                    if isinstance(function_def, PyClass) and not function_def.constructor:
                        continue

                    if isinstance(function_def, ExternalModule):
                        continue

                    call.convert_args_to_kwargs()
