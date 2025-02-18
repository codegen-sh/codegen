from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_set_docstring(tmpdir) -> None:
    content = """
export function symbol() {}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        assert symbol.docstring is None
        symbol.set_docstring("this is a test docstring")

    # Check that the docstring was added
    assert "/* this is a test docstring */\nexport function symbol() {}" in file.source


def test_set_docstring_with_formatting(tmpdir) -> None:
    content = """
export function symbol() {}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        assert symbol.docstring is None
        symbol.set_docstring("/* this is a test docstring */")

    # Check that the docstring was added
    assert "/* this is a test docstring */\nexport function symbol() {}" in file.source


def test_set_docstring_multiline(tmpdir) -> None:
    content = """
function symbol() {}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        assert symbol.docstring is None
        symbol.set_docstring("this is a test docstring\nthat spans multiple lines")

    # Check that the docstring was added
    assert "/**\n * this is a test docstring\n * that spans multiple lines\n */\nfunction symbol() {}" in file.source


def test_set_docstring_indented(tmpdir) -> None:
    content = """
class A {
    foo() {}
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("A")
        foo = symbol.get_method("foo")
        assert foo.docstring is None
        foo.set_docstring("this is a test docstring")

    # Check that the docstring was added
    assert "    /* this is a test docstring */\n    foo() {}" in file.source


def test_set_docstring_multiline_indented(tmpdir) -> None:
    content = """
class A {
    foo() {}
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("A")
        foo = symbol.get_method("foo")
        assert foo.docstring is None
        foo.set_docstring("this is a test docstring\nthat spans multiple lines")

    # Check that the docstring was added
    assert "    /**\n     * this is a test docstring\n     * that spans multiple lines\n     */\n    foo() {}" in file.source


def test_insert_docstring_block(tmpdir) -> None:
    content = """
/* this is a test docstring */
function symbol() {}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        assert symbol.docstring.source == "/* this is a test docstring */"
        assert symbol.docstring.text == "this is a test docstring"
        symbol.set_docstring("this is a new docstring")

    # Check that the docstring was edited
    assert "/* this is a new docstring */" in file.source


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
        symbol.set_docstring("this is a new docstring\nthat spans multiple lines")

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
        symbol.set_docstring("this is a new docstring\nthat spans multiple lines")

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
        symbol.set_docstring("this is a new docstring")

    # Check that the docstring was edited
    assert "/* this is a new docstring */" in file.source
    assert "// this is a test comment" in file.source
    assert "// this is another test comment" in file.source


def test_docstring_arrow_function(tmpdir) -> None:
    content = """
export const foo = () => {}
    """
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")
        foo = file.get_symbol("foo")
        foo.set_docstring("this is a new docstring")
        print(foo.extended.source)

    # Check that the docstring was edited
    assert "/* this is a new docstring */" in file.source
    assert "export const foo = () => {}" in file.source
