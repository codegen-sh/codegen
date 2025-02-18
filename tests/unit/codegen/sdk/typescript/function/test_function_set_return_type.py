from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_set_return_type(tmpdir) -> None:
    FILE_NAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
export function foo(input: string) {
    return "hello";
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME: FILE_CONTENT}) as codebase:
        file = codebase.get_file(FILE_NAME)
        func = file.get_function("foo")
        func.set_return_type("string")

    # language=typescript
    expected_content = """
export function foo(input: string): string {
    return "hello";
}
    """
    assert file.content == expected_content
