from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.typescript.file import TSFile


def test_reduce_ternary_condition_to_true(tmpdir):
    # language=typescript
    content = """
function foo(): void {
    let result = a ? 'valueA' : 'valueB';
    console.log(result);
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")
        foo = file.get_function("foo")
        ternary_block = foo.code_block.statements[0].value
        ternary_block.reduce_condition(True)
    # language=typescript
    assert (
        file.content
        == """
function foo(): void {
    let result = 'valueA';
    console.log(result);
}
    """
    )


def test_reduce_ternary_condition_to_false(tmpdir):
    # language=typescript
    content = """
function foo(): void {
    let result = a ? 'valueA' : 'valueB';
    console.log(result);
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")
        foo = file.get_function("foo")
        ternary_block = foo.code_block.statements[0].value
        ternary_block.reduce_condition(False)
    # language=typescript
    assert (
        file.content
        == """
function foo(): void {
    let result = 'valueB';
    console.log(result);
}
    """
    )


def test_reduce_nested_ternary_condition_to_true_and_false(tmpdir):
    # language=typescript
    content = """
function foo(): void {
    let result = a ? (b ? 'valueB_true' : 'valueB_false') : 'valueA';
    console.log(result);
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")
        foo = file.get_function("foo")
        outer_ternary = foo.code_block.statements[0].value
        inner_ternary = outer_ternary.consequence.resolve()
        inner_ternary.reduce_condition(True)
        outer_ternary.reduce_condition(True)
    # language=typescript
    assert (
        file.content
        == """
function foo(): void {
    let result = 'valueB_true';
    console.log(result);
}
    """
    )


def test_reduce_nested_ternary_condition_outer_false(tmpdir):
    # language=typescript
    content = """
function foo(): void {
    let result = a ? (b ? 'valueB_true' : 'valueB_false') : 'valueA';
    console.log(result);
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")
        foo = file.get_function("foo")
        outer_ternary = foo.code_block.statements[0].value
        outer_ternary.reduce_condition(False)
    # language=typescript
    assert (
        file.content
        == """
function foo(): void {
    let result = 'valueA';
    console.log(result);
}
    """
    )


def test_reduce_multiple_ternary_conditions(tmpdir):
    # language=typescript
    content = """
function foo(): void {
    let result1 = a ? 'valueA' : 'valueB';
    let result2 = b ? 'valueC' : 'valueD';
    console.log(result1, result2);
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")
        foo = file.get_function("foo")
        ternary_block1 = foo.code_block.statements[0].value
        ternary_block2 = foo.code_block.statements[1].value
        ternary_block1.reduce_condition(True)
        ternary_block2.reduce_condition(False)
    # language=typescript
    assert (
        file.content
        == """
function foo(): void {
    let result1 = 'valueA';
    let result2 = 'valueD';
    console.log(result1, result2);
}
    """
    )


def test_reduce_ternary_condition_with_function_call(tmpdir):
    # language=typescript
    content = """
function foo(): void {
    let result = isTrue(a) ? 'valueA' : 'valueB';
    console.log(result);
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")
        foo = file.get_function("foo")
        ternary_block = foo.code_block.statements[0].value
        ternary_block.reduce_condition(False)
    # language=typescript
    assert (
        file.content
        == """
function foo(): void {
    let result = 'valueB';
    console.log(result);
}
    """
    )


def test_reduce_ternary_condition_with_dict(tmpdir):
    # language=typescript jsx
    # language=typescript
    content = """
function foo(): { a: number } {
    let result = b;
    return {
        a: 1,
        ...(result ?
                {b: 1} :
                {c: 2}
        )
    };
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")
        foo = file.get_function("foo")
        result_value = foo.code_block.statements[0].value
        result_value.reduce_condition(False)
    # language=typescript jsx
    # language=typescript
    assert (
        file.content
        == """
function foo(): { a: number } {
    return {
        a: 1,
        c: 2,
    };
}
"""
    )


def test_reduce_ternary_condition_with_dict_complex(tmpdir):
    # language=typescript jsx
    # language=typescript
    content = """
function foo(): { a: number } {
    let result = b;
    return {
        a: 1,
        ...(result ?
                {b: 1} :
                {c: 2, d: 3}
        )
    };
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")
        foo = file.get_function("foo")
        result_value = foo.code_block.statements[0].value
        result_value.reduce_condition(False)
    # language=typescript jsx
    # language=typescript
    assert (
        file.content
        == """
function foo(): { a: number } {
    return {
        a: 1,
        c: 2,
        d: 3,
    };
}
"""
    )


def test_reduce_ternary_condition_with_dict_trailing_comma(tmpdir):
    # language=typescript
    content = """
function foo(): { a: number } {
    let result = b;
    return {
        a: 1,
        ...(result ?
                {b: 1} :
                {c: 2, d: 3}
        ),
    };
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")
        foo = file.get_function("foo")
        result_value = foo.code_block.statements[0].value
        result_value.reduce_condition(False)
    # language=typescript
    assert (
        file.content
        == """
function foo(): { a: number } {
    return {
        a: 1,
        c: 2,
        d: 3,
    };
}
"""
    )


def test_reduce_ternary_condition_with_empty_arrays(tmpdir):
    # language=typescript
    content = """
function foo(): string[] {
    let result = condition ? [] : ['value'];
    let result2 = condition ? ['value'] : [];
    return result.concat(result2);
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")
        foo = file.get_function("foo")
        ternary1 = foo.code_block.statements[0].value
        ternary2 = foo.code_block.statements[1].value
        ternary1.reduce_condition(True)
        ternary2.reduce_condition(False)
    # language=typescript
    assert (
        file.content
        == """
function foo(): string[] {
    let result = [];
    let result2 = [];
    return result.concat(result2);
}
"""
    )


def test_reduce_ternary_condition_with_jsx_prop(tmpdir):
    # language=typescript jsx
    content = """
function foo(): JSX.Element {
    return (
        <Container
            content={condition ? <ComponentA title="hello" /> : undefined}
        />
    );
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")
        foo = file.get_function("foo")
        ternary = foo.code_block.statements[0].value.value.props[0].value.statement
        ternary.reduce_condition(True)
    # language=typescript jsx
    assert (
        file.content
        == """
function foo(): JSX.Element {
    return (
        <Container
            content={<ComponentA title="hello" />}
        />
    );
}
"""
    )
