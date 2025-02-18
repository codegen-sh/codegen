from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.dataclasses.usage import UsageType
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.typescript.file import TSFile


def test_resolve_export_with_declared_symbols(tmpdir) -> None:
    # language=typescript
    content = """
export const a = value;
export let b = value;
export var c = value;
export function functionName() {}
export function* namedGenerator() {}
export const namedArrowFunction = () => {}
export class ClassName {}
export interface InterfaceName {}
export type TypeName = {};
export enum EnumName {}
export namespace MyNamespace {}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("file.ts")
        exports = file.exports
        assert len(file.imports) == 0
        assert len(exports) == 11
        # TODO: update EnumName once properly parsed (CG-8697)
        assert set(exp.name for exp in file.exports) == {
            "a",
            "b",
            "c",
            "functionName",
            "namedGenerator",
            "namedArrowFunction",
            "ClassName",
            "InterfaceName",
            "TypeName",
            "EnumName",
            "MyNamespace",
        }
        assert all(file.get_export(exp.name) == exp for exp in file.exports)
        assert exports[0].declared_symbol == exports[0].exported_symbol == exports[0].resolved_symbol == file.get_global_var("a")
        assert exports[1].declared_symbol == exports[1].exported_symbol == exports[1].resolved_symbol == file.get_global_var("b")
        assert exports[2].declared_symbol == exports[2].exported_symbol == exports[2].resolved_symbol == file.get_global_var("c")
        assert exports[3].declared_symbol == exports[3].exported_symbol == exports[3].resolved_symbol == file.get_function("functionName")
        assert exports[4].declared_symbol == exports[4].exported_symbol == exports[4].resolved_symbol == file.get_function("namedGenerator")
        assert exports[5].declared_symbol == exports[5].exported_symbol == exports[5].resolved_symbol == file.get_function("namedArrowFunction")
        assert exports[6].declared_symbol == exports[6].exported_symbol == exports[6].resolved_symbol == file.get_class("ClassName")
        assert exports[7].declared_symbol == exports[7].exported_symbol == exports[7].resolved_symbol == file.get_interface("InterfaceName")
        assert exports[8].declared_symbol == exports[8].exported_symbol == exports[8].resolved_symbol == file.get_type("TypeName")
        assert exports[10].declared_symbol == exports[10].exported_symbol == exports[10].resolved_symbol == file.get_namespace("MyNamespace")
        assert all(not exp.is_default_export() for exp in exports)
        assert [exp.is_type_export() for exp in exports].count(True) == 1
        assert all(not exp.is_reexport() for exp in exports)
        assert all(not exp.is_wildcard_export() for exp in exports)


def test_resolve_export_with_declared_values(tmpdir) -> None:
    # language=typescript
    content = """
export default function() {}
export default function*() {}
export default () => {}
export default class {}
export default { myfunc1, myfunc2 } // object
export default [1, 2, 3]            // array
export default 42                   // number
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("file.ts")
        exports = file.exports
        assert len(file.imports) == 0
        assert len(exports) == 8
        assert all(file.get_export(exp.name) == exp for exp in exports)
        assert [exp.name for exp in file.exports] == ["function() {}", "function*() {}", "() => {}", "class {}", "myfunc1", "myfunc2", "[1, 2, 3]", "42"]
        assert [exp.declared_symbol.source if exp.declared_symbol else None for exp in exports] == [
            "export default function() {}",
            "export default function*() {}",
            "export default () => {}",
            "export default class {}",
            None,
            None,
            None,
            None,
        ]
        assert all(exp.declared_symbol == exp.exported_symbol for exp in exports)
        assert all(exp.declared_symbol == exp.resolved_symbol for exp in exports)
        assert all(exp.is_default_export() for exp in exports)
        assert all(not exp.is_type_export() for exp in exports)
        assert all(not exp.is_reexport() for exp in exports)
        assert all(not exp.is_wildcard_export() for exp in exports)


def test_resolve_export_with_export_clause_named_symbol(tmpdir) -> None:
    # language=typescript
    content = """
const variable = value;
function functionName() {}
class ClassName {}

export { variable, functionName, ClassName };
export { variable as aliasName };
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("file.ts")
        exports = file.exports
        assert len(file.imports) == 0
        assert len(exports) == 4
        assert all(file.get_export(exp.name) == exp for exp in exports)
        assert [exp.name for exp in file.exports] == ["variable", "functionName", "ClassName", "aliasName"]
        assert all(exp.declared_symbol is None for exp in exports)
        assert all(exp.exported_symbol == exp.resolved_symbol for exp in exports)
        assert exports[0].resolved_symbol == file.get_global_var("variable")
        assert exports[1].resolved_symbol == file.get_function("functionName")
        assert exports[2].resolved_symbol == file.get_class("ClassName")
        assert exports[3].resolved_symbol == file.get_global_var("variable")

        assert all(not exp.is_default_export() for exp in exports)
        assert all(not exp.is_type_export() for exp in exports)
        assert all(not exp.is_reexport() for exp in exports)
        assert all(not exp.is_wildcard_export() for exp in exports)


def test_resolve_export_with_export_clause_named_imports(tmpdir) -> None:
    # language=typescript
    reexporter_content = """
import { variable, functionName, ClassName } from './definer'

export { variable, functionName, ClassName };
export { variable as aliasName };
    """
    # language=typescript
    definer_content = """
export const variable = value;
export function functionName() {}
export class ClassName {}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"reexporter.ts": reexporter_content, "definer.ts": definer_content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        reexporter_file: TSFile = codebase.get_file("reexporter.ts")
        definer_file: TSFile = codebase.get_file("definer.ts")
        reexported_exports = reexporter_file.exports
        assert len(reexporter_file.imports) == 3
        assert len(reexported_exports) == 4
        assert all(reexporter_file.get_export(exp.name) == exp for exp in reexported_exports)
        assert [exp.name for exp in reexporter_file.exports] == ["variable", "functionName", "ClassName", "aliasName"]
        assert all(exp.declared_symbol is None for exp in reexported_exports)
        assert all(exp.exported_symbol != exp.resolved_symbol for exp in reexported_exports)
        assert reexported_exports[0].exported_symbol == reexporter_file.get_import("variable")
        assert reexported_exports[1].exported_symbol == reexporter_file.get_import("functionName")
        assert reexported_exports[2].exported_symbol == reexporter_file.get_import("ClassName")
        assert reexported_exports[3].exported_symbol == reexporter_file.get_import("variable")
        assert reexported_exports[0].resolved_symbol == definer_file.get_global_var("variable")
        assert reexported_exports[1].resolved_symbol == definer_file.get_function("functionName")
        assert reexported_exports[2].resolved_symbol == definer_file.get_class("ClassName")
        assert reexported_exports[3].resolved_symbol == definer_file.get_global_var("variable")

        assert all(not exp.is_default_export() for exp in reexported_exports)
        assert all(not exp.is_type_export() for exp in reexported_exports)
        assert all(exp.is_reexport() for exp in reexported_exports)
        assert all(not exp.is_wildcard_export() for exp in reexported_exports)


def test_resolve_export_as_reexport(tmpdir) -> None:
    # language=typescript
    content = """
export { a, b } from './m';
export { foo as bar } from './m';
export { default } from './m';
export * from './m';
export * as myModule from './m';
    """
    # language=typescript
    content2 = """
export const a = value;
export const b = value;
export function foo() {}
export default class ClassName {}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content, "m.ts": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("file.ts")
        m_file: TSFile = codebase.get_file("m.ts")
        imports = file.imports
        exports = file.exports
        assert len(imports) == 6
        assert len(exports) == 6
        assert all(file.get_export(exp.name) == exp for exp in exports if exp.name)
        assert [exp.name for exp in file.exports] == ["a", "b", "bar", "default", None, "myModule"]
        assert all(exp.declared_symbol == imports[i] for i, exp in enumerate(exports))
        assert all(exp.exported_symbol != exp.resolved_symbol for exp in exports)
        assert exports[0].resolved_symbol == m_file.get_global_var("a")
        assert exports[1].resolved_symbol == m_file.get_global_var("b")
        assert exports[2].resolved_symbol == m_file.get_function("foo")
        assert exports[3].resolved_symbol == m_file.get_class("ClassName")
        assert exports[4].resolved_symbol == m_file
        assert exports[5].resolved_symbol == m_file

        assert exports[3].is_default_export()
        assert all(not exp.is_default_export() for exp in exports if exp != exports[3])
        assert all(not exp.is_type_export() for exp in exports)
        assert all(exp.is_reexport() for exp in exports)
        assert not exports[0].is_wildcard_export()
        assert not exports[1].is_wildcard_export()
        assert not exports[2].is_wildcard_export()
        assert not exports[3].is_wildcard_export()
        assert exports[4].is_wildcard_export()
        assert exports[5].is_wildcard_export()


def test_resolve_export_with_type_export(tmpdir) -> None:
    # language=typescript
    content = """
export type { SomeType } from './m';
export type MyType = {};
    """
    # language=typescript
    content2 = """
export type SomeType = {}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content, "m.ts": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("file.ts")
        m_file: TSFile = codebase.get_file("m.ts")
        imports = file.imports
        exports = file.exports
        assert len(imports) == 1
        assert len(exports) == 2
        assert all(file.get_export(exp.name) == exp for exp in exports)
        assert [exp.name for exp in file.exports] == ["SomeType", "MyType"]

        assert exports[0].declared_symbol == imports[0]
        assert exports[0].exported_symbol == imports[0]
        assert exports[0].resolved_symbol == m_file.get_type("SomeType")
        assert exports[0].is_reexport()

        assert exports[1].declared_symbol == file.get_type("MyType")
        assert exports[1].exported_symbol == file.get_type("MyType")
        assert exports[1].resolved_symbol == file.get_type("MyType")
        assert not exports[1].is_reexport()

        assert all(not exp.is_default_export() for exp in exports)
        assert all(exp.is_type_export() for exp in exports)
        assert all(not exp.is_wildcard_export() for exp in exports)


def test_resolve_export_assignment(tmpdir) -> None:
    # language=typescript
    content = """
function f1() {}
function f2() {}
class MyClass {}

export = MyClass;
export = function myfunc() {};
export = function() {};
export = { f1, f2 };
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("file.ts")
        imports = file.imports
        exports = file.exports
        assert len(imports) == 0
        assert len(exports) == 5
        assert len(file.functions) == 4
        assert all(file.get_export(exp.name) == exp for exp in exports)
        assert [exp.name for exp in file.exports] == ["MyClass", "myfunc", "function() {}", "f1", "f2"]

        assert exports[0].source == "export = MyClass;"
        assert exports[0].declared_symbol is None
        assert exports[0].exported_symbol == file.get_class("MyClass")
        assert exports[0].resolved_symbol == file.get_class("MyClass")
        assert not exports[0].is_reexport()
        assert exports[0].is_default_export()
        assert not exports[0].is_wildcard_export()

        assert exports[1].source == "export = function myfunc() {};"
        assert exports[1].declared_symbol == file.get_function("myfunc")
        assert exports[1].exported_symbol == file.get_function("myfunc")
        assert exports[1].resolved_symbol == file.get_function("myfunc")
        assert not exports[1].is_reexport()
        assert exports[1].is_default_export()
        assert not exports[1].is_wildcard_export()

        assert exports[2].source == "export = function() {};"
        assert exports[2].declared_symbol == file.functions[3]
        assert exports[2].exported_symbol == file.functions[3]
        assert exports[2].resolved_symbol == file.functions[3]
        assert not exports[2].is_reexport()
        assert exports[2].is_default_export()
        assert not exports[2].is_wildcard_export()

        assert exports[3].source == "export = { f1, f2 };"
        assert exports[3].declared_symbol is None
        assert exports[3].exported_symbol == file.get_function("f1")
        assert exports[3].resolved_symbol == file.get_function("f1")
        assert not exports[3].is_reexport()
        assert exports[3].is_default_export()
        assert not exports[3].is_wildcard_export()

        assert exports[4].source == "export = { f1, f2 };"
        assert exports[4].declared_symbol is None
        assert exports[4].exported_symbol == file.get_function("f2")
        assert exports[4].resolved_symbol == file.get_function("f2")
        assert not exports[4].is_reexport()
        assert exports[4].is_default_export()
        assert not exports[4].is_wildcard_export()

        assert all(exp.is_default_export() for exp in exports)
        assert all(not exp.is_type_export() for exp in exports)


def test_resolve_default_and_named_exports(tmpdir) -> None:
    # language=typescript
    content1 = """
function myfunc1() {}
function myfunc2() {}
function myfunc3() {}

export default { myfunc1, myfunc2 }
export { myfunc3 }
    """
    # language=typescript
    content2 = """
import fileA, { myfunc3 } from './file1'

function foo() {
    fileA.myfunc1()
    fileA.myfunc2()
    myfunc3()
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file1.ts": content1, "file2.ts": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file1: TSFile = codebase.get_file("file1.ts")
        file2: TSFile = codebase.get_file("file2.ts")
        f1 = file1.get_function("myfunc1")
        f2 = file1.get_function("myfunc2")
        f3 = file1.get_function("myfunc3")
        assert f1.symbol_usages(UsageType.DIRECT) == [file1.get_export("myfunc1")]
        assert f2.symbol_usages(UsageType.DIRECT) == [file1.get_export("myfunc2")]
        assert f3.symbol_usages(UsageType.DIRECT | UsageType.CHAINED) == [file1.get_export("myfunc3"), file2.get_import("myfunc3")]


def test_resolve_namespace_object_export(tmpdir) -> None:
    # language=typescript
    content1 = """
import * as MathUtils from './mathUtils';
import * as StringUtils from './stringUtils';
import * as DateUtils from './dateUtils';

export default {
  Math: MathUtils,
  String: StringUtils,
  Date: DateUtils
};
    """
    # language=typescript
    content2 = """
import DefaultUtils from './file1';

function foo() {
    DefaultUtils.Math.myfunc1()
    DefaultUtils.Math.myfunc1()
    DefaultUtils.DateUtils.someFunc()   // incorrect usage of exported name; should be DefaultUtils.Date.someFunc()
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file1.ts": content1, "file2.ts": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file1: TSFile = codebase.get_file("file1.ts")
        file2: TSFile = codebase.get_file("file2.ts")
        math_utils_imp = file1.get_import("MathUtils")
        string_utils_imp = file1.get_import("StringUtils")
        date_utils_imp = file1.get_import("DateUtils")

        assert math_utils_imp.symbol_usages(UsageType.DIRECT) == [file1.get_export("Math")]
        assert string_utils_imp.symbol_usages(UsageType.DIRECT | UsageType.CHAINED) == [file1.get_export("String")]
        assert date_utils_imp.symbol_usages(UsageType.DIRECT | UsageType.CHAINED) == [file1.get_export("Date")]

        assert set(math_utils_imp.symbol_usages) == {file1.get_export("Math"), file2.get_function("foo")}
        assert set(string_utils_imp.symbol_usages) == {file1.get_export("String")}
        assert set(date_utils_imp.symbol_usages) == {file1.get_export("Date")}


def test_resolve_wildcard_reexport_through_index_files(tmpdir) -> None:
    FILENAME_1 = "dir/dir1/file1.ts"
    FILENAME_2 = "dir/dir1/index.ts"
    FILENAME_3 = "dir/index.ts"
    FILENAME_4 = "file4.ts"
    # language=typescript
    content1 = """
export function myFunction() {}
    """
    # language=typescript
    content2 = """
export * from './file1';
export * from './otherModule1';
export * from './otherModule2';
    """
    # language=typescript
    content3 = """
export * from './dir1';
export * from './dir2';
export * from './dir3';
    """
    # language=typescript
    content4 = """
import { myFunction } from './dir';

myFunction();
    """
    with get_codebase_session(
        tmpdir=tmpdir, files={FILENAME_1: content1, FILENAME_2: content2, FILENAME_3: content3, FILENAME_4: content4}, programming_language=ProgrammingLanguage.TYPESCRIPT
    ) as codebase:
        file1: TSFile = codebase.get_file(FILENAME_1)
        dir1_index: TSFile = codebase.get_file(FILENAME_2)
        dir_index: TSFile = codebase.get_file(FILENAME_3)
        file4: TSFile = codebase.get_file(FILENAME_4)

        my_function = file1.get_function("myFunction")
        assert set(my_function.symbol_usages) == {
            file1.get_export("myFunction"),
            file4.get_import("myFunction"),
            file4,
        }


def test_resolve_wildcard_reexport_through_explicit_index_files(tmpdir) -> None:
    FILENAME_1 = "dir/dir1/file1.ts"
    FILENAME_2 = "dir/dir1/index.ts"
    FILENAME_3 = "dir/index.ts"
    FILENAME_4 = "file4.ts"
    # language=typescript
    content1 = """
export function myFunction() {}
    """
    # language=typescript
    content2 = """
export * from './file1';
export * from './otherModule1/index.ts';
export * from './otherModule2/index.ts';
    """
    # language=typescript
    content3 = """
export * from './dir1/index.ts';
export * from './dir2/index.ts';
export * from './dir3/index.ts';
    """
    # language=typescript
    content4 = """
import { myFunction } from './dir/index.ts';

myFunction();
    """
    with get_codebase_session(
        tmpdir=tmpdir, files={FILENAME_1: content1, FILENAME_2: content2, FILENAME_3: content3, FILENAME_4: content4}, programming_language=ProgrammingLanguage.TYPESCRIPT
    ) as codebase:
        file1: TSFile = codebase.get_file(FILENAME_1)
        dir1_index: TSFile = codebase.get_file(FILENAME_2)
        dir_index: TSFile = codebase.get_file(FILENAME_3)
        file4: TSFile = codebase.get_file(FILENAME_4)

        my_function = file1.get_function("myFunction")
        assert set(my_function.symbol_usages) == {
            file1.get_export("myFunction"),
            file4.get_import("myFunction"),
            file4,
        }


def test_resolve_simple_wildcard_reexport(tmpdir) -> None:
    # language=typescript
    content1 = """
export function myFunction() {}
    """
    # language=typescript
    content2 = """
export * from './file1';
    """
    # language=typescript
    content3 = """
import { myFunction } from './file2';

myFunction();
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file1.ts": content1, "file2.ts": content2, "file3.ts": content3}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file1: TSFile = codebase.get_file("file1.ts")
        file2: TSFile = codebase.get_file("file2.ts")
        file3: TSFile = codebase.get_file("file3.ts")

        my_function = file1.get_function("myFunction")
        assert set(my_function.symbol_usages) == {
            file1.get_export("myFunction"),
            file3.get_import("myFunction"),
            file3,
        }
