from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_function_call_without_docstring_prepend_statements(tmpdir) -> None:
    FILE_NAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
export function doSomething(param1: string, param2: number): string[] {
    console.log("original statement")
    return []
}
    """
    # language=typescript
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME: FILE_CONTENT}) as codebase:
        file = codebase.get_file(FILE_NAME)
        func = file.get_function("doSomething")

        lines = """const newVar = 123;
if (newVar > 100) {
    console.log("prepended statement");
}"""
        func.prepend_statements(lines)

        expected_content = """
export function doSomething(param1: string, param2: number): string[] {
    const newVar = 123;
    if (newVar > 100) {
        console.log("prepended statement");
    }
    console.log("original statement")
    return []
}
    """

    assert file.content == expected_content


def test_function_call_with_docstring_prepend_statements(tmpdir) -> None:
    FILE_NAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
/**
* Example function with docstring
* @param param1 First parameter description
* @param param2 Second parameter description
*/
export function doSomething(param1: string, param2: number): string[] {
    console.log("original statement")
    return []
}
    """
    # language=typescript
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME: FILE_CONTENT}) as codebase:
        file = codebase.get_file(FILE_NAME)
        func = file.get_function("doSomething")

        lines = """const newVar = 123;
if (newVar > 100) {
    console.log("prepended statement");
}"""
        func.prepend_statements(lines)

        expected_content = """
/**
* Example function with docstring
* @param param1 First parameter description
* @param param2 Second parameter description
*/
export function doSomething(param1: string, param2: number): string[] {
    const newVar = 123;
    if (newVar > 100) {
        console.log("prepended statement");
    }
    console.log("original statement")
    return []
}
    """

    assert file.content == expected_content
