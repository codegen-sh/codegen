from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_function_return_statements_includes_in_if_else_bocks(tmpdir) -> None:
    FILENAME = "function_test.ts"
    # language=typescript
    FILE_CONTENT = """
function foo(a: number): boolean {
    if (a === 1) {
        return true;
    } else {
        return false;
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILENAME: FILE_CONTENT}) as codebase:
        function_symbol = codebase.get_symbol("foo")

        assert len(function_symbol.return_statements) == 2
        assert function_symbol.return_statements[0].source == "return true;"
        assert function_symbol.return_statements[0].value == "true"
        assert function_symbol.return_statements[1].source == "return false;"
        assert function_symbol.return_statements[1].value == "false"
