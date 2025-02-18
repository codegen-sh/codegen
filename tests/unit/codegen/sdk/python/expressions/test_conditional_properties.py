from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.python.file import PyFile


def test_parse_simple_conditional_expression(tmpdir: str) -> None:
    # language=python
    content = """
result = a + b if a + b else b
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.py": content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        file: PyFile = codebase.get_file("dir/file1.py")
        expression = file.symbols[0].value
        assert expression.condition.source == "a + b"
        assert expression.consequence.source == "a + b"
        assert expression.alternative.source == "b"


def test_parse_nested_conditional_expressions(tmpdir: str) -> None:
    # language=python
    content = """
result = c if a else (d if b else e)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.py": content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        file: PyFile = codebase.get_file("dir/file1.py")
        top_expression = file.symbols[0].value
        nested_expression = top_expression.alternative.resolve()
        assert top_expression.condition.source == "a"
        assert top_expression.consequence.source == "c"
        assert top_expression.alternative.source == "(d if b else e)"
        assert nested_expression.condition.source == "b"
        assert nested_expression.consequence.source == "d"
        assert nested_expression.alternative.source == "e"


def test_parse_complex_conditional_expression(tmpdir: str) -> None:
    # language=python
    content = """
result = a if (a + b) else (c if b else d)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.py": content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        file: PyFile = codebase.get_file("dir/file1.py")
        top_expression = file.symbols[0].value
        nested_expression = top_expression.alternative.resolve()
        assert top_expression.condition.source == "(a + b)"
        assert top_expression.consequence.source == "a"
        assert top_expression.alternative.source == "(c if b else d)"
        assert nested_expression.condition.source == "b"
        assert nested_expression.consequence.source == "c"
        assert nested_expression.alternative.source == "d"
