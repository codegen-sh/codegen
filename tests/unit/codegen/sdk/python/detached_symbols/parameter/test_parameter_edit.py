from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.core.function import Function


def test_edit_parameter_in_function_definition(tmpdir) -> None:
    filename = "test.py"
    # language=python
    file_content = """
def addNumbers(a: int, b: int) -> int:
    return a + b
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.PYTHON, files={filename: file_content}) as codebase:
        file = codebase.get_file(filename)
        symbol: Function = file.get_symbol("addNumbers")
        assert symbol is not None
        assert len(symbol.parameters) == 2
        symbol.parameters[0].edit("c: int")

    assert "c: int" in file.content
    assert "a: int" not in file.content


def test_edit_multiple_parameters_in_function_definition(tmpdir) -> None:
    filename = "test.py"
    # language=python
    file_content = """
def addNumbers(a: int, b: int) -> int:
    return a + b
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.PYTHON, files={filename: file_content}) as codebase:
        file = codebase.get_file(filename)
        symbol: Function = file.get_symbol("addNumbers")
        assert symbol is not None
        assert len(symbol.parameters) == 2
        symbol.parameters[0].edit("c: int")
        symbol.parameters[1].edit("d: int")

    assert "c: int" in file.content
    assert "a: int" not in file.content
    assert "d: int" in file.content
    assert "b: int" not in file.content
