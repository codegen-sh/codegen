from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.expressions.binary_expression import BinaryExpression
from codegen.sdk.core.expressions.boolean import Boolean
from codegen.sdk.core.statements.statement import StatementType
from codegen.sdk.core.statements.while_statement import WhileStatement
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_while_statement_parse(tmpdir) -> None:
    # language=typescript
    content = """
// Single while statement
while (true) {
    console.log("Hello");
    break;
}

// Do/While loop
let a: number = 1;
let b: number = 10;
do {
    a += 1;
    console.log(a);
} while (a < b);

// This will always execute after the loop
console.log("a is not less than b");
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        statements = file.code_block.statements
        simple_while = statements[1]
        while_else = statements[5]

        assert isinstance(simple_while, WhileStatement)
        assert isinstance(while_else, WhileStatement)
        assert simple_while.statement_type == StatementType.WHILE_STATEMENT
        assert while_else.statement_type == StatementType.WHILE_STATEMENT

        assert simple_while.condition == "true"
        assert isinstance(simple_while.condition, Boolean)
        assert len(simple_while.code_block.statements) == 2

        assert while_else.condition == "a < b"
        assert isinstance(while_else.condition, BinaryExpression)
        assert len(while_else.code_block.statements) == 2


def test_while_statement_function_calls(tmpdir) -> None:
    # language=typescript
    content = """
let a: number = 1;

function foo(): number {
    return a;
}

function bar(): number {
    return a + 1;
}

const c: number = 10;

function test() {
    while (foo() + bar()) {
        console.log("Hello");
        if (a > 10) {
            console.log(c);
        }
        break;
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        test = file.get_function("test")
        while_statement = test.code_block.statements[0]

        test_calls = test.function_calls
        while_calls = while_statement.function_calls
        assert len(test_calls) == 4
        assert test_calls == while_calls


def test_while_statement_dependencies(tmpdir) -> None:
    # language=typescript
    content = """
let a: number = 1;


function foo(): number {
    return a;
}

function bar(): number {
    return a + 1;
}

const c: number = 10;

function test() {
    console.log(c);
    while (foo() + bar()) {
        console.log("Hello");
        break;
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        test = file.get_function("test")

        test_dependencies = test.dependencies
        assert set([x.name for x in test_dependencies]) == {"foo", "bar", "c"}
        assert len(test_dependencies) == 3
