import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


@pytest.fixture
def ts_file(tmpdir):
    def _get_file(content: str):
        filename = "test.ts"
        with get_codebase_session(
            tmpdir=tmpdir,
            programming_language=ProgrammingLanguage.TYPESCRIPT,
            files={filename: content},
        ) as codebase:
            return codebase.get_file(filename)

    return _get_file


@pytest.fixture
def export_check(ts_file):
    def _export_check(*sources):
        file = ts_file("\n".join(sources))
        assert len(file.export_statements) == len(sources)
        for i, source in enumerate(sources):
            assert file.export_statements[i].source == source

    return _export_check


# 1. Named exports


def test_named_exports__export_const(export_check):
    export_check("export const variable = value;")


def test_named_exports__export_let(export_check):
    export_check("export let variable = value;")


def test_named_exports__export_var(export_check):
    export_check("export var variable = value;")


def test_named_exports__export_function(export_check):
    export_check("export function functionName() { /* ... */ }")


def test_named_exports__export_class(export_check):
    export_check("export class ClassName { /* ... */ }")


def test_named_exports__export_interface(export_check):
    export_check("export interface InterfaceName { /* ... */ }")


def test_named_exports__export_type(export_check):
    export_check("export type TypeName = value;")


def test_named_exports__export_enum(export_check):
    export_check("export enum EnumName { /* ... */ }")


# 2. Default exports


def test_default_exports__export_default_value(export_check):
    export_check("export default value;")


def test_default_exports__export_default_function(export_check):
    export_check("export default function() { /* ... */ }")


def test_default_exports__export_default_class(export_check):
    export_check("export default class { /* ... */ }")


# 3. Exporting declarations after they're defined


def test_defined_declarations__just_export_statement(export_check):
    export_check("export { variable, functionName, ClassName };")


# 4. Exporting with aliases


def test_exporting_with_aliases(export_check):
    export_check("export { variable as aliasName };")


# 5. Re-exporting


def test_reexporting__export_many_names(export_check):
    export_check("export { name1, name2 } from './other-module';")


def test_reexporting__export_many_names_with_aliases(export_check):
    export_check("export { import1 as name1, import2 as name2 } from './other-module';")


def test_reexporting__export_star(export_check):
    export_check("export * from './other-module';")


def test_reexporting__export_default(export_check):
    export_check("export { default } from './other-module';")


# 6. Combining default and named exports


def test_default_named__export_default_class(export_check):
    export_check("export default class { /* ... */ }")


def test_default_named__export_const(export_check):
    export_check("export const namedExport = value;")


# 7. Exporting types


def test_types__export_type_block(export_check):
    export_check("export type { SomeType } from './types';")


# 8. Exporting namespaces


def test_export_namespace(export_check):
    export_check("export namespace MyNamespace { export const something = value; }")


# 9. Exporting as a namespace


def test_export_star_as_namespace(export_check):
    export_check("export * as myNamespace from './module';")


# 10. Exporting declarations with modifiers


def test_declaration_with_modifiers__export_abstract_class(export_check):
    export_check("export abstract class AbstractClass { /* ... */ }")


def test_declaration_with_modifiers__export_const_enum(export_check):
    export_check("export const enum ConstEnum { /* ... */ }")


# 11. Exporting with generics


def test_generics__export_function(export_check):
    export_check("export function genericFunction<T>() { /* ... */ }")


def test_generics__export_class(export_check):
    export_check("export class GenericClass<T> { /* ... */ }")


def test_has_export_empty_file(tmpdir) -> None:
    # language=typescript
    content = ""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        assert file.has_export_statement_for_path("anything", "WILDCARD") is False
        assert file.has_export_statement_for_path("anything", "TYPE") is False
        assert file.has_export_statement_for_path("anything", "EXPORT") is False


def test_has_export_no_exports(tmpdir) -> None:
    # language=typescript
    content = """
    const x = 5;
    function test() {}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        assert file.has_export_statement_for_path("anything", "WILDCARD") is False
        assert file.has_export_statement_for_path("anything", "TYPE") is False
        assert file.has_export_statement_for_path("anything", "EXPORT") is False


def test_has_export_non_wildcard(tmpdir) -> None:
    # language=typescript
    content = """
    export { something } from './path';
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        assert file.has_export_statement_for_path("./path", "WILDCARD") is False
        assert file.has_export_statement_for_path("./path", "TYPE") is False
        assert file.has_export_statement_for_path("./path", "EXPORT") is True


def test_has_export_wrong_path(tmpdir) -> None:
    # language=typescript
    content = """
    export * from './wrong/path';
    export type { MyType } from './wrong/path2';
    export { something } from './wrong/path3';
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        assert file.has_export_statement_for_path("./correct/path", "WILDCARD") is False
        assert file.has_export_statement_for_path("./correct/path", "TYPE") is False
        assert file.has_export_statement_for_path("./correct/path", "EXPORT") is False


def test_has_export_multiple_exports(tmpdir) -> None:
    # language=typescript
    content = """
    export { something } from './path1';
    export * from './path2';
    export type { MyType } from './path3';
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        assert file.has_export_statement_for_path("./path1", "EXPORT") is True
        assert file.has_export_statement_for_path("./path2", "WILDCARD") is True
        assert file.has_export_statement_for_path("./path3", "TYPE") is True


def test_has_export_substring(tmpdir) -> None:
    # language=typescript
    content = """
    export * from './path/subpath';
    export type { MyType } from './type/subpath';
    export { something } from './export/subpath';
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        assert file.has_export_statement_for_path("./path", "WILDCARD") is False
        assert file.has_export_statement_for_path("./type", "TYPE") is False
        assert file.has_export_statement_for_path("./export", "EXPORT") is False


def test_has_export_case_sensitivity(tmpdir) -> None:
    # language=typescript
    content = """
    export * from './Path';
    export type { MyType } from './Type';
    export { something } from './Export';
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        assert file.has_export_statement_for_path("./path", "WILDCARD") is False
        assert file.has_export_statement_for_path("./type", "TYPE") is False
        assert file.has_export_statement_for_path("./export", "EXPORT") is False


def test_has_export_quote_types(tmpdir) -> None:
    # language=typescript
    content = """
    export * from "./path1";
    export type { MyType } from './path2';
    export { something } from "./path3";
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        assert file.has_export_statement_for_path("./path1", "WILDCARD") is True
        assert file.has_export_statement_for_path("./path2", "TYPE") is True
        assert file.has_export_statement_for_path("./path3", "EXPORT") is True


def test_has_export_mixed_types(tmpdir) -> None:
    # language=typescript
    content = """
    export * from './path';
    export type { MyType } from './path';
    export { something } from './path';
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        assert file.has_export_statement_for_path("./path", "WILDCARD") is True
        assert file.has_export_statement_for_path("./path", "TYPE") is True
        assert file.has_export_statement_for_path("./path", "EXPORT") is True


def test_has_export_default_parameter(tmpdir) -> None:
    # language=typescript
    content = """
    export { something } from './path';
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        # Testing the default export_type parameter (should be "EXPORT")
        assert file.has_export_statement_for_path("./path") is True


def test_get_export_statement_empty_file(tmpdir) -> None:
    # language=typescript
    content = ""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        assert file.get_export_statement_for_path("anything", "WILDCARD") is None
        assert file.get_export_statement_for_path("anything", "TYPE") is None
        assert file.get_export_statement_for_path("anything", "EXPORT") is None


def test_get_export_statement_no_exports(tmpdir) -> None:
    # language=typescript
    content = """
    const x = 5;
    function test() {}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        assert file.get_export_statement_for_path("anything", "WILDCARD") is None
        assert file.get_export_statement_for_path("anything", "TYPE") is None
        assert file.get_export_statement_for_path("anything", "EXPORT") is None


def test_get_export_statement_non_wildcard(tmpdir) -> None:
    # language=typescript
    content = """
    export { something } from './path';
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        assert file.get_export_statement_for_path("./path", "WILDCARD") is None
        assert file.get_export_statement_for_path("./path", "TYPE") is None
        export_stmt = file.get_export_statement_for_path("./path", "EXPORT")
        assert export_stmt is not None
        assert export_stmt.source == "export { something } from './path';"
        assert not export_stmt.is_type_export()
        assert not export_stmt.is_wildcard_export()


def test_get_export_statement_multiple_exports(tmpdir) -> None:
    # language=typescript
    content = """
    export { something } from './path1';
    export * from './path2';
    export type { MyType } from './path3';
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        regular_stmt = file.get_export_statement_for_path("./path1", "EXPORT")
        wildcard_stmt = file.get_export_statement_for_path("./path2", "WILDCARD")
        type_stmt = file.get_export_statement_for_path("./path3", "TYPE")

        assert regular_stmt is not None
        assert regular_stmt.source == "export { something } from './path1';"
        assert not regular_stmt.is_type_export()
        assert not regular_stmt.is_wildcard_export()

        assert wildcard_stmt is not None
        assert wildcard_stmt.source == "export * from './path2';"
        assert wildcard_stmt.is_wildcard_export()

        assert type_stmt is not None
        assert type_stmt.source == "export type { MyType } from './path3';"
        assert type_stmt.is_type_export()


def test_get_export_statement_mixed_types(tmpdir) -> None:
    # language=typescript
    path_content = """
    export type MyType = {
        prop1: string;
        prop2: number;
    };

    export const something = "test";
    """

    main_content = """
    export * from './path';
    export type { MyType } from './path';
    export { something } from './path';
    """

    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": main_content, "path.ts": path_content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")

        wildcard_stmt = file.get_export_statement_for_path("./path", "WILDCARD")
        type_stmt = file.get_export_statement_for_path("./path", "TYPE")
        regular_stmt = file.get_export_statement_for_path("./path", "EXPORT")

        assert wildcard_stmt is not None
        assert wildcard_stmt.source == "export * from './path';"
        assert wildcard_stmt.is_wildcard_export()

        assert type_stmt is not None
        assert type_stmt.source == "export type { MyType } from './path';"
        assert type_stmt.is_type_export()

        assert regular_stmt is not None
        assert regular_stmt.source == "export { something } from './path';"
        assert not regular_stmt.is_type_export()
        assert not regular_stmt.is_wildcard_export()


def test_get_export_statement_quote_types(tmpdir) -> None:
    # language=typescript
    content = """
    export * from "./path1";
    export type { MyType } from './path2';
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        wildcard_stmt = file.get_export_statement_for_path("./path1", "WILDCARD")
        type_stmt = file.get_export_statement_for_path("./path2", "TYPE")

        assert wildcard_stmt is not None
        assert wildcard_stmt.source == 'export * from "./path1";'
        assert wildcard_stmt.is_wildcard_export()

        assert type_stmt is not None
        assert type_stmt.source == "export type { MyType } from './path2';"
        assert type_stmt.is_type_export()
