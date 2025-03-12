import logging
import textwrap

from codegen.sdk.core.codebase import PyCodebaseType
from codegen.sdk.writer_decorators import canonical
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codemods.codemod import Codemod
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill

logger = logging.getLogger(__name__)


@skill(
    canonical=True,
    prompt="""Generate a Python codemod that migrates class attributes from a source class named 'RequestResetPassword' to a destination class named
'UserGroupsSettingsControlPanel'. The migrated attributes should be made private in the source class by renaming them with a leading underscore.
Additionally, create a hybrid property for each migrated attribute in the source class, including getter and setter methods that manage the private
attribute and maintain a copy in the source class.""",
    uid="739061ae-4f4f-48eb-a825-7424417ce540",
)
@canonical
class MigrateClassAttributes(Codemod, Skill):
    """Migrates class attributes from a source class to another class.
    Any migrated attributes are made private in the source class.
    """

    language = ProgrammingLanguage.PYTHON

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.PYTHON)
    def execute(self, codebase: PyCodebaseType) -> None:
        # Get the source and destination classes
        source_class = codebase.get_class("RequestResetPassword")
        dest_class = codebase.get_class("UserGroupsSettingsControlPanel")
        dest_attr_names = [x.name for x in dest_class.attributes]

        # Iterate over all attributes in the source class
        for attribute in source_class.attributes(private=False):
            # Skip attributes that are already added
            if attribute.name in dest_attr_names:
                continue

            # Add the attribute to the destination class (and bring its dependencies with it)
            dest_class.add_attribute(attribute, include_dependencies=True)

            # Make this attribute private (_name) in the source class
            attribute.rename(f"_{attribute.name}")

            # Add a "shadow copy write" to the source class
            return_type = attribute.assignment.type.source if attribute.assignment.type else "None"
            source_class.add_attribute_from_source(f"""{attribute.name} = hybrid_property(fget=get_{attribute.name}, fset=set_{attribute.name})""")
            source_class.methods.append(
                textwrap.dedent(f"""
    def get_{attribute.name}(self) -> {return_type}:
        return self._{attribute.name}

    def set_{attribute.name}(self, value: str) -> None:
        self._{attribute.name} = value
        self.copy.{attribute.name} = value
    """)
            )
