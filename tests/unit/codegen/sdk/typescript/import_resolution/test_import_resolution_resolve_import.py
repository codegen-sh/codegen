from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.dataclasses.usage import UsageType
from codegen.sdk.enums import ImportType
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.core.file import SourceFile
    from codegen.sdk.core.import_resolution import Import, ImportResolution


def test_dynamic_import_module_export_const(tmpdir) -> None:
    # language=typescript
    content = """
const a = await import('./m');
const b = require('./m');
let c = await import('./m');
let d = require('./m');
e = await import('./m');
f = require('./m');
    """
    # language=typescript
    content2 = """
function a() {
    return
}
function b() {
    return
}
function c() {
    return
}
function d() {
    return
}
function e() {
    return
}
function f() {
    return
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content, "m.ts": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        m_file = codebase.get_file("m.ts")
        assert len(file.imports) == 6

        assert file.get_import("a").source == "const a = await import('./m');"
        assert file.get_import("a").module.source == "'./m'"
        assert file.get_import("a").symbol_name.source == "a"  # TODO: shouldn't this be null?
        assert file.get_import("a").name == "a"
        assert file.get_import("a").alias.source == "a"
        assert file.get_import("a").import_type == ImportType.MODULE
        assert not file.get_import("a").is_wildcard_import()
        assert file.get_import("a").is_module_import()
        assert not file.get_import("a").is_type_import()

        assert file.get_import("b").source == "const b = require('./m');"
        assert file.get_import("b").module.source == "'./m'"
        assert file.get_import("b").symbol_name.source == "b"  # TODO: shouldn't this be null?
        assert file.get_import("b").name == "b"
        assert file.get_import("b").alias.source == "b"
        assert file.get_import("b").import_type == ImportType.MODULE
        assert not file.get_import("b").is_wildcard_import()
        assert file.get_import("b").is_module_import()
        assert not file.get_import("b").is_type_import()

        assert file.get_import("c").source == "let c = await import('./m');"
        assert file.get_import("c").module.source == "'./m'"
        assert file.get_import("c").symbol_name.source == "c"  # TODO: shouldn't this be null?
        assert file.get_import("c").name == "c"
        assert file.get_import("c").alias.source == "c"
        assert file.get_import("c").import_type == ImportType.MODULE
        assert not file.get_import("c").is_wildcard_import()
        assert file.get_import("c").is_module_import()
        assert not file.get_import("c").is_type_import()

        assert file.get_import("d").source == "let d = require('./m');"
        assert file.get_import("d").module.source == "'./m'"
        assert file.get_import("d").symbol_name.source == "d"  # TODO: shouldn't this be null?
        assert file.get_import("d").name == "d"
        assert file.get_import("d").alias.source == "d"
        assert file.get_import("d").import_type == ImportType.MODULE
        assert not file.get_import("d").is_wildcard_import()
        assert file.get_import("d").is_module_import()
        assert not file.get_import("d").is_type_import()

        assert file.get_import("e").source == "e = await import('./m');"
        assert file.get_import("e").module.source == "'./m'"
        assert file.get_import("e").symbol_name.source == "e"  # TODO: shouldn't this be null?
        assert file.get_import("e").name == "e"
        assert file.get_import("e").alias.source == "e"
        assert file.get_import("e").import_type == ImportType.MODULE
        assert not file.get_import("e").is_wildcard_import()
        assert file.get_import("e").is_module_import()
        assert not file.get_import("e").is_type_import()

        assert file.get_import("f").source == "f = require('./m');"
        assert file.get_import("f").module.source == "'./m'"
        assert file.get_import("f").symbol_name.source == "f"  # TODO: shouldn't this be null?
        assert file.get_import("f").name == "f"
        assert file.get_import("f").alias.source == "f"
        assert file.get_import("f").import_type == ImportType.MODULE
        assert not file.get_import("f").is_wildcard_import()
        assert file.get_import("f").is_module_import()
        assert not file.get_import("f").is_type_import()

        assert file.get_import("a").resolved_symbol == m_file
        assert file.get_import("b").resolved_symbol == m_file
        assert file.get_import("c").resolved_symbol == m_file
        assert file.get_import("d").resolved_symbol == m_file
        assert file.get_import("e").resolved_symbol == m_file
        assert file.get_import("f").resolved_symbol == m_file


def test_dynamic_import_side_effect(tmpdir) -> None:
    # language=typescript
    content = """
await import('./m');
require('./m');
(await import('./m')).SomeType
require('./m').OtherType
"""
    # language=typescript
    content2 = """
export function a() {
    return
}
export function b() {
    return
}
export type SomeType = {};
export type OtherType = {};
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content, "m.ts": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        m_file = codebase.get_file("m.ts")
        assert len(file.imports) == 4
        import_imp = file.imports[0]
        require_imp = file.imports[1]
        import_type_imp = file.imports[2]
        require_type_imp = file.imports[3]

        assert import_imp.source == "await import('./m');"
        assert import_imp.module.source == "'./m'"
        assert import_imp.symbol_name is None
        assert import_imp.name is None
        assert import_imp.alias is None
        assert import_imp.import_type == ImportType.SIDE_EFFECT
        assert not import_imp.is_wildcard_import()
        assert import_imp.is_module_import()
        assert not import_imp.is_type_import()

        assert require_imp.source == "require('./m');"
        assert require_imp.module.source == "'./m'"
        assert require_imp.symbol_name is None
        assert require_imp.name is None
        assert require_imp.alias is None
        assert require_imp.import_type == ImportType.SIDE_EFFECT
        assert not require_imp.is_wildcard_import()
        assert require_imp.is_module_import()
        assert not import_imp.is_type_import()

        assert import_type_imp.source == "(await import('./m')).SomeType"
        assert import_type_imp.module.source == "'./m'"
        assert import_type_imp.symbol_name.source == "SomeType"
        assert import_type_imp.name == "SomeType"
        assert import_type_imp.alias.source == "SomeType"
        assert import_type_imp.import_type == ImportType.NAMED_EXPORT
        assert not import_type_imp.is_wildcard_import()
        assert not import_type_imp.is_module_import()
        assert import_type_imp.is_type_import()

        assert require_type_imp.source == "require('./m').OtherType"
        assert require_type_imp.module.source == "'./m'"
        assert require_type_imp.symbol_name.source == "OtherType"
        assert require_type_imp.name == "OtherType"
        assert require_type_imp.alias.source == "OtherType"
        assert require_type_imp.import_type == ImportType.NAMED_EXPORT
        assert not require_type_imp.is_wildcard_import()
        assert not require_type_imp.is_module_import()
        assert require_type_imp.is_type_import()

        assert import_imp.resolved_symbol == m_file
        assert require_imp.resolved_symbol == m_file
        assert import_type_imp.resolved_symbol == m_file.get_type("SomeType")
        assert require_type_imp.resolved_symbol == m_file.get_type("OtherType")


def test_dynamic_import_type_alias(tmpdir) -> None:
    # language=typescript
    content = """
type DynamicType = typeof import('./m').SomeType
const MyType = typeof import('./m').SomeType
DefaultType = (await import('./m')).default
RequiredDefaultType = require('./m').default
    """
    # language=typescript
    content2 = """
export type SomeType = {}
export interface SomeInterface {
  prop: string;
}

export default SomeInterface;
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content, "m.ts": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        m_file = codebase.get_file("m.ts")
        assert len(file.imports) == 4

        assert file.get_import("DynamicType").source == "type DynamicType = typeof import('./m').SomeType"
        assert file.get_import("DynamicType").module.source == "'./m'"
        assert file.get_import("DynamicType").symbol_name.source == "SomeType"
        assert file.get_import("DynamicType").name == "DynamicType"
        assert file.get_import("DynamicType").alias.source == "DynamicType"
        assert file.get_import("DynamicType").import_type == ImportType.NAMED_EXPORT
        assert not file.get_import("DynamicType").is_wildcard_import()
        assert not file.get_import("DynamicType").is_module_import()
        assert file.get_import("DynamicType").is_type_import()
        assert file.get_import("DynamicType").resolved_symbol == m_file.get_type("SomeType")

        assert file.get_import("MyType").source == "const MyType = typeof import('./m').SomeType"
        assert file.get_import("MyType").module.source == "'./m'"
        assert file.get_import("MyType").symbol_name.source == "SomeType"
        assert file.get_import("MyType").name == "MyType"
        assert file.get_import("MyType").alias.source == "MyType"
        assert file.get_import("MyType").import_type == ImportType.NAMED_EXPORT
        assert not file.get_import("MyType").is_wildcard_import()
        assert not file.get_import("MyType").is_module_import()
        assert file.get_import("MyType").is_type_import()
        assert file.get_import("MyType").resolved_symbol == m_file.get_type("SomeType")

        assert file.get_import("DefaultType").source == "DefaultType = (await import('./m')).default"
        assert file.get_import("DefaultType").module.source == "'./m'"
        assert file.get_import("DefaultType").symbol_name.source == "default"
        assert file.get_import("DefaultType").name == "DefaultType"
        assert file.get_import("DefaultType").alias.source == "DefaultType"
        assert file.get_import("DefaultType").import_type == ImportType.DEFAULT_EXPORT
        assert not file.get_import("DefaultType").is_wildcard_import()
        assert file.get_import("DefaultType").is_module_import()
        assert file.get_import("DefaultType").is_default_import()
        assert file.get_import("DefaultType").is_type_import()
        assert file.get_import("DefaultType").resolved_symbol == m_file.get_interface("SomeInterface")

        assert file.get_import("RequiredDefaultType").source == "RequiredDefaultType = require('./m').default"
        assert file.get_import("RequiredDefaultType").module.source == "'./m'"
        assert file.get_import("RequiredDefaultType").symbol_name.source == "default"
        assert file.get_import("RequiredDefaultType").name == "RequiredDefaultType"
        assert file.get_import("RequiredDefaultType").alias.source == "RequiredDefaultType"
        assert file.get_import("RequiredDefaultType").import_type == ImportType.DEFAULT_EXPORT
        assert not file.get_import("RequiredDefaultType").is_wildcard_import()
        assert file.get_import("RequiredDefaultType").is_module_import()
        assert file.get_import("RequiredDefaultType").is_default_import()
        assert file.get_import("RequiredDefaultType").is_type_import()
        assert file.get_import("RequiredDefaultType").resolved_symbol == m_file.get_interface("SomeInterface")


def test_dynamic_import_function_param_type(tmpdir) -> None:
    # language=typescript
    content = """
function foo(param: import('./m').SomeType) {}
section: {
    functions: {
        get: require("./m").default
    }
}
"""
    # language=typescript
    content2 = """
export default type SomeType = {}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content, "m.ts": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        m_file = codebase.get_file("m.ts")
        assert len(file.imports) == 2
        param_imp = file.imports[0]
        dict_imp = file.imports[1]

        assert param_imp.source == "import('./m').SomeType"
        assert param_imp.module.source == "'./m'"
        assert param_imp.symbol_name.source == "SomeType"
        assert param_imp.name == "SomeType"
        assert param_imp.alias.source == "SomeType"
        assert param_imp.import_type == ImportType.NAMED_EXPORT
        assert not param_imp.is_wildcard_import()
        assert not param_imp.is_module_import()
        assert param_imp.is_type_import()
        assert param_imp.imported_symbol == m_file.get_type("SomeType")
        assert param_imp.resolved_symbol == m_file.get_type("SomeType")

        assert dict_imp.source == 'require("./m").default'
        assert dict_imp.module.source == '"./m"'
        assert dict_imp.symbol_name.source == "default"
        assert dict_imp.name == "default"
        assert dict_imp.alias.source == "default"
        assert dict_imp.import_type == ImportType.DEFAULT_EXPORT
        assert not dict_imp.is_wildcard_import()
        assert dict_imp.is_module_import()
        assert dict_imp.is_type_import()
        assert param_imp.imported_symbol == m_file.get_type("SomeType")
        assert dict_imp.resolved_symbol == m_file.get_type("SomeType")


def test_dynamic_import_named_and_aliased(tmpdir) -> None:
    # language=typescript
    content = """
const { a: aliasedA, b } = await import('./m');
const { SomeType, OtherType: AliasedType } = require('./m')
    """
    # language=typescript
    content2 = """
export function a() {
    return
}
export function b() {
    return
}
export type SomeType = {}
export type OtherType = {}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content, "m.ts": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        m_file = codebase.get_file("m.ts")
        assert len(file.imports) == 4

        assert file.get_import("aliasedA").source == "const { a: aliasedA, b } = await import('./m');"
        assert file.get_import("aliasedA").module.source == "'./m'"
        assert file.get_import("aliasedA").symbol_name.source == "a"
        assert file.get_import("aliasedA").name == "aliasedA"
        assert file.get_import("aliasedA").alias.source == "aliasedA"
        assert file.get_import("aliasedA").import_type == ImportType.NAMED_EXPORT
        assert not file.get_import("aliasedA").is_wildcard_import()
        assert not file.get_import("aliasedA").is_module_import()
        assert not file.get_import("aliasedA").is_type_import()
        assert file.get_import("aliasedA").imported_symbol == m_file.get_function("a")
        assert file.get_import("aliasedA").resolved_symbol == m_file.get_function("a")

        assert file.get_import("b").source == "const { a: aliasedA, b } = await import('./m');"
        assert file.get_import("b").module.source == "'./m'"
        assert file.get_import("b").symbol_name.source == "b"
        assert file.get_import("b").name == "b"
        assert file.get_import("b").alias.source == "b"
        assert file.get_import("b").import_type == ImportType.NAMED_EXPORT
        assert not file.get_import("b").is_wildcard_import()
        assert not file.get_import("b").is_module_import()
        assert not file.get_import("b").is_type_import()
        assert file.get_import("b").imported_symbol == m_file.get_function("b")
        assert file.get_import("b").resolved_symbol == m_file.get_function("b")

        assert file.get_import("SomeType").source == "const { SomeType, OtherType: AliasedType } = require('./m')"
        assert file.get_import("SomeType").module.source == "'./m'"
        assert file.get_import("SomeType").symbol_name.source == "SomeType"
        assert file.get_import("SomeType").name == "SomeType"
        assert file.get_import("SomeType").alias.source == "SomeType"
        assert file.get_import("SomeType").import_type == ImportType.NAMED_EXPORT
        assert not file.get_import("SomeType").is_wildcard_import()
        assert not file.get_import("SomeType").is_module_import()
        assert not file.get_import("SomeType").is_type_import()
        assert file.get_import("SomeType").imported_symbol == m_file.get_type("SomeType")
        assert file.get_import("SomeType").resolved_symbol == m_file.get_type("SomeType")

        assert file.get_import("AliasedType").source == "const { SomeType, OtherType: AliasedType } = require('./m')"
        assert file.get_import("AliasedType").module.source == "'./m'"
        assert file.get_import("AliasedType").symbol_name.source == "OtherType"
        assert file.get_import("AliasedType").name == "AliasedType"
        assert file.get_import("AliasedType").alias.source == "AliasedType"
        assert file.get_import("AliasedType").import_type == ImportType.NAMED_EXPORT
        assert not file.get_import("AliasedType").is_wildcard_import()
        assert not file.get_import("AliasedType").is_module_import()
        assert not file.get_import("AliasedType").is_type_import()
        assert file.get_import("AliasedType").imported_symbol == m_file.get_type("OtherType")
        assert file.get_import("AliasedType").resolved_symbol == m_file.get_type("OtherType")


def test_import_default_export(tmpdir) -> None:
    # language=typescript
    content = """
import a from './m'
    """
    # language=typescript
    content2 = """
export default function a() {
    return
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content, "m.ts": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        m_file = codebase.get_file("m.ts")
        assert len(file.imports) == 1

        imp = file.get_import("a")
        assert imp.source == "import a from './m'"
        assert imp.module.source == "'./m'"
        assert imp.symbol_name.source == "a"
        assert imp.name == "a"
        assert imp.alias.source == "a"
        assert imp.import_type == ImportType.DEFAULT_EXPORT
        assert not imp.is_wildcard_import()
        assert imp.is_module_import()
        assert not imp.is_type_import()
        assert imp.resolved_symbol == m_file.get_function("a")


def test_import_default_symbol_export(tmpdir) -> None:
    # language=typescript
    content = """
import type a from './m'
    """
    # language=typescript
    content2 = """
export default type a = {}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content, "m.ts": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        m_file = codebase.get_file("m.ts")
        assert len(file.imports) == 1

        imp = file.get_import("a")
        assert imp.source == "import type a from './m'"
        assert imp.module.source == "'./m'"
        assert imp.symbol_name.source == "a"
        assert imp.name == "a"
        assert imp.alias.source == "a"
        assert imp.import_type == ImportType.DEFAULT_EXPORT
        assert not imp.is_wildcard_import()
        assert imp.is_module_import()
        assert imp.is_type_import()
        assert imp.resolved_symbol == m_file.get_type("a")


def test_import_default_module_export(tmpdir) -> None:
    # language=typescript
    content = """
import type a from './m'
    """
    # language=typescript
    content2 = """
export type a = {}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content, "m.ts": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        m_file = codebase.get_file("m.ts")
        assert len(file.imports) == 1

        imp = file.get_import("a")
        assert imp.source == "import type a from './m'"
        assert imp.module.source == "'./m'"
        assert imp.symbol_name.source == "a"
        assert imp.name == "a"
        assert imp.alias.source == "a"
        assert imp.import_type == ImportType.DEFAULT_EXPORT
        assert not imp.is_wildcard_import()
        assert imp.is_module_import()
        assert imp.is_type_import()
        assert imp.resolved_symbol == m_file


def test_import_side_effect(tmpdir) -> None:
    # language=typescript
    content = """
import './m'
    """
    # language=typescript
    content2 = """
export type a = {}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content, "m.ts": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        m_file = codebase.get_file("m.ts")
        assert len(file.imports) == 1

        imp = file.imports[0]
        assert imp.source == "import './m'"
        assert imp.module.source == "'./m'"
        assert imp.symbol_name is None
        assert imp.name is None
        assert imp.alias is None
        assert imp.import_type == ImportType.SIDE_EFFECT
        assert not imp.is_wildcard_import()
        assert imp.is_module_import()
        assert not imp.is_type_import()
        assert imp.resolved_symbol == m_file


def test_import_wildcard(tmpdir) -> None:
    # language=typescript
    content = """
import * as namespace from './m'
    """
    # language=typescript
    content2 = """
export default type MyType = {}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content, "m.ts": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        m_file = codebase.get_file("m.ts")
        assert len(file.imports) == 1

        imp = file.get_import("namespace")
        assert imp.source == "import * as namespace from './m'"
        assert imp.module.source == "'./m'"
        assert imp.symbol_name.source == "* as namespace"
        assert imp.name == "namespace"
        assert imp.alias == "namespace"
        assert imp.import_type == ImportType.WILDCARD
        assert imp.is_wildcard_import()
        assert imp.is_module_import()
        assert not imp.is_type_import()
        assert imp.resolved_symbol == m_file
        assert len(m_file.get_type("MyType").symbol_usages) == 1


def test_import_combined_default_and_named(tmpdir) -> None:
    # language=typescript
    content = """
import something, {a, b as c, d} from './m'
    """
    # language=typescript
    content2 = """
export function a() {
    return
}
export function b() {
    return
}
export function d() {
    return
}
export default const something = [
    "beta",
] as something
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content, "m.ts": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        m_file = codebase.get_file("m.ts")
        assert len(file.imports) == 4

        assert file.get_import("something").source == "import something, {a, b as c, d} from './m'"
        assert file.get_import("something").module.source == "'./m'"
        assert file.get_import("something").symbol_name.source == "something"
        assert file.get_import("something").name == "something"
        assert file.get_import("something").alias.source == "something"
        assert file.get_import("something").import_type == ImportType.DEFAULT_EXPORT
        assert not file.get_import("something").is_wildcard_import()
        assert file.get_import("something").is_module_import()
        assert not file.get_import("something").is_type_import()
        assert file.get_import("something").imported_symbol == m_file
        assert file.get_import("something").resolved_symbol == m_file.get_global_var("something")

        assert file.get_import("a").source == "import something, {a, b as c, d} from './m'"
        assert file.get_import("a").module.source == "'./m'"
        assert file.get_import("a").symbol_name.source == "a"
        assert file.get_import("a").name == "a"
        assert file.get_import("a").alias.source == "a"
        assert file.get_import("a").import_type == ImportType.NAMED_EXPORT
        assert not file.get_import("a").is_wildcard_import()
        assert not file.get_import("a").is_module_import()
        assert not file.get_import("a").is_type_import()

        assert file.get_import("c").source == "import something, {a, b as c, d} from './m'"
        assert file.get_import("c").module.source == "'./m'"
        assert file.get_import("c").symbol_name.source == "b"
        assert file.get_import("c").name == "c"
        assert file.get_import("c").alias.source == "c"
        assert file.get_import("c").import_type == ImportType.NAMED_EXPORT
        assert not file.get_import("c").is_wildcard_import()
        assert not file.get_import("c").is_module_import()
        assert not file.get_import("c").is_type_import()

        assert file.get_import("d").source == "import something, {a, b as c, d} from './m'"
        assert file.get_import("d").module.source == "'./m'"
        assert file.get_import("d").symbol_name.source == "d"
        assert file.get_import("d").name == "d"
        assert file.get_import("d").alias.source == "d"
        assert file.get_import("d").import_type == ImportType.NAMED_EXPORT
        assert not file.get_import("d").is_wildcard_import()
        assert not file.get_import("d").is_module_import()
        assert not file.get_import("d").is_type_import()

        assert file.get_import("a").resolved_symbol == m_file.get_function("a")
        assert file.get_import("c").resolved_symbol == m_file.get_function("b")
        assert file.get_import("d").resolved_symbol == m_file.get_function("d")


def test_import_combined_type_default_and_named(tmpdir) -> None:
    # language=typescript
    content = """
import type DefaultType, {a, b as c} from './m'
    """
    # language=typescript
    content2 = """
export type a = {}
export type b = {}
export default type DefaultType = {}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content, "m.ts": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        m_file = codebase.get_file("m.ts")
        assert len(file.imports) == 3

        assert file.get_import("DefaultType").source == "import type DefaultType, {a, b as c} from './m'"
        assert file.get_import("DefaultType").module.source == "'./m'"
        assert file.get_import("DefaultType").symbol_name.source == "DefaultType"
        assert file.get_import("DefaultType").name == "DefaultType"
        assert file.get_import("DefaultType").alias.source == "DefaultType"
        assert file.get_import("DefaultType").import_type == ImportType.DEFAULT_EXPORT
        assert not file.get_import("DefaultType").is_wildcard_import()
        assert file.get_import("DefaultType").is_module_import()
        assert file.get_import("DefaultType").is_type_import()
        assert file.get_import("DefaultType").imported_symbol == m_file
        assert file.get_import("DefaultType").resolved_symbol == m_file.get_type("DefaultType")

        assert file.get_import("a").source == "import type DefaultType, {a, b as c} from './m'"
        assert file.get_import("a").module.source == "'./m'"
        assert file.get_import("a").symbol_name.source == "a"
        assert file.get_import("a").name == "a"
        assert file.get_import("a").alias.source == "a"
        assert file.get_import("a").import_type == ImportType.NAMED_EXPORT
        assert not file.get_import("a").is_wildcard_import()
        assert not file.get_import("a").is_module_import()
        assert file.get_import("a").is_type_import()
        assert file.get_import("a").imported_symbol == m_file.get_type("a")
        assert file.get_import("a").resolved_symbol == m_file.get_type("a")

        assert file.get_import("c").source == "import type DefaultType, {a, b as c} from './m'"
        assert file.get_import("c").module.source == "'./m'"
        assert file.get_import("c").symbol_name.source == "b"
        assert file.get_import("c").name == "c"
        assert file.get_import("c").alias.source == "c"
        assert file.get_import("c").import_type == ImportType.NAMED_EXPORT
        assert not file.get_import("c").is_wildcard_import()
        assert not file.get_import("c").is_module_import()
        assert file.get_import("c").is_type_import()
        assert file.get_import("c").imported_symbol == m_file.get_type("b")
        assert file.get_import("c").resolved_symbol == m_file.get_type("b")


def test_resolve_absolute_import(tmpdir) -> None:
    """Tests import resolution with an absolute import path"""
    src_filename = "src/foo/bar.ts"
    # language=typescript
    src_file_content = """
export function someFunction() {}
"""
    usage_filename = "src/baz.ts"
    # language=typescript
    usage_file_content = """
import * as bar from "./foo/bar"
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={src_filename: src_file_content, usage_filename: usage_file_content}) as codebase:
        src_file: SourceFile = codebase.get_file(src_filename)
        usage_file: SourceFile = codebase.get_file(usage_filename)
        assert len(usage_file.imports) == 1
        src_import: Import = usage_file.imports[0]
        src_import_resolution: ImportResolution = src_import.resolve_import()
        assert src_import_resolution
        assert src_import_resolution.from_file is src_file
        assert src_import_resolution.imports_file is True


def test_resolve_relative_import_base_dir(tmpdir) -> None:
    """Tests import resolution when both files are in the base dir"""
    src_filename = "foo.ts"
    # language=typescript
    src_file_content = """
export function someFunction() {}
"""
    usage_filename = "bar.ts"
    # language=typescript
    usage_file_content = """
import * as foo from "./foo"
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={src_filename: src_file_content, usage_filename: usage_file_content}) as codebase:
        src_file: SourceFile = codebase.get_file(src_filename)
        usage_file: SourceFile = codebase.get_file(usage_filename)
        assert len(usage_file.imports) == 1
        src_import: Import = usage_file.imports[0]
        src_import_resolution: ImportResolution = src_import.resolve_import()
        assert src_import_resolution
        assert src_import_resolution.from_file is src_file
        assert src_import_resolution.imports_file is True


def test_resolve_relative_import_single_dir(tmpdir) -> None:
    """Tests import resolution when both files are in the same (non base) directory"""
    src_filename = "src/foo.ts"
    # language=typescript
    src_file_content = """
export function someFunction() {}
"""
    usage_filename = "src/bar.ts"
    # language=typescript
    usage_file_content = """
import * as foo from "./foo"
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={src_filename: src_file_content, usage_filename: usage_file_content}) as codebase:
        src_file: SourceFile = codebase.get_file(src_filename)
        usage_file: SourceFile = codebase.get_file(usage_filename)
        assert len(usage_file.imports) == 1
        src_import: Import = usage_file.imports[0]
        src_import_resolution: ImportResolution = src_import.resolve_import()
        assert src_import_resolution
        assert src_import_resolution.from_file is src_file
        assert src_import_resolution.imports_file is True


def test_resolve_relative_import_single_child(tmpdir) -> None:
    """Tests when importing using a single child traversal (i.e. ./<dir>/file)"""
    src_filename = "src/foo/bar.ts"
    # language=typescript
    src_file_content = """
export function someFunction() {}
"""
    usage_filename = "src/baz.ts"
    # language=typescript
    usage_file_content = """
import * as bar from "./foo/bar"
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={src_filename: src_file_content, usage_filename: usage_file_content}) as codebase:
        src_file: SourceFile = codebase.get_file(src_filename)
        usage_file: SourceFile = codebase.get_file(usage_filename)
        assert len(usage_file.imports) == 1
        src_import: Import = usage_file.imports[0]
        src_import_resolution: ImportResolution = src_import.resolve_import()
        assert src_import_resolution
        assert src_import_resolution.from_file is src_file
        assert src_import_resolution.imports_file is True


def test_resolve_relative_import_single_parent(tmpdir) -> None:
    """Tests when importing using a single parent traversal (i.e. ../)"""
    src_filename = "src/foo.ts"
    # language=typescript
    src_file_content = """
export function someFunction() {}
"""
    usage_filename = "src/bar/baz.ts"
    # language=typescript
    usage_file_content = """
import * as foo from "../foo"
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={src_filename: src_file_content, usage_filename: usage_file_content}) as codebase:
        src_file: SourceFile = codebase.get_file(src_filename)
        usage_file: SourceFile = codebase.get_file(usage_filename)
        assert len(usage_file.imports) == 1
        src_import: Import = usage_file.imports[0]
        src_import_resolution: ImportResolution = src_import.resolve_import()
        assert src_import_resolution
        assert src_import_resolution.from_file is src_file
        assert src_import_resolution.imports_file is True


def test_resolve_relative_import_multi_parent(tmpdir) -> None:
    """Tests when importing using a multi parent traversal (i.e. ../../)"""
    src_filename = "src/foo.ts"
    # language=typescript
    src_file_content = """
export function someFunction() {}
"""
    usage_filename = "src/bar/baz/qux.ts"
    # language=typescript
    usage_file_content = """
import * as foo from "../../foo"
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={src_filename: src_file_content, usage_filename: usage_file_content}) as codebase:
        src_file: SourceFile = codebase.get_file(src_filename)
        usage_file: SourceFile = codebase.get_file(usage_filename)
        assert len(usage_file.imports) == 1
        src_import: Import = usage_file.imports[0]
        src_import_resolution: ImportResolution = src_import.resolve_import()
        assert src_import_resolution
        assert src_import_resolution.from_file is src_file
        assert src_import_resolution.imports_file is True


def test_resolve_wildcard_import(tmpdir) -> None:
    """Tests when importing using a wildcard import"""
    # language=typescript
    src_content = """
export function someFunction() {}
"""
    # language=typescript
    usage_content = """
import * as foo from "./source";
const a = foo.someFunction();
const b = foo.someOtherFunction();
const c = foo.someFunction();
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"source.ts": src_content, "usage.ts": usage_content}) as codebase:
        src_file: SourceFile = codebase.get_file("source.ts")
        some_function = src_file.get_function("someFunction")
        assert len(some_function.symbol_usages(UsageType.DIRECT)) == 1
        assert len(some_function.symbol_usages(UsageType.CHAINED)) == 2


def test_resolve_double_dynamic_import(tmpdir) -> None:
    # language=typescript
    content1 = """
const myFile2 = await import("./file2");
const myFile3 = await import("./file3");

function example() {
    myFile2.foo();
    myFile3.bar();
}

example();

"""
    # language=typescript
    content2 = """
export function foo() {
  console.log("This is foo from file2");
}
"""
    # language=typescript
    content3 = """
export function bar() {
  console.log("This is bar from file3");
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"file1.ts": content1, "file2.ts": content2, "file3.ts": content3}) as codebase:
        file2 = codebase.get_file("file2.ts")
        file3 = codebase.get_file("file3.ts")
        foo = file2.get_function("foo")
        bar = file3.get_function("bar")

        assert len(foo.call_sites) == 1
        assert len(bar.call_sites) == 1
        assert foo.call_sites[0].source == "myFile2.foo()"
        assert bar.call_sites[0].source == "myFile3.bar()"
