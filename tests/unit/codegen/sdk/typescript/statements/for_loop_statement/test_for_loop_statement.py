from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.statements.statement import StatementType
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_for_loop_statement_parse(tmpdir) -> None:
    # language=typescript
    content = """
// Traditional for loop
for (let i = 0; i < 10; i++) {
    console.log(i);
}

// Traditional for loop with no increments
for (let i = 0; i < 10;) {
    console.log(i);
    i++;
}

// For...of loop
const arr = [1, 2, 3, 4, 5];
for (const num of arr) {
    console.log(num);
}

// For...in loop
const obj = { a: 1, b: 2, c: 3 };
for (const key in obj) {
    console.log(key);
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        statements = file.code_block.statements
        traditional_for = statements[1]
        traditional_for_no_increment = statements[3]
        for_of = statements[6]
        for_in = statements[9]

        assert traditional_for.statement_type == StatementType.FOR_LOOP_STATEMENT
        assert traditional_for_no_increment.statement_type == StatementType.FOR_LOOP_STATEMENT
        assert for_of.statement_type == StatementType.FOR_LOOP_STATEMENT
        assert for_in.statement_type == StatementType.FOR_LOOP_STATEMENT

        assert traditional_for.initializer == "let i = 0;"
        assert traditional_for.condition == "i < 10"
        assert traditional_for.increment == "i++"
        assert len(traditional_for.code_block.statements) == 1

        assert traditional_for_no_increment.initializer == "let i = 0;"
        assert traditional_for_no_increment.condition == "i < 10"
        assert traditional_for_no_increment.increment is None
        assert len(traditional_for_no_increment.code_block.statements) == 2

        assert for_of.item == "num"
        assert for_of.iterable == "arr"
        assert len(for_of.code_block.statements) == 1

        assert for_in.item == "key"
        assert for_in.iterable == "obj"
        assert len(for_in.code_block.statements) == 1


def test_for_loop_statement_function_calls(tmpdir) -> None:
    # language=typescript
    content = """
for(let i = init(); i < 10; i += increment()) {
    console.log(i);
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        for_loop = file.code_block.statements[0]

        assert len(for_loop.function_calls) == 3
        assert for_loop.function_calls[0].source == "init()"
        assert for_loop.function_calls[1].source == "increment()"
        assert for_loop.function_calls[2].source == "console.log(i)"


def test_for_loop_statement_dependencies(tmpdir) -> None:
    # language=typescript
    content = """
var x = 0;
function foo() {
    for(let i = 0; i < 10; i++) {
        const a = () => {
            x + i;
            console.log(x);
        };
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        foo = file.get_function("foo")

        assert len(foo.dependencies) == 1
        assert foo.dependencies[0] == file.get_global_var("x")
