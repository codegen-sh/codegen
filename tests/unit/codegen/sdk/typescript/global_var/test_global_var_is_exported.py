from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_is_exported_should_return_true(tmpdir) -> None:
    ts_code = """
export const g = 6;
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": ts_code}) as ctx:
        file = ctx.get_file("test.ts")
        g = file.get_global_var("g")
        assert g.is_exported is True


def test_is_exported_should_return_false(tmpdir) -> None:
    ts_code = """
const h = 1;
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": ts_code}) as ctx:
        file = ctx.get_file("test.ts")
        h = file.get_global_var("h")
        assert h.is_exported is False


def test_is_exported_let(tmpdir) -> None:
    file = """
export let a = 'c'
    """
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")
        global_var_a = file.get_symbol("a")
        assert global_var_a.is_exported
