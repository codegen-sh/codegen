from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_comment_single_line(tmpdir) -> None:
    FILENAME = "test_file.ts"
    # language=typescript
    FILE_CONTENT = """
// This is a comment
export async function foo() {
    // Function body
}
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={FILENAME: FILE_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        foo = file.get_symbol("foo")

        assert foo.comment.source == "// This is a comment"
        assert "// This is a comment" in foo.extended_source
        # assert "// This is a comment" not in foo.source
        assert "function foo() {" in foo.source
        assert "function foo() {" in foo.extended_source
