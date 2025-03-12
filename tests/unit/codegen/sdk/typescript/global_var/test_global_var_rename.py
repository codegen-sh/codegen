from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_rename_global_var_excludes_class_and_function_matches(tmpdir) -> None:
    # language=typescript
    file = """
let b: number = 1;

class A {
    b: number = 1;
}

function baz() {
    const a = new A();
    const c = a.b;
}
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as codebase:
        file = codebase.get_file("test.ts")
        symbol = file.get_symbol("b")
        symbol.rename("XYZ")

    assert "let XYZ: number = 1" in file.content
    assert "b: number = 1" in file.content  # does NOT replace class usages
    assert "const c = a.b" in file.content  # does NOT replace function usages
