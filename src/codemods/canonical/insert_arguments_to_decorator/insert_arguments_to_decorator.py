from codegen.sdk.core.codebase import Codebase
from codegen.sdk.writer_decorators import canonical
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codemods.codemod import Codemod
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill


@skill(
    canonical=True,
    prompt="""Generate a Python codemod that iterates through a codebase, identifying all instances of the `@app.function` decorator. For each decorator, check if
the `cloud` and `region` arguments are present. If they are missing, append `cloud='aws'` and `region='us-east-1'` to the decorator's arguments.
Ensure that the modifications are made only when the arguments are not already included.""",
    uid="de868e09-796c-421b-9efd-151f94f08aef",
)
@canonical
class InsertArgumentsToDecorator(Codemod, Skill):
    """This codemod inserts the cloud and region arguments to every app.function decorator.
    it decides whether to insert the arguments based on whether they are already present in the decorator.
    if they are not present, it inserts them.
    for example:

    -@app.function(image=runner_image, secrets=[modal.Secret.from_name("aws-secret")])
    +@app.function(image=runner_image, secrets=[modal.Secret.from_name("aws-secret")], cloud="aws", region="us-east-1")

    """

    language = ProgrammingLanguage.PYTHON

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.PYTHON)
    def execute(self, codebase: Codebase) -> None:
        # Iterate over all files in the codebase
        for file in codebase.files:
            # Iterate over all functions in each file
            for function in file.functions:
                # Check each decorator for the function
                for decorator in function.decorators:
                    # Identify decorators that are app.function and modify them
                    if decorator.source.startswith("@app.function("):
                        # Parse the existing decorator to add or update the cloud and region parameters
                        # Check if 'cloud' and 'region' are already in the decorator
                        if "cloud=" not in decorator.source:
                            decorator.call.args.append('cloud="aws"')
                        if "region=" not in decorator.source:
                            decorator.call.args.append('region="us-east-1"')
