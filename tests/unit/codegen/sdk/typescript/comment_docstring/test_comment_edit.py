import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_comment_basic(tmpdir) -> None:
    content = """
// this is a test comment
const symbol = 1
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        assert symbol.comment.source == "// this is a test comment"
        assert symbol.comment.text == "this is a test comment"
        symbol.comment.edit_text("this is a new comment")

    # Check that the comment was edited
    assert "// this is a new comment" in file.source


@pytest.mark.skip("Corrupts output")
def test_comment_edit_source(tmpdir) -> None:
    content = """
// this is a test comment
const symbol = 1
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}, sync_graph=False) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        assert symbol.comment.source == "// this is a test comment"
        assert symbol.comment.text == "this is a test comment"
        symbol.comment.edit("@hello_i_am_a_decorator")

    # Check that the comment was edited
    assert "@hello_i_am_a_decorator" in file.source
    assert "//" not in file.source


def test_comment_block(tmpdir) -> None:
    content = """
/* this is a test comment */
const symbol = 1
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        assert symbol.comment.source == "/* this is a test comment */"
        assert symbol.comment.text == "this is a test comment"
        symbol.comment.edit_text("this is a new comment")

    # Check that the comment was edited
    assert "/* this is a new comment */" in file.source


def test_comment_multiline(tmpdir) -> None:
    content = """
// this is a test comment
// that spans multiple lines
const symbol = 1
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        assert symbol.comment.source == "// this is a test comment\n// that spans multiple lines"
        assert symbol.comment.text == "this is a test comment\nthat spans multiple lines"
        symbol.comment.edit_text("this is a new comment\nthat spans multiple lines")

    # Check that the comment was edited
    assert "// this is a new comment\n// that spans multiple lines" in file.source


def test_comment_multiline_block(tmpdir) -> None:
    content = """
/*
this is a test comment
that spans multiple lines
*/
const symbol = 1
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        assert symbol.comment.source == "/*\nthis is a test comment\nthat spans multiple lines\n*/"
        assert symbol.comment.text == "this is a test comment\nthat spans multiple lines"
        symbol.comment.edit_text("this is a new comment\nthat spans multiple lines")

    # Check that the comment was edited
    assert "/*\nthis is a new comment\nthat spans multiple lines\n*/" in file.source


def test_comment_multiline_block_starred(tmpdir) -> None:
    content = """
/**
 * this is a test comment
 * that spans multiple lines
 */
const symbol = 1
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        assert symbol.comment.source == "/**\n * this is a test comment\n * that spans multiple lines\n */"
        assert symbol.comment.text == "this is a test comment\nthat spans multiple lines"
        symbol.comment.edit_text("this is a new comment\nthat spans multiple lines")

    # Check that the comment was edited
    assert "/**\n * this is a new comment\n * that spans multiple lines\n */" in file.source


def test_comment_mixed(tmpdir) -> None:
    content = """
// comment 1
/* comment 2 */
// comment 3
// comment 4
/*
comment 5
comment 6
*/
/*
 * comment 7
 * comment 8
*/
const symbol = 1
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        assert symbol.comment.source == "// comment 1\n/* comment 2 */\n// comment 3\n// comment 4\n/*\ncomment 5\ncomment 6\n*/\n/*\n * comment 7\n * comment 8\n*/"
        assert symbol.comment.text == "comment 1\ncomment 2\ncomment 3\ncomment 4\ncomment 5\ncomment 6\ncomment 7\ncomment 8"
        symbol.comment.edit_text("new comment 1\nnew comment 2\nnew comment 3\nnew comment 4\nnew comment 5\nnew comment 6\nnew comment 7\nnew comment 8")

    # Check that the comment was edited
    assert "// new comment 1\n// new comment 2\n// new comment 3\n// new comment 4\n// new comment 5\n// new comment 6\n// new comment 7\n// new comment 8" in file.source


def test_comment_with_indentation(tmpdir) -> None:
    content = """
class A {
    // this is a test comment
    // that has indentation
    symbol() {
        // something
    }
}
"""

    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        A = file.get_symbol("A")
        symbol = A.get_method("symbol")
        assert symbol.comment.source == "// this is a test comment\n// that has indentation"
        assert symbol.comment.text == "this is a test comment\nthat has indentation"
        symbol.comment.edit_text("this is a new comment\nthat has indentation")

    # Check that the comment was edited
    assert "    // this is a new comment\n    // that has indentation" in file.source


def test_comment_with_indentation_in_block(tmpdir) -> None:
    content = """
class A {
    /*
    this is a test comment
    that has indentation
    */
    symbol() {
        // something
    }
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        A = file.get_symbol("A")
        symbol = A.get_method("symbol")
        assert symbol.comment.source == "/*\n    this is a test comment\n    that has indentation\n    */"
        assert symbol.comment.text == "this is a test comment\nthat has indentation"
        symbol.comment.edit_text("this is a new comment\nthat has indentation")

    # Check that the comment was edited
    assert "    /*\n    this is a new comment\n    that has indentation\n    */" in file.source


def test_comment_with_indentation_in_block_starred(tmpdir) -> None:
    content = """
class A {
    /**
     * this is a test comment
     * that has indentation
     */
    symbol() {
        // something
    }
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        A = file.get_symbol("A")
        symbol = A.get_method("symbol")
        assert symbol.comment.source == "/**\n     * this is a test comment\n     * that has indentation\n     */"
        assert symbol.comment.text == "this is a test comment\nthat has indentation"
        symbol.comment.edit_text("this is a new comment\nthat has indentation")

    # Check that the comment was edited
    assert "    /**\n     * this is a new comment\n     * that has indentation\n     */\n    symbol() {" in file.source
