from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.expressions import Type
from codegen.sdk.core.expressions.generic_type import GenericType
from codegen.sdk.core.expressions.union_type import UnionType
from codegen.sdk.writer_decorators import canonical
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codemods.codemod import Codemod
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill


@skill(
    canonical=True,
    prompt="""Generate a Python codemod that updates type annotations in a codebase. The codemod should replace instances of 'Optional[X]' with 'X | None' and
handle other generic types and unions appropriately. Ensure that the codemod iterates through all files, processes functions and methods, checks for
typed parameters, and modifies their annotations as needed. Additionally, include an import statement for future annotations if any changes are made.""",
    uid="0e2d60db-bff0-4020-bda7-f264ff6c7f46",
)
@canonical
class UpdateOptionalTypeAnnotations(Codemod, Skill):
    """Replaces type annotations with builtin ones, e.g.:
        def f(x: Optional[int]):
    becomes
        def f(x: int | None):
    """

    language = ProgrammingLanguage.PYTHON

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.PYTHON)
    def execute(self, codebase: Codebase) -> None:
        def update_type_annotation(type: Type) -> str:
            if "Optional" in type.source:
                if isinstance(type, GenericType):
                    if type.name == "Optional":
                        return update_type_annotation(type.parameters[0]) + " | None"
                    else:
                        return f"{type.name}[{', '.join(update_type_annotation(param) for param in type.parameters)}]"
                if isinstance(type, UnionType):
                    return " | ".join(update_type_annotation(param) for param in type)
            return type.source

        # Iterate over all files in the codebase
        for file in codebase.files:
            # Process standalone functions and methods within classes
            for function in file.functions + [method for cls in file.classes for method in cls.methods]:
                # Iterate over all parameters in the function
                if function.parameters:
                    for parameter in function.parameters:
                        if parameter.is_typed:
                            # Check if the parameter has a type annotation
                            new_type = update_type_annotation(parameter.type)
                            if parameter.type != new_type:
                                # Add the future annotations import
                                file.add_import_from_import_string("from __future__ import annotations\n")
                                parameter.type.edit(new_type)
