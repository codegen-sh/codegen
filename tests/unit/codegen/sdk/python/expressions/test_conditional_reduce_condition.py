from typing import TYPE_CHECKING, Any

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.python.file import PyFile


def test_reduce_ternary_condition_to_true(tmpdir: Any) -> None:
    # language=python
    content = """
def foo() -> None:
    result = 'valueA' if a else 'valueB'
    print(result)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.py": content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        file: PyFile = codebase.get_file("dir/file1.py")
        foo = file.get_function("foo")
        ternary_expr = foo.code_block.statements[0].value
        ternary_expr.reduce_condition(True)
    # language=python
    assert (
        file.content
        == """
def foo() -> None:
    result = 'valueA'
    print(result)
    """
    )


def test_reduce_ternary_condition_to_false(tmpdir: Any) -> None:
    # language=python
    content = """
def foo() -> None:
    result = 'valueA' if a else 'valueB'
    print(result)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.py": content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        file: PyFile = codebase.get_file("dir/file1.py")
        foo = file.get_function("foo")
        ternary_expr = foo.code_block.statements[0].value
        ternary_expr.reduce_condition(False)
    # language=python
    assert (
        file.content
        == """
def foo() -> None:
    result = 'valueB'
    print(result)
    """
    )


def test_reduce_nested_ternary_condition_to_true_and_false(tmpdir: Any) -> None:
    # language=python
    content = """
def foo() -> None:
    result = 'valueB_true' if b else 'valueB_false' if a else 'valueA'
    print(result)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.py": content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        file: PyFile = codebase.get_file("dir/file1.py")
        foo = file.get_function("foo")
        outer_ternary = foo.code_block.statements[0].value
        inner_ternary = outer_ternary.alternative
        inner_ternary.reduce_condition(True)
        outer_ternary.reduce_condition(True)
    # language=python
    assert (
        file.content
        == """
def foo() -> None:
    result = 'valueB_true'
    print(result)
    """
    )


def test_reduce_nested_ternary_condition_outer_false(tmpdir: Any) -> None:
    # language=python
    content = """
def foo() -> None:
    result = 'valueB_true' if b else 'valueB_false' if a else 'valueA'
    print(result)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.py": content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        file: PyFile = codebase.get_file("dir/file1.py")
        foo = file.get_function("foo")
        outer_ternary = foo.code_block.statements[0].value
        outer_ternary.reduce_condition(False)
    # language=python
    assert (
        file.content
        == """
def foo() -> None:
    result = 'valueB_false' if a else 'valueA'
    print(result)
    """
    )


def test_reduce_multiple_ternary_conditions(tmpdir: Any) -> None:
    # language=python
    content = """
def foo() -> None:
    result1 = 'valueA' if a else 'valueB'
    result2 = 'valueC' if b else 'valueD'
    print(result1, result2)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.py": content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        file: PyFile = codebase.get_file("dir/file1.py")
        foo = file.get_function("foo")
        ternary_expr1 = foo.code_block.statements[0].value
        ternary_expr2 = foo.code_block.statements[1].value
        ternary_expr1.reduce_condition(True)
        ternary_expr2.reduce_condition(False)
    # language=python
    assert (
        file.content
        == """
def foo() -> None:
    result1 = 'valueA'
    result2 = 'valueD'
    print(result1, result2)
    """
    )


def test_reduce_ternary_condition_with_function_call(tmpdir: Any) -> None:
    # language=python
    content = """
def foo() -> None:
    result = 'valueA' if is_true(a) else 'valueB'
    print(result)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.py": content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        file: PyFile = codebase.get_file("dir/file1.py")
        foo = file.get_function("foo")
        ternary_expr = foo.code_block.statements[0].value
        ternary_expr.reduce_condition(False)
    # language=python
    assert (
        file.content
        == """
def foo() -> None:
    result = 'valueB'
    print(result)
    """
    )
