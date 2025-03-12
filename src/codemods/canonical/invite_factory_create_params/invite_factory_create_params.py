from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.detached_symbols.function_call import FunctionCall
from codegen.sdk.writer_decorators import canonical
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codemods.codemod import Codemod
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill


@skill(
    canonical=True,
    prompt="""Generate a Python codemod that updates calls to `InviteFactory.create`, `InviteFactory.build`, and `InviteFactory(...)` to use the `invitee` parameter
instead of `invitee_id`, `invitee['email']`, or `invitee.id`. The codemod should iterate through all files in a codebase, find the relevant function
calls, and modify the arguments accordingly. Specifically, it should replace `invitee_id` with `invitee`, and adjust the value to remove `.id` or
`['email']` as needed.""",
    uid="1c43f274-e4bc-49c7-abca-8b273e9cad9a",
)
@canonical
class InviteFactoryCreateParams(Codemod, Skill):
    """This codemod updates calls to InviteFactory.create, InviteFactory.build and InviteFactory(...) to use the `invitee` parameter instead of `invitee_id`, `invitee["email"]`, or `invitee.id`.

    For example:

        InviteFactory.create(invitee_id=user_deleted_recently.id)

    Becomes:

        InviteFactory.create(invitee=user_deleted_recently)

    Note that this involves grabbing the function calls by using `file.find` and `file.search` to find the function calls, and then using `FunctionCall.from_usage` to create a `FunctionCall` object from the usage. This is because **the current version of GraphSitter does not support finding method usages**
    """  # noqa: E501

    language = ProgrammingLanguage.PYTHON

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.PYTHON)
    def execute(self, codebase: Codebase) -> None:
        # Iterate over all files
        for file in codebase.files:
            # Find invocations of InviteFactory.create and InviteFactory.build in the file
            usages = file.find("InviteFactory.create", exact=True)  # returns an Editable
            usages += file.find("InviteFactory.build", exact=True)
            usages += file.search(r"\bInviteFactory\(")

            # Iterate over all these function calls
            for usage in usages:
                # Create a function call from this `usage`
                function_call = FunctionCall.from_usage(usage)
                if function_call is None:
                    continue

                # Grab the invitee_id argument
                invitee_arg = function_call.get_arg_by_parameter_name("invitee_id")
                # If it exists...
                if invitee_arg:
                    # Grab the current value
                    arg_value = invitee_arg.value

                    # Replace the arg value with the correct value
                    if arg_value.endswith(".id"):
                        # replace `xyz.id` with `xyz`
                        invitee_arg.set_value(arg_value.replace(".id", ""))
                    elif arg_value.endswith('["email"]'):
                        # replace `xyz["email"]` with `xyz`
                        invitee_arg.set_value(arg_value.replace('["email"]', ""))
                    else:
                        continue

                    # Update the arg keyword from `invitee_id` => 'invitee'
                    invitee_arg.rename("invitee")
