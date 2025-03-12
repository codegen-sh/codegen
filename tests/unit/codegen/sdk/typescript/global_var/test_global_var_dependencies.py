from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session
from codegen.sdk.core.import_resolution import Import
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.typescript.assignment import TSAssignment


def test_dependencies_gets_symbols_in_same_file(tmpdir) -> None:
    filename = "test.ts"
    content = """
export const foo = [
    "value",
] as const

const bar = {
    key: foo,
} as const
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={filename: content}) as ctx:
        file = ctx.get_file(filename)

        gvar: TSAssignment = file.get_global_var("bar")
        deps = gvar.dependencies
        assert len(deps) == 1
        assert deps[0].name == "foo"


def test_dependencies_gets_imports(tmpdir) -> None:
    filename = "test.ts"
    content = """
import {helper} from "utils"

export const values = [
    ...helper(),
] as const
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={filename: content}) as ctx:
        file = ctx.get_file(filename)

        gvar: TSAssignment = file.get_global_var("values")
        deps = gvar.dependencies
        assert len(deps) == 1
        assert [d.name for d in deps if isinstance(d, Import)] == ["helper"]


def test_dependencies_finds_multiple_symbol_deps(tmpdir) -> None:
    ts_code = """
const a = 1;
let b = 2;
var c = 3;
const d = 4, e = 5;
let f = a + b + c;
export const g = 6;
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": ts_code}) as ctx:
        file = ctx.get_file("test.ts")

        # =====[ Count symbols ]=====
        symbols = file.symbols
        assert set(x.name for x in symbols) == {"a", "b", "c", "d", "e", "f", "g"}
        assert len(symbols) == 7

        # =====[ Dependencies ]=====
        f = file.get_global_var("f")
        deps = f.dependencies
        assert len(deps) == 3
        assert set(x.name for x in deps) == {"a", "b", "c"}


def test_global_var_dependencies_value(tmpdir) -> None:
    ts_code = """
function Component() {
    return <div>Content</div>;
}

Container.SubComponent = Component
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.tsx": ts_code}) as ctx:
        file = ctx.get_file("test.tsx")

        # =====[ Count symbols ]=====
        symbol = file.get_symbol("Component")
        assert symbol.is_jsx
        assert len(symbol.symbol_usages) == 1
