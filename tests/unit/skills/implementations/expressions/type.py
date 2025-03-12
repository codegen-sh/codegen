from typing import TYPE_CHECKING

from codegen.sdk.core.codebase import CodebaseType
from codegen.sdk.core.expressions.union_type import UnionType
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCasePyFile, SkillTestCaseTSFile

if TYPE_CHECKING:
    from codegen.sdk.python.assignment import PyAssignment
    from codegen.sdk.typescript.assignment import TSAssignment

test_cases_append_py = [
    SkillTestCase(files=[SkillTestCasePyFile(input="a: int | None", output="a: int | None | str")]),
    SkillTestCase(files=[SkillTestCasePyFile(input="a: str | None", output="a: str | None")]),
    SkillTestCase(files=[SkillTestCasePyFile(input="a: int | str | None", output="a: int | str | None")]),
]

test_cases_append_ts = [
    SkillTestCase(files=[SkillTestCaseTSFile(input="let a: number | null", output="let a: number | null | string")]),
    SkillTestCase(files=[SkillTestCaseTSFile(input="let a: string | null", output="let a: string | null")]),
    SkillTestCase(files=[SkillTestCaseTSFile(input="let a: number | string | null", output="let a: number | string | null")]),
]


@skill(eval_skill=False, prompt="Add an additional type to a union type", uid="ffa7a5ac-ef6c-4801-9865-bb302449ac2a")
class AppendTypeToUnionTypeSkill(Skill):
    """Appends an additional 'str' type to a piped union type in Python"""

    @staticmethod
    @skill_impl(test_cases_append_py, language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: CodebaseType):
        """If the type of 'a' is a UnionType, append "str" to it if it doesn't already exist"""
        a: PyAssignment = codebase.get_symbol("a")
        if isinstance(a.type, UnionType):
            if "str" not in a.type:
                a.type.append("str")

    @staticmethod
    @skill_impl(test_cases_append_ts, language=ProgrammingLanguage.TYPESCRIPT)
    def typescript_skill_func(codebase: CodebaseType):
        """If the type of 'a' is a UnionType, append "str" to it if it doesn't already exist"""
        a: TSAssignment = codebase.get_symbol("a")
        if isinstance(a.type, UnionType):
            if "string" not in a.type:
                a.type.append("string")


built_in_type_input = """
from typing import Dict, List, Set, Tuple


def fn(a: List[List[Tuple[int, Set[int]]]]) -> Dict[str, str]:
    pass
"""
built_in_type_output = """
def fn(a: list[list[tuple[int, set[int]]]]) -> dict[str, str]:
    pass
"""


@skill(eval_skill=False, prompt="Convert typing.Type to built-in type in Python", uid="f3059b5b-4d0b-49e1-bb15-1581931534a4")
class ConvertToBuiltInTypeSkill(Skill):
    """Replaces type annotations using typing module with builtin types.

    Examples:
        typing.List -> list
        typing.Dict -> dict
        typing.Set -> set
        typing.Tuple -> tuple
    """

    @staticmethod
    @skill_impl([SkillTestCase(files=[SkillTestCasePyFile(input=built_in_type_input, output=built_in_type_output)])], language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: CodebaseType):
        """Replaces type annotations using typing module with builtin types."""
        import_replacements = {"List": "list", "Dict": "dict", "Set": "set", "Tuple": "tuple"}

        # Iterate over all imports in the codebase
        for imported in codebase.imports:
            # Check if the import is from the typing module and is a builtin type
            if imported.module == "typing" and imported.name in import_replacements:
                # Remove the type import
                imported.remove()
                # Iterate over all symbols that use this imported module
                for symbol in imported.symbol_usages:
                    # Find all exact matches (Editables) in the symbol with this imported module
                    for usage in symbol.find(imported.name, exact=True):
                        # Replace the usage with the builtin type
                        usage.edit(import_replacements[imported.name])

    @staticmethod
    @skill_impl([], language=ProgrammingLanguage.TYPESCRIPT, ignore=True)
    def typescript_skill_func(codebase: CodebaseType):
        """The typing package is only available in Python"""
        ...
