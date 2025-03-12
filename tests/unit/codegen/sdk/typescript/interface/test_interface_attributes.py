from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session, get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.core.statements.attribute import Attribute


def test_interface_attributes_finds_correct_number(tmpdir) -> None:
    file = """
interface Animal {
  name: string;
  age: number;
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")
        animal = file.get_symbol("Animal")
        assert len(animal.attributes) == 2


def test_attribute_is_optional(tmpdir) -> None:
    # language=typescript
    content = """
interface Animal {
  name: string;
  age?: number;
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        animal = file.get_symbol("Animal")
        name_attr: Attribute = animal.get_attribute("name")
        assert name_attr.is_optional is False
        age_attr: Attribute = animal.get_attribute("age")
        assert age_attr.is_optional is True
