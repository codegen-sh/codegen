from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.dataclasses.usage import UsageType
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_function_is_reexported_from_separate_file(tmpdir) -> None:
    EXPORTER_FILENANE = "exporter.ts"
    # language=typescript
    EXPORTER_FILE_CONTENT = """
    export function foo() {}
    """

    REEXPORTER_FILENAME = "reexporter.ts"
    # language=typescript
    REEXPORTER_FILE_CONTENT = """
    export {foo} from "./exporter.ts";
    """

    IMPORTER_FILENAME = "importer.ts"
    # language=typescript
    IMPORTER_FILE_CONTENT = """
    import {foo} from "./reexporter.ts";
    """
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={EXPORTER_FILENANE: EXPORTER_FILE_CONTENT, REEXPORTER_FILENAME: REEXPORTER_FILE_CONTENT, IMPORTER_FILENAME: IMPORTER_FILE_CONTENT},
    ) as codebase:
        exporter_file = codebase.get_file(EXPORTER_FILENANE)
        reexporter_file = codebase.get_file(REEXPORTER_FILENAME)
        importer_file = codebase.get_file(IMPORTER_FILENAME)

        foo_symbol = exporter_file.get_symbol("foo")
        assert len(foo_symbol.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == 2
        assert set(foo_symbol.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == {exporter_file.get_export("foo"), reexporter_file.get_import("foo")}
        assert len(foo_symbol.symbol_usages) == 4
        assert set(foo_symbol.symbol_usages) == {exporter_file.get_export("foo"), reexporter_file.get_export("foo"), reexporter_file.get_import("foo"), importer_file.get_import("foo")}
        assert foo_symbol.is_reexported is True


def test_function_is_reexported_with_star_export(tmpdir) -> None:
    EXPORTER_FILENANE = "exporter.ts"
    # language=typescript
    EXPORTER_FILE_CONTENT = """
    export function foo() {}
    """

    REEXPORTER_FILENAME = "reexporter.ts"
    # language=typescript
    REEXPORTER_FILE_CONTENT = """
    export * from "./exporter.ts";
    """

    IMPORTER_FILENAME = "importer.ts"
    # language=typescript
    IMPORTER_FILE_CONTENT = """
    import {foo} from "./reexporter.ts";
    """
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={EXPORTER_FILENANE: EXPORTER_FILE_CONTENT, REEXPORTER_FILENAME: REEXPORTER_FILE_CONTENT, IMPORTER_FILENAME: IMPORTER_FILE_CONTENT},
    ) as codebase:
        exporter_file = codebase.get_file(EXPORTER_FILENANE)
        reexporter_file = codebase.get_file(REEXPORTER_FILENAME)
        importer_file = codebase.get_file(IMPORTER_FILENAME)
        foo_symbol = exporter_file.get_symbol("foo")

        assert importer_file.imports[0].imported_symbol == reexporter_file
        assert importer_file.imports[0].resolved_symbol == foo_symbol
        assert reexporter_file.exports[0].symbol_usages(UsageType.DIRECT | UsageType.CHAINED) == [importer_file.get_import("foo")]
        assert foo_symbol.symbol_usages(UsageType.DIRECT | UsageType.CHAINED) == [exporter_file.get_export("foo")]
        assert len(foo_symbol.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == 1
        assert len(foo_symbol.symbol_usages) == 2
        assert set(foo_symbol.symbol_usages) == {exporter_file.get_export("foo"), importer_file.imports[0]}
        assert foo_symbol.is_reexported is True
