from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_inline_comment_includes_inline(tmpdir) -> None:
    FILENAME = "test_file.ts"
    # language=typescript
    FILE_CONTENT = """
const foo = 1;  // This is a comment
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={FILENAME: FILE_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        foo = file.get_symbol("foo")

        assert foo.inline_comment.source == "// This is a comment"
        assert "// This is a comment" in foo.extended_source
        # assert "// This is a comment" not in foo.source
        assert "foo = 1" in foo.source
        assert "const foo = 1;" in foo.extended_source


def test_inline_comment_does_not_include_detached_comment(tmpdir) -> None:
    FILENAME = "test_file.ts"
    # language=typescript
    FILE_CONTENT = """
// DO NOT INCLUDE

const foo = 1;
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={FILENAME: FILE_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        foo = file.get_symbol("foo")

        assert foo.inline_comment is None
        assert "DO NOT INCLUDE" not in foo.extended_source
        assert "DO NOT INCLUDE" not in foo.source
        assert "foo = 1" in foo.source
        assert "const foo = 1;" in foo.extended_source
