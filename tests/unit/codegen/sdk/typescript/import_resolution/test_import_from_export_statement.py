from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.enums import ImportType
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.typescript.file import TSFile


def test_from_export_statement_default(tmpdir) -> None:
    # language=typescript
    content = """
export { default } from './m';
    """
    # language=typescript
    content2 = """
export default function foo() {}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content, "m.ts": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("file.ts")
        m_file: TSFile = codebase.get_file("m.ts")
        assert len(file.imports) == 1
        assert len(file.exports) == 1
        imp = file.imports[0]
        assert imp.source == "export { default } from './m';"
        assert imp.name == "default"
        assert imp.module.source == "'./m'"
        assert imp.symbol_name.source == "default"
        assert imp.alias.source == "default"
        assert imp.import_type == ImportType.DEFAULT_EXPORT
        assert not imp.is_wildcard_import()
        assert imp.is_module_import()
        assert not imp.is_type_import()
        assert imp.resolved_symbol == m_file.get_function("foo")

        export = file.exports[0]
        assert export.source == "export { default } from './m';"
        assert export.is_default_export()
        assert not export.is_type_export()
        assert export.is_reexport()
        assert not export.is_wildcard_export()
        assert export.declared_symbol == imp
        assert export.exported_symbol == imp
        assert export.resolved_symbol == m_file.get_function("foo")


def test_from_export_statement_default_alias(tmpdir) -> None:
    # language=typescript
    content = """
export { default as foo } from './m';
export { default as bar } from './m';
    """
    # language=typescript
    content2 = """
export default function foo() {}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content, "m.ts": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("file.ts")
        m_file: TSFile = codebase.get_file("m.ts")
        assert len(file.imports) == 2
        assert len(file.exports) == 2

        assert file.imports[0].source == "export { default as foo } from './m';"
        assert file.imports[0].name == "foo"
        assert file.imports[0].module.source == "'./m'"
        assert file.imports[0].symbol_name.source == "default"
        assert file.imports[0].alias.source == "foo"
        assert file.imports[0].import_type == ImportType.DEFAULT_EXPORT
        assert not file.imports[0].is_wildcard_import()
        assert file.imports[0].is_module_import()
        assert not file.imports[0].is_type_import()
        assert file.imports[0].resolved_symbol == m_file.get_function("foo")

        assert file.imports[1].source == "export { default as bar } from './m';"
        assert file.imports[1].name == "bar"
        assert file.imports[1].module.source == "'./m'"
        assert file.imports[1].symbol_name.source == "default"
        assert file.imports[1].alias.source == "bar"
        assert file.imports[1].import_type == ImportType.DEFAULT_EXPORT
        assert not file.imports[1].is_wildcard_import()
        assert file.imports[1].is_module_import()
        assert not file.imports[1].is_type_import()
        assert file.imports[1].resolved_symbol == m_file.get_function("foo")

        assert file.exports[0].source == "export { default as foo } from './m';"
        assert file.exports[0].is_default_export()
        assert not file.exports[0].is_type_export()
        assert file.exports[0].is_reexport()
        assert not file.exports[0].is_wildcard_export()
        assert file.exports[0].declared_symbol == file.imports[0]
        assert file.exports[0].exported_symbol == file.imports[0]
        assert file.exports[0].resolved_symbol == m_file.get_function("foo")

        assert file.exports[1].source == "export { default as bar } from './m';"
        assert file.exports[1].is_default_export()
        assert not file.exports[1].is_type_export()
        assert file.exports[1].is_reexport()
        assert not file.exports[1].is_wildcard_export()
        assert file.exports[1].declared_symbol == file.imports[1]
        assert file.exports[1].exported_symbol == file.imports[1]
        assert file.exports[1].resolved_symbol == m_file.get_function("foo")


def test_from_export_statement_named_alias(tmpdir) -> None:
    # language=typescript
    content = """
export { foo as someOtherName, bar } from './m';
    """
    # language=typescript
    content2 = """
export function foo() {}
export function bar() {}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content, "m.ts": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("file.ts")
        m_file: TSFile = codebase.get_file("m.ts")
        assert len(file.imports) == 2
        assert len(file.exports) == 2

        assert file.imports[1].source == "export { foo as someOtherName, bar } from './m';"
        assert file.imports[1].name == "bar"
        assert file.imports[1].module.source == "'./m'"
        assert file.imports[1].symbol_name.source == "bar"
        assert file.imports[1].alias.source == "bar"
        assert file.imports[1].import_type == ImportType.NAMED_EXPORT
        assert not file.imports[1].is_wildcard_import()
        assert not file.imports[1].is_module_import()
        assert not file.imports[1].is_type_import()
        assert file.imports[1].resolved_symbol == m_file.get_function("bar")

        assert file.exports[0].source == "export { foo as someOtherName, bar } from './m';"
        assert not file.exports[0].is_default_export()
        assert not file.exports[0].is_type_export()
        assert file.exports[0].is_reexport()
        assert not file.exports[0].is_wildcard_export()
        assert file.exports[0].declared_symbol == file.imports[0]
        assert file.exports[0].exported_symbol == file.imports[0]
        assert file.exports[0].resolved_symbol == m_file.get_function("foo")

        assert file.exports[1].source == "export { foo as someOtherName, bar } from './m';"
        assert not file.exports[1].is_default_export()
        assert not file.exports[1].is_type_export()
        assert file.exports[1].is_reexport()
        assert not file.exports[1].is_wildcard_export()
        assert file.exports[1].declared_symbol == file.imports[1]
        assert file.exports[1].exported_symbol == file.imports[1]
        assert file.exports[1].resolved_symbol == m_file.get_function("bar")


def test_from_export_statement_type(tmpdir) -> None:
    # language=typescript
    content = """
export type { SomeType } from './m';
    """
    # language=typescript
    content2 = """
export type SomeType = {}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content, "m.ts": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("file.ts")
        m_file: TSFile = codebase.get_file("m.ts")
        assert len(file.imports) == 1
        assert len(file.exports) == 1

        assert file.imports[0].source == "export type { SomeType } from './m';"
        assert file.imports[0].name == "SomeType"
        assert file.imports[0].module.source == "'./m'"
        assert file.imports[0].symbol_name.source == "SomeType"
        assert file.imports[0].alias.source == "SomeType"
        assert file.imports[0].import_type == ImportType.NAMED_EXPORT
        assert not file.imports[0].is_wildcard_import()
        assert not file.imports[0].is_module_import()
        assert file.imports[0].is_type_import()
        assert file.imports[0].resolved_symbol == m_file.get_type("SomeType")

        assert file.exports[0].source == "export type { SomeType } from './m';"
        assert not file.exports[0].is_default_export()
        assert file.exports[0].is_type_export()
        assert file.exports[0].is_reexport()
        assert not file.exports[0].is_wildcard_export()
        assert file.exports[0].declared_symbol == file.imports[0]
        assert file.exports[0].exported_symbol == file.imports[0]
        assert file.exports[0].resolved_symbol == m_file.get_type("SomeType")


def test_from_export_statement_unnamed_wildcard(tmpdir) -> None:
    # language=typescript
    content = """
export * from './m';
    """
    # language=typescript
    content2 = """
export type SomeType = {}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content, "m.ts": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("file.ts")
        m_file: TSFile = codebase.get_file("m.ts")
        assert len(file.imports) == 1
        assert len(file.exports) == 1

        assert file.imports[0].source == "export * from './m';"
        assert file.imports[0].name is None
        assert file.imports[0].module.source == "'./m'"
        assert file.imports[0].symbol_name is None
        assert file.imports[0].alias is None
        assert file.imports[0].import_type == ImportType.WILDCARD
        assert file.imports[0].is_wildcard_import()
        assert file.imports[0].is_module_import()
        assert not file.imports[0].is_type_import()
        assert file.imports[0].resolved_symbol == m_file

        assert file.exports[0].source == "export * from './m';"
        assert not file.exports[0].is_default_export()
        assert not file.exports[0].is_type_export()
        assert file.exports[0].is_reexport()
        assert file.exports[0].is_wildcard_export()
        assert file.exports[0].declared_symbol == file.imports[0]
        assert file.exports[0].exported_symbol == file.imports[0]
        assert file.exports[0].resolved_symbol == m_file


def test_from_export_statement_named_wildcard(tmpdir) -> None:
    # language=typescript
    content = """
export * as AliasedName from './m';
    """
    # language=typescript
    content2 = """
export type SomeType = {}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content, "m.ts": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("file.ts")
        m_file: TSFile = codebase.get_file("m.ts")
        assert len(file.imports) == 1
        assert len(file.exports) == 1

        assert file.imports[0].source == "export * as AliasedName from './m';"
        assert file.imports[0].module.source == "'./m'"
        assert file.imports[0].name == "AliasedName"
        assert file.imports[0].symbol_name == "* as AliasedName"
        assert file.imports[0].alias.source == "AliasedName"
        assert file.imports[0].import_type == ImportType.WILDCARD
        assert file.imports[0].is_wildcard_import()
        assert file.imports[0].is_module_import()
        assert not file.imports[0].is_type_import()
        assert file.imports[0].resolved_symbol == m_file

        assert file.exports[0].source == "export * as AliasedName from './m';"
        assert not file.exports[0].is_default_export()
        assert not file.exports[0].is_type_export()
        assert file.exports[0].is_reexport()
        assert file.exports[0].is_wildcard_export()
        assert file.exports[0].declared_symbol == file.imports[0]
        assert file.exports[0].exported_symbol == file.imports[0]
        assert file.exports[0].resolved_symbol == m_file
