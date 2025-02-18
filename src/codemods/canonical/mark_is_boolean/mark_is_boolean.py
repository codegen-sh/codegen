from codegen.sdk.core.codebase import Codebase
from codegen.sdk.writer_decorators import canonical
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codemods.codemod import Codemod
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill


@skill(
    canonical=True,
    prompt="""Generate a TypeScript codemod that renames function parameters of boolean type that do not start with 'is'. The codemod should iterate through all
files in a codebase, check each function's parameters, and if a parameter is boolean and does not start with 'is', it should be renamed to start with
'is' followed by the capitalized parameter name. Additionally, all function calls using the old parameter name should be updated to use the new name.""",
    uid="e848b784-c703-4f4f-bfa4-e3876b2468d1",
)
@canonical
class MarkIsBoolean(Codemod, Skill):
    """This (TypeScript) Codemod illustrates how to rename function parameters that are boolean types but do not start with 'is'.

    In a real application, you would probably also check for other valid prefixes, like `should` etc.
    """

    language = ProgrammingLanguage.TYPESCRIPT

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.TYPESCRIPT)
    def execute(self, codebase: Codebase) -> None:
        # Iterate over all files in the codebase
        for file in codebase.files:
            # Iterate over all functions in the file
            for function in file.functions:
                # Iterate over all parameters in each function
                for param in function.parameters:
                    # Check if the parameter is a boolean type
                    if param.type == "boolean" or param.default in ["true", "false"]:
                        # Check if the parameter name does not start with 'is'
                        if not param.name.startswith("is"):
                            # Generate the new parameter name
                            new_name = "is" + param.name.capitalize()
                            # Rename the parameter and update all usages
                            param.rename(new_name)
                            # Update all function calls with the new parameter name
                            for call in function.call_sites:
                                arg = call.get_arg_by_parameter_name(param.name)
                                if arg:
                                    arg.rename(new_name)
