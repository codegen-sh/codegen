from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_function_function_calls_gets_calls_in_return_statement(tmpdir) -> None:
    FILENAME = "function_test.ts"
    # language=typescript
    FILE_CONTENT = """
    function foo(): void {
        a(1, 2);
        const b = c('3');
        return d(4);
    }
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILENAME: FILE_CONTENT}) as codebase:
        function_symbol = codebase.get_symbol("foo")

        assert len(function_symbol.function_calls) == 3

        # First Call
        assert function_symbol.function_calls[0].source == "a(1, 2)"
        assert function_symbol.function_calls[0].name == "a"

        # Second Call
        assert function_symbol.function_calls[1].source == "c('3')"
        assert function_symbol.function_calls[1].name == "c"

        # Third Call
        assert function_symbol.function_calls[2].source == "d(4)"
        assert function_symbol.function_calls[2].name == "d"
