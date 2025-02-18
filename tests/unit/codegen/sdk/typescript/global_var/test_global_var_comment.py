from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_comment_single_line(tmpdir) -> None:
    FILENAME = "test_file.ts"
    # language=typescript
    FILE_CONTENT = """
// This is a comment
const foo = 1;
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
        assert "foo = 1" in foo.source
        assert "const foo = 1;" in foo.extended_source


def test_comment_does_not_include_inline(tmpdir) -> None:
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

        assert foo.comment is None


def test_comment_multiple_single_line(tmpdir) -> None:
    FILENAME = "test_file.ts"
    # language=typescript
    FILE_CONTENT = """
// This is comment 1
// This is comment 2
// This is comment 3
const foo = 1;
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={FILENAME: FILE_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        foo = file.get_symbol("foo")

        assert foo.comment.source == "// This is comment 1\n// This is comment 2\n// This is comment 3"
        assert "// This is comment 1" in foo.extended_source
        assert "// This is comment 2" in foo.extended_source
        assert "// This is comment 3" in foo.extended_source
        # assert "// This is comment 1" not in foo.source
        # assert "// This is comment 2" not in foo.source
        # assert "// This is comment 3" not in foo.source
        assert "foo = 1" in foo.source
        assert "const foo = 1;" in foo.extended_source


def test_comment_multiline(tmpdir) -> None:
    FILENAME = "test_file.ts"
    # language=typescript
    FILE_CONTENT = """
/**
* This is comment 1
* This is comment 2
* This is comment 3
*/
const foo = 1;
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={FILENAME: FILE_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        foo = file.get_symbol("foo")

        assert foo.comment.source == "/**\n* This is comment 1\n* This is comment 2\n* This is comment 3\n*/"
        assert "* This is comment 1" in foo.extended_source
        assert "* This is comment 2" in foo.extended_source
        assert "* This is comment 3" in foo.extended_source
        # assert "* This is comment 1" not in foo.source
        # assert "* This is comment 2" not in foo.source
        # assert "* This is comment 3" not in foo.source
        assert "foo = 1" in foo.source
        assert "const foo = 1;" in foo.extended_source


def test_comment_whitespace_separated_does_not_match(tmpdir) -> None:
    FILENAME = "test_file.ts"
    # language=typescript
    FILE_CONTENT = """
// DO NOT INCLUDE
// DO NOT INCLUDE

// This is comment 1
// This is comment 2
const foo = 1;
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={FILENAME: FILE_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        foo = file.get_symbol("foo")

        assert foo.comment.source == "// This is comment 1\n// This is comment 2"
        assert "// This is comment 1" in foo.extended_source
        assert "// This is comment 2" in foo.extended_source
        # assert "// This is comment 1" not in foo.source
        # assert "// This is comment 2" not in foo.source
        assert "DO NOT INCLUDE" not in foo.extended_source
        assert "DO NOT INCLUDE" not in foo.source
        assert "foo = 1" in foo.source
        assert "const foo = 1;" in foo.extended_source


def test_comment_does_not_include_detached_comment(tmpdir) -> None:
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

        assert foo.comment is None
        assert foo.inline_comment is None
        assert "DO NOT INCLUDE" not in foo.extended_source
        assert "DO NOT INCLUDE" not in foo.source
        assert "foo = 1" in foo.source
        assert "const foo = 1;" in foo.extended_source
