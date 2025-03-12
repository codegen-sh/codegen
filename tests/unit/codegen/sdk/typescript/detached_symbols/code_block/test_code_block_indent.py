from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.statements.statement import StatementType
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_indent_once_to_left(tmpdir):
    # language=typescript
    content = """
function foo(): number {
    const x: number = 1;
    const y: number = 2;
    return x + y;
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        code_block = file.get_function("foo").code_block
        code_block.indent(-1)

    # language=typescript
    assert (
        file.content
        == """
function foo(): number {
const x: number = 1;
const y: number = 2;
return x + y;
}
    """
    )


def test_indent_left_exceed_limit(tmpdir):
    # language=typescript
    content = """
function foo(): number {
    const x: number = 1;
    const y: number = 2;
    return x + y;
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        code_block = file.get_function("foo").code_block
        code_block.indent(-5)

    # language=typescript
    assert (
        file.content
        == """
function foo(): number {
const x: number = 1;
const y: number = 2;
return x + y;
}
    """
    )


def test_indent_right_once(tmpdir):
    # language=typescript
    content = """
function foo(): number {
    const x: number = 1;
    const y: number = 2;
    return x + y;
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        code_block = file.get_function("foo").code_block
        code_block.indent(1)

    # language=typescript
    assert (
        file.content
        == """
function foo(): number {
        const x: number = 1;
        const y: number = 2;
        return x + y;
}
    """
    )


def test_indent_right_multiple(tmpdir):
    # language=typescript
    content = """
function foo(): number {
    const x: number = 1;
    const y: number = 2;
    return x + y;
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        code_block = file.get_function("foo").code_block
        code_block.indent(5)

    # language=typescript
    assert (
        file.content
        == """
function foo(): number {
                        const x: number = 1;
                        const y: number = 2;
                        return x + y;
}
    """
    )


def test_indent_zero(tmpdir):
    # language=typescript
    content = """
function foo(): number {
    const x: number = 1;
    const y: number = 2;
    return x + y;
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        code_block = file.get_function("foo").code_block
        code_block.indent(0)

    assert file.content == content


def test_indent_nested_code_blocks(tmpdir):
    # language=typescript
    content = """
function foo(): number {
    let sum_val: number = 0;
    const threshold: number = 10;
    const is_threshold_reached = (): boolean => sum_val > threshold;
    is_threshold_reached();

    for (let i = 0; i < 10; i++) {
        console.log(i);
    }

    if (a) {
        if (b) {
            console.log(b);
        }
        if (c) {
            console.log(c);
        } else if (d) {
            return 0; // Assuming we should return a number
        }
    } else {
        return 0;
    }

    if (is_threshold_reached()) {
        return sum_val;
    }
    return 0;
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        code_block = file.get_function("foo").code_block
        code_block.indent(-1)

    # language=typescript
    assert (
        file.content
        == """
function foo(): number {
let sum_val: number = 0;
const threshold: number = 10;
const is_threshold_reached = (): boolean => sum_val > threshold;
is_threshold_reached();

for (let i = 0; i < 10; i++) {
    console.log(i);
}

if (a) {
    if (b) {
        console.log(b);
    }
    if (c) {
        console.log(c);
    } else if (d) {
        return 0; // Assuming we should return a number
    }
} else {
    return 0;
}

if (is_threshold_reached()) {
    return sum_val;
}
return 0;
}
    """
    )


def test_indent_only_nested_block(tmpdir):
    # language=typescript
    content = """
function foo(a: boolean, b: any, c: any, d: boolean): void {
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
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        code_block = file.get_function("foo").code_block
        if_blocks = code_block.get_statements(StatementType.IF_BLOCK_STATEMENT)
        if_blocks[0].consequence_block.indent(-1)
        if_blocks[1].consequence_block.indent(1)

    # language=typescript
    assert (
        file.content
        == """
function foo(a: boolean, b: any, c: any, d: boolean): void {
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
    )
