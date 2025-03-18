from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.statements.statement import StatementType
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.typescript.file import TSFile
    from codegen.sdk.typescript.statements.if_block_statement import TSIfBlockStatement


def test_parse_if_else_statement_from_codeblock(tmpdir) -> None:
    # language=typescript
    content = """
function foo(): void {
    if (a + b) {
        console.log(a);
    } else if (b && c) {
        console.log(b);
    } else if ((c = a + b) && true) {
        console.log(c);
        return;
    } else {
        return;
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")
        function = file.get_function("foo")
        if_blocks = function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT)
        assert len(if_blocks) == 1
        statement = if_blocks[0]
        assert statement.is_if_statement and not statement.is_else_statement and not statement.is_elif_statement
        assert statement.condition.source == "a + b"
        assert len(statement.consequence_block.statements) == 1
        assert statement.consequence_block.statements[0].source == "console.log(a);"

        else_ifs = statement.elif_statements
        assert len(else_ifs) == 2
        assert all([not else_if.is_if_statement and not else_if.is_else_statement and else_if.is_elif_statement for else_if in else_ifs])
        assert else_ifs[0].condition.source == "b && c"
        assert else_ifs[1].condition.source == "(c = a + b) && true"
        assert len(else_ifs[0].consequence_block.statements) == 1
        assert len(else_ifs[1].consequence_block.statements) == 2
        assert else_ifs[0].consequence_block.statements[0].source == "console.log(b);"
        assert else_ifs[1].consequence_block.statements[0].source == "console.log(c);"
        assert else_ifs[1].consequence_block.statements[1].source == "return;"

        else_statement = statement.else_statement
        assert else_statement.is_else_statement and not else_statement.is_elif_statement and not else_statement.is_if_statement
        assert else_statement.condition is None
        assert len(else_statement.consequence_block.statements) == 1
        assert else_statement.consequence_block.statements[0].source == "return;"


def test_parse_nested_if_statements_from_codeblock(tmpdir) -> None:
    # language=typescript
    content = """
function foo(): void {
    if (a) {
        if (b) {
            console.log(b);
        }
        if (c) {
            console.log(c);
        } else if (d) {
            return;
        }
    } else {
        return;
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")
        function = file.get_function("foo")
        assert len(function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT)) == 3
        assert len(function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT, function.code_block.level)) == 1
        assert len(function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT, function.code_block.level + 1)) == 3

        top_if_block = function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT, function.code_block.level)[0]
        assert top_if_block.is_if_statement and not top_if_block.is_else_statement and not top_if_block.is_elif_statement
        assert len(top_if_block.elif_statements) == 0
        assert top_if_block.else_statement is not None

        nested_if_blocks: list[TSIfBlockStatement] = top_if_block.consequence_block.get_statements(StatementType.IF_BLOCK_STATEMENT)
        assert len(nested_if_blocks) == 2
        assert all([nested_if_block.is_if_statement and not nested_if_block.is_else_statement and not nested_if_block.is_elif_statement for nested_if_block in nested_if_blocks])
        assert nested_if_blocks[0].condition.source == "b"
        assert len(nested_if_blocks[0].elif_statements) == 0
        assert nested_if_blocks[0].else_statement is None

        assert nested_if_blocks[1].condition.source == "c"
        assert len(nested_if_blocks[1].elif_statements) == 1
        assert nested_if_blocks[1].elif_statements[0].is_elif_statement
        assert nested_if_blocks[1].else_statement is None


def test_get_alternative_if_blocks_from_codeblock(tmpdir) -> None:
    # language=typescript
    content = """
function foo(): void {
    if (a) {
        console.log(a);
    } else if (b) {
        console.log(b);
    } else if (c) {
        console.log(c);
    } else {
        return;
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")
        function = file.get_function("foo")
        if_blocks = function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT)
        assert len(if_blocks) == 1
        alt_blocks = if_blocks[0].alternative_blocks
        assert len(alt_blocks) == 3
        assert len(if_blocks[0].alternative_blocks) == 3
        assert len(if_blocks[0].elif_statements) == 2
        assert if_blocks[0].else_statement is not None
        assert if_blocks[0].else_statement.is_else_statement
        assert not if_blocks[0].else_statement.is_elif_statement
        assert not if_blocks[0].else_statement.is_if_statement

        assert len(alt_blocks[0].alternative_blocks) == 2
        assert len(alt_blocks[0].elif_statements) == 1
        assert alt_blocks[0].elif_statements[0].is_elif_statement
        assert alt_blocks[0].else_statement is not None
        assert alt_blocks[0].else_statement.is_else_statement

        assert len(alt_blocks[1].alternative_blocks) == 1
        assert len(alt_blocks[1].elif_statements) == 0
        assert alt_blocks[1].else_statement is not None
        assert alt_blocks[1].else_statement.is_else_statement

        assert len(alt_blocks[2].alternative_blocks) == 0
        assert len(alt_blocks[2].elif_statements) == 0
        assert alt_blocks[2].else_statement is None


def test_if_else_reassignment_handling(tmpdir) -> None:
    # language=typescript
    content = """
if (true) {
    PYSPARK = true;
} else if (false) {
    PYSPARK = false;
} else {
    PYSPARK = null;
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


def test_if_else_reassignment_handling_function(tmpdir) -> None:
    # language=typescript
    content = """
if (true) {
    function foo() {
        console.log('t');
    }
} else if (false) {
    function foo() {
        console.log('t');
    }
} else {
    function foo() {
        console.log('t');
    }
}
foo();
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        foo = file.get_function("foo")
        func_call = file.function_calls[3]
        for func in file.functions:
            usage = func.usages[0]
            assert usage.match == func_call


def test_if_else_reassignment_handling_inside_func(tmpdir) -> None:
    # language=typescript
    content = """
function foo(a) {
    a = 1;
    if (xyz) {
        b = 1;
    } else {
        b = 2;
    }
    f(a); // a resolves to 1 name
    f(b); // b resolves to 2 possible names
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        foo = file.get_function("foo")
        assert foo
        assert len(foo.parameters[0].usages) == 0
        func_call_a = foo.function_calls[0].args[0]
        func_call_b = foo.function_calls[1]
        for symbol in file.symbols(True):
            if symbol.name == "a":
                assert len(symbol.usages) == 1
                symbol.usages[0].match == func_call_a
            elif symbol.name == "b":
                assert len(symbol.usages) == 1
                symbol.usages[0].match == func_call_b


def test_if_else_reassignment_handling_partial_if(tmpdir) -> None:
    # language=typescript
    content = """
PYSPARK = "TEST";
if (true) {
    PYSPARK = true;
} else if (null) {
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


def test_if_else_reassignment_handling_solo_if(tmpdir) -> None:
    # language=typescript
    content = """
PYSPARK = "TEST";
if (true) {
    PYSPARK = true;
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


def test_if_else_reassignment_handling_double(tmpdir) -> None:
    # language=typescript
    content = """
if (false) {
    PYSPARK = "TEST1";
} else if (true) {
    PYSPARK = "TEST2";
}

if (true) {
    PYSPARK = true;
} else if (null) {
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


def test_if_else_reassignment_handling_nested_usage(tmpdir) -> None:
    # language=typescript
    content = """
if (true) {
    PYSPARK = true;
} else if (null) {
    PYSPARK = false;
    console.log(PYSPARK);
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        func_call = file.function_calls[0]
        pyspark_arg = func_call.args.children[0]
        first = file.symbols[0]
        second = file.symbols[1]
        assert len(first.usages) == 0
        assert second.usages[0].match == pyspark_arg


def test_if_else_reassignment_inside_func_with_external_element(tmpdir) -> None:
    # language=typescript
    content = """
PYSPARK = "0";
function foo() {
    if (true) {
        PYSPARK = true;
    } else {
        PYSPARK = false;
    }
    console.log(PYSPARK);
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        func_call = file.function_calls[0]
        pyspark_arg = func_call.args.children[0]
        func = file.get_function("foo")
        for assign in func.valid_symbol_names[:-1]:
            assign.usages[0] == pyspark_arg
