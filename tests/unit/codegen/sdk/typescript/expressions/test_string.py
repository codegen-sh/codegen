import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.expressions import String
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_string_edit(tmpdir) -> None:
    file = "test.ts"
    # language=typescript
    content = """
function foo() {
    let symbol = "test_string"
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)
        foo = codebase.get_symbol("foo")
        string = foo.code_block.statements[0].right
        assert isinstance(string, String)
        assert string == "test_string"
        string.content_nodes[0].edit("boop")
    # language=typescript
    assert (
        file.content
        == """
function foo() {
    let symbol = "boop"
}
"""
    )


def test_string_empty(tmpdir) -> None:
    file = "test.ts"
    # language=typescript
    content = """
function foo() {
    let symbol = ""
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)
        foo = codebase.get_symbol("foo")
        string = foo.code_block.statements[0].right
        assert isinstance(string, String)
        assert string == ""


def test_string_escape_sequence(tmpdir) -> None:
    # language=typescript
    content = """
const escaped = "test1\\test2"
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        f = codebase.files[0]
        escaped = f.code_block.statements[0].right
        assert isinstance(escaped, String)
        assert escaped == "test1\\test2"


@pytest.mark.xfail(reason="Empty string edit not implemented")
def test_string_empty_edit(tmpdir) -> None:
    file = "test.ts"
    # language=typescript
    content = """
function foo() {
    let symbol = ""
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)
        foo = codebase.get_symbol("foo")
        string = foo.code_block.statements[0].right
        assert isinstance(string, String)
        assert string == ""
        string.content_nodes[0].edit("boop")
    # language=typescript
    assert (
        file.content
        == """
function foo() {
    let symbol = "boop"
}
"""
    )


def test_string_expressions(tmpdir) -> None:
    # language=typescript
    content = """
const a = `${foo(x, y)} + ${bar()}`;
    """
    with get_codebase_session(tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        f = codebase.get_file("test.ts")
        a = f.get_global_var("a")
        assert isinstance(a.value, String)
        assert a.value == "`${foo(x, y)} + ${bar()}`"
        assert len(a.value.expressions) == 2
        assert a.value.expressions[0] == "foo(x, y)"
        assert a.value.expressions[1] == "bar()"
