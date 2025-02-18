from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_function_call_rename_updates_source(tmpdir) -> None:
    FILE_NAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
function example() {
    helper("a", "b", "c")
    return true;
}
    """
    # language=typescript
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME: FILE_CONTENT}) as codebase:
        file = codebase.get_file(FILE_NAME)
        func = file.get_function("example")
        fcall = func.function_calls[0]
        fcall.args[0].edit('"modified"')
        fcall.rename("new_helper")

        lines = """const x = 5;
const y = 10;
if (x < y) {
    console.log("x is less than y");
}"""
        func.prepend_statements(lines)

        expected_content = """
function example() {
    const x = 5;
    const y = 10;
    if (x < y) {
        console.log("x is less than y");
    }
    new_helper("modified", "b", "c")
    return true;
}
    """

    assert file.content == expected_content
