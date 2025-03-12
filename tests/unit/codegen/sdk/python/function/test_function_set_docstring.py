from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.core.function import Function


def test_set_docstring(tmpdir) -> None:
    FILENAME = "file.py"

    # language=python
    FILE_CONTENT = """
def foo():
    \"\"\"This is a docstring\"\"\"
    return 1

def bar():
    return 2

class A():
    def baz(self):
        return 3
    """

    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={FILENAME: FILE_CONTENT},
    ) as codebase:
        file = codebase.get_file(FILENAME)

        # Check setting docstring
        foo: Function = file.get_function("foo")
        foo.docstring.edit_text("This is a new docstring")

    foo: Function = file.get_function("foo")

    assert "This is a new docstring" in foo.docstring.text
    assert "This is a docstring" not in foo.docstring.text
    assert "return 1" in foo.source

    # Check setting docstring no quotes
    foo = file.get_function("foo")
    foo.docstring.edit_text("This is a another docstring")

    codebase.ctx.commit_transactions()
    foo = file.get_function("foo")

    assert "This is a another docstring" in foo.docstring.text
    assert "This is a new docstring" not in foo.docstring.text
    assert "return 1" in foo.source

    # Check creating a new docstring
    bar = file.get_function("bar")
    bar.set_docstring("This is a brand new docstring")

    codebase.ctx.commit_transactions()
    bar = file.get_symbol("bar")

    assert "This is a brand new docstring" in bar.docstring.text
    assert "return 2" in bar.source

    # Check creating a multi-line docstring
    baz = file.get_class("A").get_method("baz")
    baz.set_docstring(".\nThis is a multi-line docstring\n.")

    codebase.ctx.commit_transactions()
    baz = file.get_class("A").get_method("baz")

    assert "This is a multi-line docstring" in baz.docstring.text
    assert "        This is a multi-line docstring" in baz.extended_source
    assert "return 3" in baz.source

    # Check modifying a multi-line docstring
    baz = file.get_class("A").get_method("baz")
    baz.docstring.edit_text(".\nThis is a new multi-line docstring\n.")

    codebase.ctx.commit_transactions()
    baz = file.get_class("A").get_method("baz")

    assert "This is a new multi-line docstring" in baz.docstring.text
    assert "        This is a new multi-line docstring" in baz.extended_source
    assert "This is a multi-line docstring" not in baz.docstring.text
    assert "return 3" in baz.source
