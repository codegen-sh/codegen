from codegen.sdk.core.codebase import Codebase
from codegen.sdk.writer_decorators import canonical
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codemods.codemod import Codemod
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill


@skill(
    canonical=True,
    prompt="""Generate a Python codemod that transforms class attributes initializing specific Session objects into decorators. The codemod should iterate through
all classes in a codebase, check for attributes with values 'NullSession' or 'SecureCookieSession', import the corresponding decorators, add them to
the class, and remove the original attributes. Ensure the decorators are imported from 'src.flask.sessions'.""",
    uid="b200fb43-dad4-4241-a0b2-75a6fbf5aca6",
)
@canonical
class ConvertAttributeToDecorator(Codemod, Skill):
    """This converts any class attributes that initializes a set of Session objects to a decorator.

    For example, before:

        class MySession(SessionInterface):
            session_class = NullSession
            ...

    After:
        @null_session
        class MySession(SessionInterface):
            ...

    That is, it deletes the attribute and adds the appropriate decorator via the `cls.add_decorator` method.
    Note that `cls.file.add_import_from_import_string(import_str)` is the method used to add import for the decorator.
    """

    language = ProgrammingLanguage.PYTHON

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.PYTHON)
    def execute(self, codebase: Codebase) -> None:
        attr_value_to_decorator = {
            "NullSession": "null_session",
            "SecureCookieSession": "secure_cookie_session",
        }
        # Iterate over all classes in the codebase
        for cls in codebase.classes:
            # Check if the class contains any targeted attributes
            for attribute in cls.attributes:
                if attribute.right is None:
                    continue

                if attribute.right.source in attr_value_to_decorator:
                    decorator_name = attr_value_to_decorator[attribute.right.source]
                    # Import the necessary decorators
                    required_import = f"from src.flask.sessions import {decorator_name}"
                    cls.file.add_import_from_import_string(required_import)

                    # Add the appropriate decorator
                    cls.add_decorator(f"@{decorator_name}")
                    # Remove the attribute
                    attribute.remove()
