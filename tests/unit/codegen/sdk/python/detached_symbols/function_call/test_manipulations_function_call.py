# TODO: convert all of this to use mock files/tmpdir

from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.core.file import SourceFile
    from codegen.sdk.core.function import Function


def test_replace_function_call_arg(tmpdir) -> None:
    filename = "test_arg.py"
    # language=python
    file_content = """
def func_2(a: int, b: int) -> int:
    return a + b

def func_1(a: int, b: int) -> int:
    return func_2(a, b)
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={filename: file_content},
    ) as codebase:
        test_file: SourceFile = codebase.get_file("test_arg.py")
        test_func_1: Function = test_file.get_symbol("func_1")
        test_func_1_call = test_func_1.function_calls[0]
        test_func_1_call.args[0].edit("new_arg")

    assert "func_2(new_arg, b)" in test_file.content


def test_replace_function_call_arg_sequence(tmpdir) -> None:
    filename = "test_arg_sequence.py"
    # language=python
    file_content = """
def func_2(a: int, b: int) -> int:
    return a + b

def func_1(a: int, b: int) -> int:
    return func_2(a, b)
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={filename: file_content},
    ) as codebase:
        test_file: SourceFile = codebase.get_file("test_arg_sequence.py")
        test_func_1: Function = test_file.get_function("func_1")
        test_func_1_call = test_func_1.function_calls[0]
        # NOTE: make the modifications in reverse order.
        test_func_1_call.args[1].edit("new_arg_b")
        test_func_1_call.args[0].edit("new_arg_a")

    assert "func_2(new_arg_a, new_arg_b)" in test_file.content


def test_replace_function_call_kwarg(tmpdir) -> None:
    filename = "test_kwarg.py"
    # language=python
    file_content = """
def func_2(a: int, b: int) -> int:
    return a + b

def func_1(a: int, b: int) -> int:
    return func_2(a=a, b=b)
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={filename: file_content},
    ) as codebase:
        test_file: SourceFile = codebase.get_file("test_kwarg.py")
        test_func_1: Function = test_file.get_symbol("func_1")
        test_func_1_call = test_func_1.function_calls[0]
        test_func_1_call.args[0].edit("a=new_arg")

    assert "func_2(a=new_arg, b=b)" in test_file.content
