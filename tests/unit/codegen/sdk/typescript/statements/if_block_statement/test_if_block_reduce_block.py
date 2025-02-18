from typing import TYPE_CHECKING

import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.statements.statement import StatementType
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.typescript.file import TSFile


def test_reduce_condition_to_true_elif(tmpdir):
    # language=typescript
    content = """
function foo(): void {
    if (a) {
        console.log(a);
        console.log(a+b);
    } else if (b) {
        console.log(b);
    } else {
        console.log(c);
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")
        function = file.get_function("foo")
        if_block = function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT)[0]
        if_block.reduce_condition(True)
    # language=typescript
    assert (
        file.content
        == """
function foo(): void {
    console.log(a);
    console.log(a+b);
    if (b) {
        console.log(b);
    } else {
        console.log(c);
    }
}
    """
    )


def test_reduce_condition_to_false_elif(tmpdir):
    # language=typescript
    content = """
function foo(): void {
    if (a) {
        console.log(a);
        console.log(a+b);
    } else if (b) {
        console.log(b);
    } else {
        console.log(c);
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")
        function = file.get_function("foo")
        if_block = function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT)[0]
        if_block.reduce_condition(False)
    # language=typescript
    assert (
        file.content
        == """
function foo(): void {
    if (b) {
        console.log(b);
    } else {
        console.log(c);
    }
}
    """
    )


def test_reduce_condition_to_true_else(tmpdir):
    # language=typescript
    content = """
function foo(): void {
    if (a) {
        console.log(a);
        console.log(c);
    } else {
        console.log(b);
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")
        function = file.get_function("foo")
        if_block = function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT)[0]
        if_block.reduce_condition(True)
    # language=typescript
    assert (
        file.content
        == """
function foo(): void {
    console.log(a);
    console.log(c);
}
    """
    )


def test_reduce_condition_to_false_else(tmpdir):
    # language=typescript
    content = """
function foo(): void {
    if (a) {
        console.log(a);
    } else {
        console.log(b);
        console.log(c);
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")
        function = file.get_function("foo")
        if_block = function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT)[0]
        if_block.reduce_condition(False)
    # language=typescript
    assert (
        file.content
        == """
function foo(): void {
    console.log(b);
    console.log(c);
}
    """
    )


def test_reduce_condition_multiple_if_blocks(tmpdir):
    # language=typescript
    content = """
function foo(): void {
    if (a) {
        console.log(a);
    }
    if (b) {
        console.log(b);
        console.log(b+c);
    } else if (c) {
        console.log(c);
        return;
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")
        function = file.get_function("foo")
        second_if = function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT)[1]
        second_if.reduce_condition(False)
    # language=typescript
    assert (
        file.content
        == """
function foo(): void {
    if (a) {
        console.log(a);
    }
    if (c) {
        console.log(c);
        return;
    }
}
    """
    )


def test_reduce_condition_nested_if(tmpdir):
    # language=typescript
    content = """
class MyClass {
    foo(): void {
        if (a) {
            if (b) {
                console.log(b);
            }
            console.log(a);
            if (c) {
                console.log(c);
                console.log(c+d);
            } else if (d) {
                console.log(d);
                return;
            }
        } else {
            console.log(e);
            return;
        }
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")
        function = file.get_class("MyClass").get_method("foo")
        top_if = function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT)[0]
        top_if.reduce_condition(True)
        nested_if = function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT)[2]
        nested_if.reduce_condition(False)

    # language=typescript
    assert (
        file.content
        == """
class MyClass {
    foo(): void {
        if (b) {
            console.log(b);
        }
        console.log(a);
        if (d) {
            console.log(d);
            return;
        }
    }
}
    """
    )


def test_reduce_condition_else_if_to_true(tmpdir):
    # language=typescript
    content = """
function foo(): void {
    if (a) {
        console.log(a);
    } else if (b) {
        console.log(b);
        console.log(b+c);
    } else if (c) {
        console.log(c);
    } else {
        console.log(d);
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")
        function = file.get_function("foo")
        elif_block = function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT)[0].elif_statements[0]
        elif_block.reduce_condition(True)
    # language=typescript
    assert (
        file.content
        == """
function foo(): void {
    if (a) {
        console.log(a);
    }
    console.log(b);
    console.log(b+c);
    if (c) {
        console.log(c);
    } else {
        console.log(d);
    }
}
    """
    )


def test_reduce_condition_else_if_to_false(tmpdir):
    # language=typescript
    content = """
function foo(): void {
    if (a) {
        console.log(a);
    } else if (b) {
        console.log(b);
        console.log(b+c);
    } else if (c) {
        console.log(c);
    } else {
        console.log(d);
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")
        function = file.get_function("foo")
        elif_block = function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT)[0].elif_statements[0]
        elif_block.reduce_condition(False)
    # language=typescript
    assert (
        file.content
        == """
function foo(): void {
    if (a) {
        console.log(a);
    } else if (c) {
        console.log(c);
    } else {
        console.log(d);
    }
}
    """
    )


def test_reduce_condition_else_statement_raises(tmpdir):
    # language=typescript
    content = """
function foo(): void {
    if (a) {
        console.log(a);
    } else if (b) {
        console.log(b);
    } else {
        console.log(c);
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")
        function = file.get_function("foo")
        else_block = function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT)[0].else_statement
        with pytest.raises(ValueError):
            else_block.reduce_condition(True)


def test_reduce_condition_to_true_single_if(tmpdir):
    # language=typescript
    content = """
function foo(): void {
    if (a) {
        console.log(a);
    }
    console.log(b);
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")
        function = file.get_function("foo")
        if_block = function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT)[0]
        if_block.reduce_condition(True)
    # language=typescript
    assert (
        file.content
        == """
function foo(): void {
    console.log(a);
    console.log(b);
}
    """
    )


def test_reduce_condition_to_false_single_if(tmpdir):
    # language=typescript
    content = """
function foo(): void {
    if (a) {
        console.log(a);
    }
    console.log(b);
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")
        function = file.get_function("foo")
        if_block = function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT)[0]
        if_block.reduce_condition(False)
    # language=typescript
    assert (
        file.content
        == """
function foo(): void {
    console.log(b);
}
    """
    )
