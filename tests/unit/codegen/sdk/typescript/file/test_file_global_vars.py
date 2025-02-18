from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_global_vars_gets_exported_global_vars(tmpdir) -> None:
    filename = "test.ts"
    content = """
export const var1 = {
    "key": ["value"],
} as const

export const var2 = ["value1"] as const

export const var3 = [
    "value2",
] as const
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={filename: content}) as ctx:
        file = ctx.get_file(filename)

        # ======[ Global Vars ]=====
        gvars = file.global_vars
        assert len(gvars) == 3
        assert "var1" in [v.name for v in gvars]
        assert "var2" in [v.name for v in gvars]
        assert "var3" in [v.name for v in gvars]
