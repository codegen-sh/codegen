from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_codebase_meta(tmpdir) -> None:
    # language=python
    file0_content = """""".strip()
    with get_codebase_session(
        tmpdir=tmpdir,
        files={"dir/file0.py": file0_content},
        programming_language=ProgrammingLanguage.PYTHON,
    ) as codebase:
        assert codebase.language == ProgrammingLanguage.PYTHON
        assert codebase.name == "test_codebase_meta0"
        assert "name=test_codebase_meta0" in str(codebase)
        assert "language=PYTHON" in str(codebase)

    with get_codebase_session(
        tmpdir=tmpdir,
        files={"dir/file0.ts": file0_content},
        programming_language=ProgrammingLanguage.TYPESCRIPT,
    ) as codebase:
        assert codebase.language == ProgrammingLanguage.TYPESCRIPT
        assert codebase.name == "test_codebase_meta0"
        assert "name=test_codebase_meta0" in str(codebase)
        assert "language=TYPESCRIPT" in str(codebase)
