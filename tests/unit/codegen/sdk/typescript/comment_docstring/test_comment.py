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


def test_comment_no_comment(tmpdir) -> None:
    content = """
const symbol = 1
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        assert symbol.comment is None


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


def test_comment_weird_spacing(tmpdir) -> None:
    content = """
// this is a test comment
//that has weird spacing
const symbol = 1
"""

    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        assert symbol.comment.source == "// this is a test comment\n//that has weird spacing"
        assert symbol.comment.text == "this is a test comment\nthat has weird spacing"


def test_comment_weird_spacing_block(tmpdir) -> None:
    content = """
/*this is a test comment
that has weird spacing*/
const symbol = 1
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        assert symbol.comment.source == "/*this is a test comment\nthat has weird spacing*/"
        assert symbol.comment.text == "this is a test comment\nthat has weird spacing"


def test_comment_weird_spacing_block_starred(tmpdir) -> None:
    content = """
/* this is a test comment
* that has weird spacing */
const symbol = 1
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        assert symbol.comment.source == "/* this is a test comment\n* that has weird spacing */"
        assert symbol.comment.text == "this is a test comment\nthat has weird spacing"


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
        symbol.comment.edit("this is a new comment\nthat has indentation")


def test_comment_with_spacing(tmpdir) -> None:
    content = """
//       this is a test comment
//     that has spacing
const symbol = 1
"""

    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        assert symbol.comment.source == "//       this is a test comment\n//     that has spacing"
        assert symbol.comment.text == "      this is a test comment\n    that has spacing"


def test_comment_with_spacing_block(tmpdir) -> None:
    content = """
/*       this is a test comment
     that has spacing */
const symbol = 1
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        assert symbol.comment.source == "/*       this is a test comment\n     that has spacing */"
        assert symbol.comment.text == " this is a test comment\nthat has spacing"


def test_comment_with_spacing_block_starred(tmpdir) -> None:
    content = """
/**
 *       this is a test comment
 *     that has spacing
*/
const symbol = 1
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        assert symbol.comment.source == "/**\n *       this is a test comment\n *     that has spacing\n*/"
        assert symbol.comment.text == "      this is a test comment\n    that has spacing"
