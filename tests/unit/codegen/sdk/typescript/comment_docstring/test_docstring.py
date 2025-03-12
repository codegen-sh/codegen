from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_docstring_no_docstring(tmpdir) -> None:
    content = """
function symbol() {}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        assert symbol.docstring is None


def test_docstring_noop(tmpdir) -> None:
    content = """
// this is a test docstring
function symbol() {}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        assert symbol.docstring is None


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


def test_docstring_multiline_noop(tmpdir) -> None:
    content = """
// this is a test docstring
// that spans multiple lines
function symbol() {}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        assert symbol.docstring is None


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


def test_docstring_class_method(tmpdir) -> None:
    content = """
class MyClass {
    /**
     * This is a method
     */
    public myMethod(): void {
        console.log('This is a method');
    }
}
    """
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")
        my_class = file.get_class("MyClass")
        my_method = my_class.get_method("myMethod")
        assert my_method.docstring.source == "/**\n     * This is a method\n     */"
        assert my_method.docstring.text == "This is a method"


def test_docstring_class_method_with_decorator(tmpdir) -> None:
    content = """
class MyClass {
    /**
     * This is a method
     */
    @withUser
    public myMethod(): void {
        console.log('This is a method');
    }
}
    """
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")
        my_class = file.get_class("MyClass")
        my_method = my_class.get_method("myMethod")
        assert my_method.docstring.source == "/**\n     * This is a method\n     */"
        assert my_method.docstring.text == "This is a method"


def test_docstring_class_method_excludes_docstring_with_space(tmpdir) -> None:
    content = """
class MyClass {
    /**
     * This is a method
     */

    @withUser
    public myMethod(): void {
        console.log('This is a method');
    }
}
    """
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")
        my_class = file.get_class("MyClass")
        my_method = my_class.get_method("myMethod")
        assert my_method.docstring is None


def test_docstring_arrow_function(tmpdir) -> None:
    content = """
/**
 * This is a docstring
 */
export const foo = () => {}
    """
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")
        foo = file.get_symbol("foo")
        assert foo.docstring.source == "/**\n * This is a docstring\n */"
        assert foo.docstring.text == "This is a docstring"
