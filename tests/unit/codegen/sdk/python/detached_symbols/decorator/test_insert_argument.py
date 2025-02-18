from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_insert_single_arg(tmpdir) -> None:
    FILENAME = "decorator.py"
    # language=python
    FILE_CONTENT = """
@decorator1(arg1="value1", arg2="value2", arg3="value3")
@decorator2(arg1="value1")
def foo(arg1, arg2, arg3):
    ...
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={FILENAME: FILE_CONTENT},
    ) as codebase:
        file = codebase.get_file("decorator.py")
        decorators = file.get_function("foo").decorators
        assert len(decorators) == 2
        assert len(decorators[0].call.args) == 3
        decorators[0].call.args.append('arg4="value"')
        codebase.commit()
        codebase.get_file("decorator.py")
        decorators = file.get_function("foo").decorators
        assert len(decorators[0].call.args) == 4
        assert decorators[0].call.args[3].name == "arg4"
