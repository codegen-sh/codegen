import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_docstring_block(tmpdir) -> None:
    content = """
/* this is a test docstring */
function symbol() {}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        assert symbol.docstring.source == "/* this is a test docstring */"
        assert symbol.docstring.text == "this is a test docstring"
        symbol.docstring.edit_text("this is a new docstring")

    # Check that the docstring was edited
    assert "/* this is a new docstring */" in file.source


@pytest.mark.skip("Corrupts output")
def test_docstring_block_source(tmpdir) -> None:
    content = """
/* this is a test docstring */
function symbol() {}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}, sync_graph=False) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        assert symbol.docstring.source == "/* this is a test docstring */"
        assert symbol.docstring.text == "this is a test docstring"
        symbol.docstring.edit("this is a new docstring")

    # Check that the docstring was edited
    assert "this is a new docstring" in file.source
    assert "/*" not in file.source
    assert "*/" not in file.source


def test_docstring_multiline_block(tmpdir) -> None:
    content = """
/*
this is a test docstring
that spans multiple lines
*/
function symbol() {}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        assert symbol.docstring.source == "/*\nthis is a test docstring\nthat spans multiple lines\n*/"
        assert symbol.docstring.text == "this is a test docstring\nthat spans multiple lines"
        symbol.docstring.edit_text("this is a new docstring\nthat spans multiple lines")

    # Check that the docstring was edited
    assert "/*\nthis is a new docstring\nthat spans multiple lines\n*/" in file.source


def test_docstring_multiline_block_starred(tmpdir) -> None:
    content = """
/**
 * this is a test docstring
 * that spans multiple lines
 */
function symbol() {}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        assert symbol.docstring.source == "/**\n * this is a test docstring\n * that spans multiple lines\n */"
        assert symbol.docstring.text == "this is a test docstring\nthat spans multiple lines"
        symbol.docstring.edit_text("this is a new docstring\nthat spans multiple lines")

    # Check that the docstring was edited
    assert "/**\n * this is a new docstring\n * that spans multiple lines\n */" in file.source


def test_docstring_surrounded_by_comments(tmpdir) -> None:
    content = """
// this is a test comment
/**
 * this is a test docstring
 */
// this is another test comment
function symbol() {}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        assert symbol.docstring.source == "/**\n * this is a test docstring\n */"
        assert symbol.docstring.text == "this is a test docstring"
        symbol.docstring.edit_text("this is a new docstring")

    # Check that the docstring was edited
    assert "/* this is a new docstring */" in file.source
    assert "// this is a test comment" in file.source
    assert "// this is another test comment" in file.source


def test_docstring_combined(tmpdir) -> None:
    content = """
/*
 * This is one part of a docstring.
 */
// this is a test comment
/*
 * This is another part of a docstring.
 */
function symbol() {}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        assert symbol.docstring.source == "/*\n * This is one part of a docstring.\n */\n/*\n * This is another part of a docstring.\n */"
        assert symbol.docstring.text == "This is one part of a docstring.\nThis is another part of a docstring."
        symbol.docstring.edit_text("This is a new docstring.")

    assert "/* This is a new docstring. */\n// this is a test comment\nfunction symbol() {}\n" in file.source


def test_docstring_arrow_function(tmpdir) -> None:
    content = """
/**
 * this is a docstring
 */
export const foo = () => {}
    """
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")
        foo = file.get_symbol("foo")
        assert foo.docstring.source == "/**\n * this is a docstring\n */"
        assert foo.docstring.text == "this is a docstring"
        foo.set_docstring("this is a new docstring")

    # Check that the docstring was edited
    assert "/* this is a new docstring */" in file.source
