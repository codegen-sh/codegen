from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_class_definition_rename_class_attribute_throws(tmpdir) -> None:
    # language=typescript
    content = """
class Foo {
    property = "property";
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        symbol = file.get_class("Foo")
        symbol.get_attribute("property").rename("property1")
    # language=typescript
    assert (
        file.content
        == """
class Foo {
    property1 = "property";
}
    """
    )
