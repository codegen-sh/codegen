from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.typescript.file import TSFile


def test_reduce_binary_simple(tmpdir):
    # language=typescript
    content = """
function foo(): void {
    let a = false;
    let result = (a && b);
    console.log(result);
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")
        foo = file.get_function("foo")
        assign = foo.code_block.assignments[0]
        assert assign.name == "a"
        assign.reduce_condition(False)
    # language=typescript
    assert (
        file.content
        == """
function foo(): void {
    console.log(false);
}
    """
    )


def test_reduce_binary_object(tmpdir):
    # language=typescript
    content = """
function foo(): void {
    let a = false;
    let object = {
        a,
    };
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")
        foo = file.get_function("foo")
        assign = foo.code_block.assignments[0]
        assert assign.name == "a"
        assign.reduce_condition(False)
    # language=typescript
    assert (
        file.content
        == """
function foo(): void {
    let object = {
        a: false,
    };
}
    """
    )


def test_reduce_binary_complex_condition(tmpdir):
    # language=typescript
    content = """
function bar(): void {
    let x = true;
    let y = false;
    let result = (x || y) && b;
    console.log(result);
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file2.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file2.ts")
        bar = file.get_function("bar")
        assign_x = bar.code_block.assignments[0]
        assign_y = bar.code_block.assignments[1]
        assign_x.reduce_condition(True)
        assign_y.reduce_condition(False)
    # language=typescript
    assert (
        file.content
        == """
function bar(): void {
    let result = b;
    console.log(result);
}
    """
    )


def test_reduce_negation_condition(tmpdir):
    # language=typescript
    content = """
function baz(): void {
    let a = true;
    let notA = !a;
    let result = (notA || b);
    console.log(result);
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file3.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file3.ts")
        baz = file.get_function("baz")
        assign_notA = baz.code_block.assignments[1]
        assign_notA.reduce_condition(False)
    # language=typescript
    assert (
        file.content
        == """
function baz(): void {
    let a = true;
    let result = b;
    console.log(result);
}
    """
    )


def test_reduce_jsx_element(tmpdir):
    # language=typescript jsx
    content = """
const MyComponent: React.FC = () => {
    let isVisible = true;
    return (
        <div>
            {isVisible && <span>Visible</span>}
            {!isVisible && <span>Hidden</span>}
        </div>
    );
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file4.tsx": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file4.tsx")
        my_component = file.get_symbol("MyComponent")
        assign_isVisible = my_component.code_block.assignments[0]

        print(repr(assign_isVisible.usages[0].match.parent))
        assign_isVisible.reduce_condition(True)
    # language=typescript jsx
    assert (
        file.content
        == """
const MyComponent: React.FC = () => {
    return (
        <div>
            <span>Visible</span>
        </div>
    );
}
    """
    )


def test_reduce_jsx_element_keep(tmpdir):
    # language=typescript jsx
    content = """
const MyComponent: React.FC = () => {
    let isVisible = true;
    return (
        <div>
            {isVisible && otherVar}
        </div>
    );
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file4.tsx": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file4.tsx")
        my_component = file.get_symbol("MyComponent")
        assign_isVisible = my_component.code_block.assignments[0]

        print(repr(assign_isVisible.usages[0].match.parent))
        assign_isVisible.reduce_condition(True)
    # language=typescript jsx
    assert (
        file.content
        == """
const MyComponent: React.FC = () => {
    return (
        <div>
            {otherVar}
        </div>
    );
}
    """
    )


def test_reduce_complex_condition_with_JSX(tmpdir):
    # language=typescript jsx
    content = """
const AnotherComponent: React.FC = () => {
    let isActive = true;
    let result = isActive || isHidden;
    return (
        <div>
            {result && <span>Active and not Disabled</span>}
            {!result && <span>Inactive or Disabled</span>}
        </div>
    );
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file5.tsx": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file5.tsx")
        another_component = file.get_symbol("AnotherComponent")
        assign_isActive = another_component.code_block.assignments[0]
        assign_isActive.reduce_condition(True)
    # language=typescript jsx
    assert (
        file.content
        == """
const AnotherComponent: React.FC = () => {
    return (
        <div>
            <span>Active and not Disabled</span>
        </div>
    );
}
    """
    )
