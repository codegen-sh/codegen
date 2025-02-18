from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.dataclasses.usage import UsageType
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_codebase_resolution(tmpdir) -> None:
    file1_name = "file1.py"
    file2_name = "file2.py"
    # language=python
    file1_content = """
from file2 import bar

square = bar()
square.method()
    """
    # language=python
    file2_content = """
class A():
    def method(self):
        pass
def bar() -> A:
    pass
    """
    with get_codebase_session(
        tmpdir=tmpdir,
        files={
            file1_name: file1_content,
            file2_name: file2_content,
        },
        programming_language=ProgrammingLanguage.PYTHON,
    ) as codebase:
        file = codebase.get_file(file1_name)
        square = file.get_symbol("square")
        imp = file.imports[0]
        file2 = codebase.get_file(file2_name)
        bar = file2.get_symbol("bar")
        a = file2.get_symbol("A")
        method = a.get_method("method")
        sq_call = square.value
        name = sq_call.get_name()
        resolutions = name.resolved_type_frames
        assert len(resolutions) == 1
        resolution = resolutions[0]
        assert resolution.node == name
        assert resolution.aliased == False
        assert resolution.direct == True
        assert resolution.parent_frame.node == imp
        assert resolution.parent_frame.aliased == False
        assert resolution.parent_frame.direct == False
        assert resolution.parent_frame.parent_frame.node == bar
        assert resolution.parent_frame.parent_frame.direct == True
        assert resolution.parent_frame.parent_frame.parent_frame is None
        call = file.function_calls[1]
        call_name = call.get_name()
        call_resolutions = call_name.resolved_type_frames
        assert len(call_resolutions) == 1
        call_resolution = call_resolutions[0]
        assert call_resolution.node == call_name
        assert call_resolution.aliased == False
        assert call_resolution.direct == True
        assert call_resolution.chained == True
        assert call_resolution.parent_frame.node == method
        assert call_resolution.parent_frame.parent_frame is None
        assert len(method.usages) == 1
        assert len(method.usages) == 1
        assert len(method.usages(UsageType.CHAINED)) == 1


def test_codebase_resolution_aliased(tmpdir) -> None:
    file1_name = "file1.py"
    file2_name = "file2.py"
    # language=python
    file1_content = """
from file2 import bar as baz

square = baz()
square.method()
    """
    # language=python
    file2_content = """
class A():
    def method():
        pass
def bar() -> A:
    pass
    """
    with get_codebase_session(
        tmpdir=tmpdir,
        files={
            file1_name: file1_content,
            file2_name: file2_content,
        },
        programming_language=ProgrammingLanguage.PYTHON,
    ) as codebase:
        file = codebase.get_file(file1_name)
        square = file.get_symbol("square")
        imp = file.imports[0]
        file2 = codebase.get_file(file2_name)
        bar = file2.get_symbol("bar")
        a = file2.get_symbol("A")
        method = a.get_method("method")
        sq_call = square.value
        name = sq_call.get_name()
        resolutions = name.resolved_type_frames
        assert len(resolutions) == 1
        resolution = resolutions[0]
        assert resolution.node == name
        assert resolution.aliased == False
        assert resolution.direct == True
        assert resolution.parent_frame.node == imp
        assert resolution.parent_frame.aliased == True
        assert resolution.parent_frame.direct == False
        assert resolution.parent_frame.parent_frame.node == bar
        assert resolution.parent_frame.parent_frame.direct == True
        assert resolution.parent_frame.parent_frame.parent_frame is None
        call = file.function_calls[1]
        call_name = call.get_name()
        call_resolutions = call_name.resolved_type_frames
        assert len(call_resolutions) == 1
        call_resolution = call_resolutions[0]
        assert call_resolution.node == call_name
        assert call_resolution.aliased == False
        assert call_resolution.direct == True
        assert call_resolution.chained == True
        assert call_resolution.parent_frame.node == method
        assert call_resolution.parent_frame.parent_frame is None
        assert len(method.usages) == 1
