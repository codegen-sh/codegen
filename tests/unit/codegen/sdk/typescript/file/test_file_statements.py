import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


@pytest.mark.skip("TODO: @caroljung fix once file and symbol code block parse is unified")
def test_file_statements(tmpdir) -> None:
    # language=typescript
    content = """
import "./a";
b();
const c = 1;

function d() {
    return 1;
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        assert len(file.code_block.statements) == 4
        assert len(file.code_block.get_statements()) == 5
