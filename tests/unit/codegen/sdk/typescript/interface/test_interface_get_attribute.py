from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_interface_get_attribute_finds_match(tmpdir) -> None:
    file = """
interface Animal {
  name: string;
  age: number;
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")
        animal = file.get_symbol("Animal")
        name_attr = animal.get_attribute("name")
        assert name_attr
        assert name_attr.name == "name"
