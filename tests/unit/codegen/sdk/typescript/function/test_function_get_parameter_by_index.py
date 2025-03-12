from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_function_get_parameter_by_index(tmpdir) -> None:
    # language=typescript
    file = """
function foo(a: number, b: string) {
    console.log(a);
    console.log(b);
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": file}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        symbol = file.get_function("foo")
        parameter = symbol.get_parameter_by_index(0)

    assert parameter.name == "a"
