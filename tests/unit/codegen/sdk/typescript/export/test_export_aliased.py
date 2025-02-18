from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.typescript.file import TSFile


def test_export_aliased(tmpdir):
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

        foo_export = next(e for e in exports if e.name == "foop")
        fuzz_export = next(e for e in exports if e.name == "fuzz")

        assert foo_export.is_aliased()
        assert not fuzz_export.is_aliased()
        assert foo_export.resolved_symbol == file.get_function("foo")
        assert fuzz_export.resolved_symbol == file.get_function("fuzz")


def test_export_aliased_multiple(tmpdir):
    # language=typescript
    content = """
function foo() {}
function bar() {}
function baz() {}

export { foo as foop, bar as barp, baz };
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("test.ts")
        exports = file.exports
        assert len(file.export_statements) == 1
        export_statement = file.export_statements[0]
        assert export_statement.source == "export { foo as foop, bar as barp, baz };"

        foo_export = next(e for e in exports if e.name == "foop")
        bar_export = next(e for e in exports if e.name == "barp")
        baz_export = next(e for e in exports if e.name == "baz")

        assert foo_export.is_aliased()
        assert bar_export.is_aliased()
        assert not baz_export.is_aliased()

        assert foo_export.resolved_symbol == file.get_function("foo")
        assert bar_export.resolved_symbol == file.get_function("bar")
        assert baz_export.resolved_symbol == file.get_function("baz")


def test_export_aliased_default(tmpdir):
    # language=typescript
    content = """
function foo() {}

export { foo as default };
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("test.ts")
        exports = file.exports
        assert len(file.export_statements) == 1
        export_statement = file.export_statements[0]
        assert export_statement.source == "export { foo as default };"

        default_export = next(e for e in exports if e.name == "default")
        assert default_export.is_aliased()
        assert default_export.resolved_symbol == file.get_function("foo")
