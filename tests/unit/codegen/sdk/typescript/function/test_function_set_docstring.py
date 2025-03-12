from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_set_docstring_multiline(tmpdir) -> None:
    FILENAME = "file.ts"
    # language=typescript
    FILE_CONTENT = """
/**
* This is a docstring
*/
function foo(): number {
    return 1;
}

function bar(): number {
    return 2;
}

class A {
    baz(): number {
        return 3;
    }
}
    """

    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILENAME: FILE_CONTENT}) as codebase:
        file = codebase.get_file(FILENAME)

        # Check setting docstring
        foo = file.get_symbol("foo")
        foo.docstring.edit_text("This is a new docstring")

    foo = file.get_symbol("foo")
    assert "This is a new docstring" in foo.docstring.text
    assert "This is a docstring" not in foo.docstring.text
    assert "return 1;" in foo.extended_source

    # Check setting docstring no quotes
    foo = file.get_symbol("foo")
    foo.docstring.edit_text("This is a another docstring")
    codebase.ctx.commit_transactions()
    foo = file.get_symbol("foo")
    assert "This is a another docstring" in foo.docstring.text
    assert "This is a new docstring" not in foo.docstring.text
    assert "return 1;" in foo.extended_source

    # Check creating a new docstring
    bar = file.get_symbol("bar")
    bar.set_docstring("This is a brand new docstring")
    codebase.ctx.commit_transactions()
    bar = file.get_symbol("bar")
    assert "This is a brand new docstring" in bar.docstring.text
    assert "return 2;" in bar.extended_source

    # Check creating a multi-line docstring
    baz = file.get_symbol("A").get_method("baz")
    baz.set_docstring(".\nThis is a multi-line docstring\n.")
    codebase.ctx.commit_transactions()
    baz = file.get_symbol("A").get_method("baz")
    assert "    * This is a multi-line docstring" in baz.extended_source
    assert "This is a multi-line docstring" in baz.docstring.text
    assert "return 3;" in baz.extended_source

    # Check modifying a multi-line docstring
    baz = file.get_symbol("A").get_method("baz")
    baz.docstring.edit_text(".\nThis is a new multi-line docstring\n.")
    codebase.ctx.commit_transactions()
    baz = file.get_symbol("A").get_method("baz")
    assert "    * This is a new multi-line docstring" in baz.extended_source
    assert "This is a new multi-line docstring" in baz.docstring.text
    assert "This is a multi-line docstring" not in baz.docstring.text
    assert "return 3;" in baz.extended_source
