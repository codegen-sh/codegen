from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.core.function import Function


def test_parameter_is_variadic_should_return_true(tmpdir) -> None:
    filename = "test.ts"
    # language=typescript
    file_content = """
function funcWithVariadicParams(...numbers: number[]): number {
    return numbers.reduce((acc, curr) => acc + curr, 0);
}
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={filename: file_content}) as codebase:
        file = codebase.get_file(filename)
        symbol: Function = file.get_symbol("funcWithVariadicParams")
        assert symbol is not None
        assert len(symbol.parameters) == 1
        assert symbol.parameters[0].is_variadic
