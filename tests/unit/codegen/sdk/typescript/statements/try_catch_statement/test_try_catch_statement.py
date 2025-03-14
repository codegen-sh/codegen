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


def test_try_catch_statement_dependencies_external(tmpdir) -> None:
    # language=typescript
    content = """
let test: Record<string, string> | undefined;
try {
    test = JSON.parse(test);
    if (Object.keys(test).length === 0) {
    test = undefined;
    }
} catch (e) {
    console.error("Error parsing test", e);
    test = undefined;
}
let use = test



    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        symbol = file.get_symbol("test")
        func_call = file.function_calls[0]
        assign_val = file.symbols[-1].value
        for symb in file.symbols[:-1]:
            assert any(usage.match == assign_val for usage in symb.usages)


def test_try_catch_reassignment_handling(tmpdir) -> None:
    # language=typescript
    content = """
try {
    PYSPARK = true;
} catch (error) {
    PYSPARK = false;
}

console.log(PYSPARK);
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        symbol = file.get_symbol("PYSPARK")
        func_call = file.function_calls[0]
        pyspark_arg = func_call.args.children[0]
        for symb in file.symbols:
            usage = symb.usages[0]
            assert usage.match == pyspark_arg


def test_try_catch_reassignment_handling_function(tmpdir) -> None:
    # language=typescript
    content = """
try {
    function foo() {
        console.log('try');
    }
} catch (error) {
    function foo() {
        console.log('catch');
    }
}
foo();
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        foo = file.get_function("foo")
        func_call = file.function_calls[2]
        for func in file.functions:
            assert func.usages
            usage = func.usages[0]
            assert usage.match == func_call


def test_try_catch_reassignment_handling_function_finally(tmpdir) -> None:
    # language=typescript
    content = """
try {
    function foo() {
        console.log('try');
    }
} catch (error) {
    function foo() {
        console.log('catch');
    }
} finally {
    function foo() {
        console.log('finally');
    }
}
foo();
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        foo = file.get_function("foo")
        func_call = file.function_calls[3]
        for idx, func in enumerate(file.functions):
            if idx == 2:
                assert func.usages
                usage = func.usages[0]
                assert usage.match == func_call
            else:
                assert len(func.usages) == 0


def test_try_catch_reassignment_handling_nested(tmpdir) -> None:
    # language=typescript
    content = """
try {
    PYSPARK = true;
    try {
        PYSPARK = "nested";
    } catch (innerError) {
        PYSPARK = "inner catch";
    }
} catch (error) {
    PYSPARK = false;
}

console.log(PYSPARK);
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        func_call = file.function_calls[0]
        pyspark_arg = func_call.args.children[0]
        for symb in file.symbols:
            usage = symb.usages[0]
            assert usage.match == pyspark_arg


def test_try_catch_reassignment_handling_inside_func(tmpdir) -> None:
    # language=typescript
    content = """
function process() {
    let result;
    try {
        result = "success";
    } catch (error) {
        result = "error";
    } finally {
        result = "done";
    }
    return result;
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        process_func = file.get_function("process")
        return_stmt = process_func.code_block.statements[-1]
        result_var = return_stmt.value
        for idx, symb in enumerate(file.symbols(True)):
            if symb.name == "result":
                if idx == 4:
                    # Only finally triggers
                    assert len(symb.usages) > 0
                    assert any(usage.match == result_var for usage in symb.usages)
                else:
                    assert len(symb.usages) == 0


def test_try_catch_reassignment_with_finally(tmpdir) -> None:
    # language=typescript
    content = """
try {
    PYSPARK = true;
} catch (error) {
    PYSPARK = false;
} finally {
    PYSPARK = "finally";
}

console.log(PYSPARK);
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        func_call = file.function_calls[0]
        pyspark_arg = func_call.args.children[0]
        for idx, symb in enumerate(file.symbols):
            if idx == 2:
                usage = symb.usages[0]
                assert usage.match == pyspark_arg
            else:
                assert not symb.usages


def test_try_catch_multiple_reassignment(tmpdir) -> None:
    # language=typescript
    content = """
try {
    PYSPARK = true;
} catch (error) {
    PYSPARK = false;
}

try {
    PYSPARK = "second try";
} catch (error) {
    PYSPARK = "second catch";
}

console.log(PYSPARK);
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        func_call = file.function_calls[0]
        pyspark_arg = func_call.args.children[0]
        for symb in file.symbols:
            usage = symb.usages[0]
            assert usage.match == pyspark_arg
