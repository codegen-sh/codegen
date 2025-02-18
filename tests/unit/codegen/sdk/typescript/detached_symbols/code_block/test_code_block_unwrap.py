from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.statements.statement import StatementType
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.typescript.file import TSFile


def test_unwrap_flat_statements(tmpdir):
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
        function.code_block.unwrap()
    # language=typescript
    assert (
        file.content
        == """
if (a) {
    console.log(a);
} else if (b) {
    console.log(b);
} else {
    console.log(c);
}
    """
    )


def test_unwrap_nested_statements(tmpdir):
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
        nested_if = function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT)[1]
        nested_if.consequence_block.unwrap()
    # language=typescript
    assert (
        file.content
        == """
function foo(): void {
    if (a) {
        console.log(b);
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
    )


def test_unwrap_sandwiched_statements(tmpdir):
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
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT, verify_output=False) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")
        function = file.get_function("foo")
        if_block = function.code_block.if_blocks[0]
        if_block.elif_statements[0].consequence_block.unwrap()
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
    else if (c) {
        console.log(c);
    } else {
        console.log(d);
    }
}
    """
    )


def test_unwrap_multiline_wrapper(tmpdir):
    # language=typescript
    content = """
function foo(): void {
    if (
      condition1 &&
      condition2 &&
      (condition3 || condition4)
    ) {
        console.log(a);
        console.log(b);
    }
    for (
      let i = 0;
      i < array.length &&
      array[i] !== null &&
      (array[i].isValid() || array[i].canBeProcessed());
      i++
    ) {
        // Loop body
        console.log(array[i]);
    }
    while (
      condition1 &&
      condition2 &&
      (condition3 || condition4) &&
      someFunction()
    ) {
        // Loop body
        // Code to execute while the conditions are true
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")
        function = file.get_function("foo")
        block_statements = function.code_block.statements
        for block_statement in block_statements:
            for code_block in block_statement.nested_code_blocks:
                code_block.unwrap()
    # language=typescript
    assert (
        file.content
        == """
function foo(): void {
    console.log(a);
    console.log(b);
    // Loop body
    console.log(array[i]);
    // Loop body
    // Code to execute while the conditions are true
}
    """
    )
