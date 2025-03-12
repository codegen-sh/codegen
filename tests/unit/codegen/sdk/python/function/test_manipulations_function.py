# TODO: break-up these tests into API specific tests, ex: one test file for set_return_type

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_prepend_to_function_body_with_docstring(tmpdir) -> None:
    FILE_NAME = "test.py"
    # language=python
    FILE_CONTENT = """
def foo():
    '''
    This is a docstring for foo()
    '''
    func_call(a, b, c)
    return "hello world"
    """
    # language=python
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={FILE_NAME: FILE_CONTENT},
    ) as codebase:
        file = codebase.get_file(FILE_NAME)
        func = file.get_function("foo")
        fcall = func.function_calls[0]
        fcall.args[0].edit('"xyz"')
        fcall.rename("func_call_2")

        lines = """a = 1
b = 2
c = 3"""
        func.prepend_statements(lines)

    # language=python
    expected_content = """
def foo():
    '''
    This is a docstring for foo()
    '''
    a = 1
    b = 2
    c = 3
    func_call_2("xyz", b, c)
    return "hello world"
    """
    assert file.content == expected_content


def test_prepend_to_function_body_without_docstring(tmpdir) -> None:
    FILE_NAME = "test.py"
    # language=python
    FILE_CONTENT = """
def foo():
    func_call(a, b, c)
    return "hello world"
    """
    # language=python
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={FILE_NAME: FILE_CONTENT},
    ) as codebase:
        file = codebase.get_file(FILE_NAME)
        func = file.get_function("foo")
        fcall = func.function_calls[0]
        fcall.args[0].edit('"xyz"')
        fcall.rename("func_call_2")

        lines = """a = 1
b = 2
c = 3"""
        func.prepend_statements(lines)

    # language=python
    expected_content = """
def foo():
    a = 1
    b = 2
    c = 3
    func_call_2("xyz", b, c)
    return "hello world"
    """
    assert file.content == expected_content


def test_prepend_statements_to_function_with_docstring(tmpdir) -> None:
    FILE_NAME = "test.py"
    # language=python
    FILE_CONTENT = '''def example_function(
    param1: int,
    param2: str,
    param3: dict,
    param4: list,
) -> bool:
    """
    This is an example docstring.
    """

    result = process_data(
        data=param1
    )
    validate_result(result)
'''
    # language=python
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={FILE_NAME: FILE_CONTENT},
    ) as codebase:
        file = codebase.get_file(FILE_NAME)
        func = file.get_function("example_function")

        lines = """setup_data = initialize_params()  # Added initialization step"""
        func.prepend_statements(lines)

    # language=python
    expected_content = '''def example_function(
    param1: int,
    param2: str,
    param3: dict,
    param4: list,
) -> bool:
    """
    This is an example docstring.
    """

    setup_data = initialize_params()  # Added initialization step
    result = process_data(
        data=param1
    )
    validate_result(result)
'''
    assert file.content == expected_content


def test_set_return_type_return_type_does_not_exist(tmpdir) -> None:
    FILE_NAME = "test.py"
    # language=python
    FILE_CONTENT = """
def foo():
    return 1
    """
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={FILE_NAME: FILE_CONTENT},
    ) as codebase:
        file = codebase.get_file(FILE_NAME)
        func = file.get_function("foo")
        func.set_return_type("int")

    # language=python
    expected_content = """
def foo() -> int:
    return 1
    """
    assert file.content == expected_content


def test_set_return_type_return_type_already_exists(tmpdir) -> None:
    FILE_NAME = "test.py"
    # language=python
    FILE_CONTENT = """
def foo() -> str:
    return 1
    """
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={FILE_NAME: FILE_CONTENT},
    ) as codebase:
        file = codebase.get_file(FILE_NAME)
        func = file.get_function("foo")
        func.set_return_type("int")

    # language=python
    expected_content = """
def foo() -> int:
    return 1
    """
    assert file.content == expected_content


def test_set_return_type_empty_string_removes(tmpdir) -> None:
    FILE_NAME = "test.py"
    # language=python
    FILE_CONTENT = """
def foo() -> str:
    return 1
    """
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={FILE_NAME: FILE_CONTENT},
    ) as codebase:
        file = codebase.get_file(FILE_NAME)
        func = file.get_function("foo")
        func.set_return_type("")

    # language=python
    expected_content = """
def foo():
    return 1
    """
    assert file.content == expected_content


def test_set_return_type_trim_arrow_prefix(tmpdir) -> None:
    FILE_NAME = "test.py"
    # language=python
    FILE_CONTENT = """
def foo() -> str:
    return 1
    """
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={FILE_NAME: FILE_CONTENT},
    ) as codebase:
        file = codebase.get_file(FILE_NAME)
        func = file.get_function("foo")
        func.set_return_type(" -> int")

    # language=python
    expected_content = """
def foo() -> int:
    return 1
    """
    assert file.content == expected_content


def test_add_parameter(tmpdir) -> None:
    FILE_NAME = "test.py"
    # language=python
    FILE_CONTENT = """
def foo(a, b: int, c: str = None) -> int:
    return 1
    """
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={FILE_NAME: FILE_CONTENT},
    ) as codebase:
        file = codebase.get_file(FILE_NAME)
        func = file.get_function("foo")
        func.parameters.append("d: int = 1")

    # language=python
    expected_content = """
def foo(a, b: int, c: str = None, d: int = 1) -> int:
    return 1
    """
    assert file.content == expected_content
