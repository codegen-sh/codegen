from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_class_definition_filter(tmpdir) -> None:
    # language=typescript
    content = """
class Foo {
  private name: string;
  public name2: string;
  public fn() {
  }
  private fn2() {
  }
}

"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        foo_class = file.get_class("Foo")
        assert len(foo_class.methods(private=False)) == 1
        assert len(foo_class.methods(private=True)) == 2
        assert len(foo_class.attributes(private=True)) == 2
        assert len(foo_class.attributes(private=False)) == 1
