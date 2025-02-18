from codegen.sdk.core.codebase import Codebase
from codegen.sdk.writer_decorators import canonical
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codemods.codemod import Codemod
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill


@skill(
    canonical=True,
    prompt="""Generate a Python codemod that iterates through all files in a codebase, identifies function parameters containing the substring 'obj', and renames
them to 'new_obj'. The codemod should be structured as a class that inherits from Codemod and Skill, with an execute method that performs the
renaming operation.""",
    uid="1576b2fd-8a00-44e4-9659-eb0f585e015a",
)
@canonical
class RenameFunctionParameters(Codemod, Skill):
    """This takes all functions that renames any parameter that contains 'obj' and replaces with 'new_obj'"""

    language = ProgrammingLanguage.PYTHON

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.PYTHON)
    def execute(self, codebase: Codebase) -> None:
        # Iterate over all files
        for file in codebase.files:
            for function in file.functions:
                # Search for parameter names that contain 'obj'
                params_to_rename = [p for p in function.parameters if "obj" in p.name]
                if params_to_rename:
                    # Rename the parameters
                    for param in params_to_rename:
                        new_param_name = param.name.replace("obj", "new_obj")
                        param.rename(new_param_name)
