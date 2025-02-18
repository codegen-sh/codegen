from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_function_call_is_awaited_basic(tmpdir) -> None:
    # language=python
    file = """
if (a):
    return await b()

c()
await d()
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.PYTHON, files={"test.py": file}) as codebase:
        file = codebase.get_file("test.py")
        assert len(file.function_calls) == 3

        # Check if the function calls are awaited
        assert file.function_calls[0].is_awaited
        assert not file.function_calls[1].is_awaited
        assert file.function_calls[2].is_awaited


def test_function_call_is_awaited_wrapped(tmpdir) -> None:
    # language=python
    file = """
if (a):
    return await (b())
c()
(d())
await (((e())))
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.PYTHON, files={"test.py": file}) as codebase:
        file = codebase.get_file("test.py")
        assert len(file.function_calls) == 4

        # Check if the function calls are awaited
        assert file.function_calls[0].is_awaited
        assert not file.function_calls[1].is_awaited
        assert not file.function_calls[2].is_awaited
        assert file.function_calls[3].is_awaited
