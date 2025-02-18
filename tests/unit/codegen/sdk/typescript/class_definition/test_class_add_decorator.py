from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_add_decorator_to_class(tmpdir) -> None:
    # =====[ Simple ]=====
    # language=typescript
    content = """
class Foo {
    property = "property";
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        symbol = file.get_class("Foo")
        symbol.add_decorator("@test_decorator")

    assert "@test_decorator\nclass Foo" in file.content


def test_add_decorator_to_class_unique(tmpdir) -> None:
    # language=typescript
    content = """
@test_decorator
class Foo {
    property = "property";
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        symbol = file.get_class("Foo")
        assert not symbol.add_decorator("@test_decorator", skip_if_exists=True)

    assert file.content.count("@test_decorator") == 1
