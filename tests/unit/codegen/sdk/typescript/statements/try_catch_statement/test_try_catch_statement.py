from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.statements.statement import StatementType
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_try_catch_statement_parse(tmpdir) -> None:
    # language=typescript
    content = """
try {
    // Try block
    riskyFunction();
} catch (error) {
    // Catch block
    console.error(error);
}
try {
    anotherRiskyFunction();
} catch (e) {
    handle(e);
} finally {
    // Finally block
    cleanup();
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        statements = file.code_block.statements
        try_catch_1 = statements[0]
        try_catch_2 = statements[1]

        assert try_catch_1.statement_type == StatementType.TRY_CATCH_STATEMENT
        assert try_catch_2.statement_type == StatementType.TRY_CATCH_STATEMENT

        assert len(try_catch_1.code_block.statements) == 2
        assert len(try_catch_1.catch.code_block.statements) == 2
        assert try_catch_1.finalizer is None

        assert len(try_catch_2.code_block.statements) == 1
        assert len(try_catch_2.catch.code_block.statements) == 1
        assert len(try_catch_2.finalizer.code_block.statements) == 2


def test_try_catch_statement_function_calls(tmpdir) -> None:
    # language=typescript
    content = """
try {
    riskyOperation();
} catch (e) {
    logError(e);
} finally {
    finalizeProcess();
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        try_catch = file.code_block.statements[0]
        assert len(try_catch.function_calls) == 3
        assert try_catch.function_calls[0].source == "riskyOperation()"
        assert try_catch.function_calls[1].source == "logError(e)"
        assert try_catch.function_calls[2].source == "finalizeProcess()"


def test_try_catch_statement_dependencies(tmpdir) -> None:
    # language=typescript
    content = """
var globalVar = 0;
function example() {
    try {
        process(globalVar);
    } catch (ex) {
        console.error(ex);
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        example = file.get_function("example")
        assert len(example.dependencies) == 1
        assert example.dependencies[0] == file.get_global_var("globalVar")
