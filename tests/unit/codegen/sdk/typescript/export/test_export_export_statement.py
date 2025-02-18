from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.typescript.file import TSFile


def test_export_export_statement(tmpdir):
    # language=typescript
    content = """
function foo() {}
function fuzz() {}

export { foo as foop, fuzz };
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("test.ts")
        exports = file.exports
        assert len(file.export_statements) == 1
        export_statement = file.export_statements[0]
        assert export_statement.source == "export { foo as foop, fuzz };"
        assert set(export_statement.exports) == set(file.exports)
        export_parents = [(e.export_statement, e.name) for e in exports]
        assert export_parents == [
            (file.export_statements[0], "foop"),
            (file.export_statements[0], "fuzz"),
        ]


def test_remove_export(tmpdir):
    # language=typescript
    content = """
function foo() {}
function bar() {}
function baz() {}
export { foo as foop, bar as barp, baz };
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("test.ts")
        export_statement = file.export_statements[0]
        export_statement.exports.pop()
        export_statement.exports.pop(0)

    # language=typescript
    assert (
        file.content
        == """
function foo() {}
function bar() {}
function baz() {}
export { bar as barp };
    """
    )


def test_remove_all_exports(tmpdir):
    # language=typescript
    content = """
function foo() {}
function bar() {}
export { foo, bar };
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("test.ts")
        export_statement = file.export_statements[0]
        export_statement.exports.clear()

    # language=typescript
    assert (
        file.content
        == """
function foo() {}
function bar() {}
    """
    )


def test_add_export(tmpdir):
    # language=typescript
    content = """
function foo() {}
function bar() {}
export { foo };
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("test.ts")
        export_statement = file.export_statements[0]
        original_export = export_statement.exports[0]
        export_statement.exports.append("bar")

    # language=typescript
    assert (
        file.content
        == """
function foo() {}
function bar() {}
export { foo, bar };
    """
    )


def test_insert_export_at_start(tmpdir):
    # language=typescript
    content = """
function foo() {}
function bar() {}
export { bar };
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("test.ts")
        export_statement = file.export_statements[0]
        original_export = export_statement.exports[0]
        export_statement.exports.insert(0, "bar")

    # language=typescript
    assert (
        file.content
        == """
function foo() {}
function bar() {}
export { bar, bar };
    """
    )


def test_remove_middle_export(tmpdir):
    # language=typescript
    content = """
function foo() {}
function bar() {}
function baz() {}
export { foo, bar, baz };
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("test.ts")
        export_statement = file.export_statements[0]
        del export_statement.exports[1]

    # language=typescript
    assert (
        file.content
        == """
function foo() {}
function bar() {}
function baz() {}
export { foo, baz };
    """
    )


def test_remove_inline_export(tmpdir):
    # language=typescript
    content = """
export function foo() {}
export const bar = 123;
export class Baz {}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("test.ts")
        export_statement = file.export_statements[1]  # Get the const export
        export_statement.exports[0].remove()

    # language=typescript
    assert (
        file.content
        == """
export function foo() {}
export class Baz {}
    """
    )


def test_add_remove_reexport_inline(tmpdir):
    # language=typescript
    content = """
export { foo, bar } from './other';
export { baz } from './another';
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("test.ts")
        # Remove one re-export
        export_statement = file.export_statements[0]
        del export_statement.exports[0]

        # Add another re-export from second statement
        second_export = file.export_statements[1]
        second_export.exports.append("boop")

    # language=typescript
    assert (
        file.content
        == """
export { bar } from './other';
export { baz, boop } from './another';
    """
    )


def test_remove_namespace_export(tmpdir):
    # language=typescript
    content = """
export namespace Foo {
    export const bar = 123;
}
export namespace Baz {
    export function qux() {}
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("test.ts")
        export_statement = file.export_statements[0]  # Get first namespace export
        export_statement.exports[0].remove()

    # language=typescript
    assert (
        file.content
        == """
export namespace Baz {
    export function qux() {}
}
    """
    )


def test_remove_add_wildcard_export(tmpdir):
    # language=typescript
    content = """
export * from './foo';
export * as bar from './bar';
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("test.ts")
        # Remove first wildcard export
        export_statement = file.export_statements[0]
        export_statement.exports[0].remove()

    # language=typescript
    assert (
        file.content
        == """
export * as bar from './bar';
    """
    )


def test_remove_all_exports_multiline(tmpdir):
    # language=typescript
    content = """
function foo() {}
function bar() {}
function baz() {}
export {
    foo as foop,
    bar as barp,
    baz,
};
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("test.ts")
        export_statement = file.export_statements[0]
        export_statement.exports.clear()

    # language=typescript
    assert (
        file.content
        == """
function foo() {}
function bar() {}
function baz() {}
    """
    )
