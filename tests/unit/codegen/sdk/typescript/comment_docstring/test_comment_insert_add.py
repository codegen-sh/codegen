from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_set_comment(tmpdir) -> None:
    content = """
const symbol = 1
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        assert symbol.comment is None
        symbol.set_comment("this is a new comment")

    # Check that the comment was added
    assert "// this is a new comment\nconst symbol = 1" in file.source


def test_set_comment_with_formatting(tmpdir) -> None:
    content = """
const symbol = 1
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        assert symbol.comment is None
        symbol.set_comment("// this is a new comment")

    # Check that the comment was added
    assert "// this is a new comment\nconst symbol = 1" in file.source
    assert "////" not in file.source
    assert "// //" not in file.source


def test_set_comment_with_block_formatting(tmpdir) -> None:
    content = """
const symbol = 1
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        assert symbol.comment is None
        symbol.set_comment("/* this is a new comment */")

    # Check that the comment was added
    assert "// this is a new comment\nconst symbol = 1" in file.source
    assert "/*" not in file.source
    assert "*/" not in file.source


def test_set_comment_multiline(tmpdir) -> None:
    content = """
const symbol = 1
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        assert symbol.comment is None
        symbol.set_comment("this is a new comment\nthat spans multiple lines")

    # Check that the comment was added
    assert "// this is a new comment\n// that spans multiple lines\nconst symbol = 1" in file.source


def test_set_comment_with_indentation(tmpdir) -> None:
    content = """
class MyClass {
    foo() {}
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        my_class = file.get_symbol("MyClass")
        foo = my_class.get_method("foo")
        foo.set_comment("this is a new comment")

    # Check that the comment was added
    assert "    // this is a new comment\n    foo() {}" in file.source


def test_add_comment(tmpdir) -> None:
    content = """
// this is an existing comment
const symbol = 1
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        symbol.add_comment("this is a new comment")

    # Check that the comment was added
    assert "// this is an existing comment\n// this is a new comment\nconst symbol = 1" in file.source


def test_add_comment_new(tmpdir) -> None:
    content = """
const symbol = 1
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        symbol.add_comment("this is a new comment")

    # Check that the comment was added
    assert "// this is a new comment\nconst symbol = 1" in file.source


def test_add_comment_with_formatting(tmpdir) -> None:
    content = """
// this is an existing comment
const symbol = 1
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        symbol.add_comment("// this is a new comment")

    # Check that the comment was added
    assert "// this is an existing comment\n// this is a new comment\nconst symbol = 1" in file.source
    assert "////" not in file.source
    assert "// //" not in file.source


def test_add_comment_with_block_formatting(tmpdir) -> None:
    content = """
// this is an existing comment
const symbol = 1
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        symbol.add_comment("/* this is a new comment */")

    # Check that the comment was added
    assert "// this is an existing comment\n// this is a new comment\nconst symbol = 1" in file.source
    assert "/*" not in file.source
    assert "*/" not in file.source


def test_add_comment_multiline(tmpdir) -> None:
    content = """
// this is an existing comment
// that spans multiple lines
const symbol = 1
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        symbol.add_comment("this is a new comment\nthat spans multiple lines")

    # Check that the comment was added
    assert "// this is an existing comment\n// that spans multiple lines\n// this is a new comment\n// that spans multiple lines\nconst symbol = 1" in file.source


def test_add_comment_with_indentation(tmpdir) -> None:
    content = """
class MyClass {
    // this is an existing comment
    foo() {}
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        my_class = file.get_symbol("MyClass")
        foo = my_class.get_method("foo")
        foo.add_comment("this is a new comment")

    # Check that the comment was added
    assert "    // this is an existing comment\n    // this is a new comment\n    foo() {}" in file.source


def test_insert_comment(tmpdir) -> None:
    content = """
// this is a test comment
const symbol = 1
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        assert symbol.comment.source == "// this is a test comment"
        assert symbol.comment.text == "this is a test comment"
        symbol.set_comment("this is a new comment")

    # Check that the comment was inserted
    assert "// this is a new comment\nconst symbol = 1" in file.source


def test_insert_comment_block(tmpdir) -> None:
    content = """
/* this is a test comment */
const symbol = 1
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        symbol = file.get_symbol("symbol")
        assert symbol.comment.source == "/* this is a test comment */"
        assert symbol.comment.text == "this is a test comment"
        symbol.set_comment("this is a new comment")

    # Check that the comment was inserted
    assert "/* this is a new comment */\nconst symbol = 1" in file.source


def test_insert_comment_multiline(tmpdir) -> None:
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
        symbol.set_comment("this is a new comment\nthat spans multiple lines")

    # Check that the comment was inserted
    assert "// this is a new comment\n// that spans multiple lines\nconst symbol = 1" in file.source


def test_insert_comment_weird_spacing(tmpdir) -> None:
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
        symbol.set_comment("this is a new comment\n    that has weird spacing")

    # Check that the comment was inserted
    assert "// this is a new comment\n//     that has weird spacing\nconst symbol = 1" in file.source


def test_insert_comment_with_indentation(tmpdir) -> None:
    content = """
class MyClass {
    // this is a test comment
    foo() {}
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        my_class = file.get_symbol("MyClass")
        foo = my_class.get_method("foo")
        assert foo.comment.source == "// this is a test comment"
        assert foo.comment.text == "this is a test comment"
        foo.set_comment("this is a new comment")

    # Check that the comment was inserted
    assert "    // this is a new comment\n    foo() {}" in file.source
