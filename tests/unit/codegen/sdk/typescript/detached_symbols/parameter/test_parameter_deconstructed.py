from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.typescript.file import TSFile
    from codegen.sdk.typescript.function import TSFunction


def test_edit_parameter_in_function_definition(tmpdir) -> None:
    filename = "test_definition.ts"
    # language=typescript
    file_content = """
// Simple case
const f = ({ a, b }: { a: number, b?: number }): number => {
    return a + b;
}

// Harder case
type T = {
    a: number;
    b?: number;
};
const g =  ({ a, b = 1 }: T): number => {
    return a + b;
}

// Defaults
const h = ({ a, b = 1 }: { a: number, b?: number }): number => {
    return a + b;
}
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={filename: file_content}) as codebase:
        file: TSFile = codebase.get_file(filename)

        # =====[ Simple case ]=====
        f: TSFunction = file.get_function("f")
        assert f is not None
        assert len(f.parameters) == 2
        assert f.parameters[0].name == "a"
        assert f.parameters[0].default is None
        assert f.parameters[1].name == "b"
        assert f.parameters[1].default is None
        assert all([p.is_destructured for p in f.parameters])

        # =====[ Complex case ]=====
        g: TSFunction = file.get_function("g")
        assert g is not None
        assert len(g.parameters) == 2
        assert g.parameters[0].name == "a"
        assert g.parameters[0].default is None
        assert g.parameters[1].name == "b"
        assert g.parameters[1].default == "1"
        assert all([p.is_destructured for p in g.parameters])

        # =====[ Defaults ]=====
        h: TSFunction = file.get_function("h")
        assert h is not None
        assert len(h.parameters) == 2
        assert h.parameters[0].name == "a"
        assert h.parameters[0].default is None
        assert h.parameters[1].name == "b"
        b = h.parameters[1]
        assert b.is_destructured
        assert b.default == "1"
