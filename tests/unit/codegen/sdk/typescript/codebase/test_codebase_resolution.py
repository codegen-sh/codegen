from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_codebase_resolution(tmpdir) -> None:
    file1_name = "file1.ts"
    file2_name = "file2.ts"
    # language=typescript
    file1_content = """
import { bar } from "./file2";

const square = bar();
square.meth()
    """
    # language=typescript
    file2_content = """
class A {
    public meth(): void {
    }
}
export function bar(): A {
}
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        files={
            file1_name: file1_content,
            file2_name: file2_content,
        },
        programming_language=ProgrammingLanguage.TYPESCRIPT,
    ) as codebase:
        file = codebase.get_file(file1_name)
        square = file.get_symbol("square")
        imp = file.imports[0]
        file2 = codebase.get_file(file2_name)
        bar = file2.get_symbol("bar")
        exp = file2.exports[0]
        a = file2.get_symbol("A")
        meth = a.get_method("meth")
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
        assert resolution.parent_frame.parent_frame.node == exp
        assert resolution.parent_frame.parent_frame.aliased == False
        assert resolution.parent_frame.parent_frame.direct == True
        assert resolution.parent_frame.parent_frame.parent_frame.node == bar
        assert resolution.parent_frame.parent_frame.parent_frame.parent_frame is None
        call = file.function_calls[1]
        call_name = call.get_name()
        call_resolutions = call_name.resolved_type_frames
        assert len(call_resolutions) == 1
        call_resolution = call_resolutions[0]
        assert call_resolution.node == call_name
        assert call_resolution.aliased == False
        assert call_resolution.direct == True
        assert call_resolution.chained == True
        assert call_resolution.parent_frame.node == meth
        assert call_resolution.parent_frame.parent_frame is None
        assert len(meth.usages) == 1


def test_codebase_resolution_aliased(tmpdir) -> None:
    file1_name = "file1.ts"
    file2_name = "file2.ts"
    # language=typescript
    file1_content = """
import { bar as baz } from "./file2";

const square = baz();
square.meth()
    """
    # language=typescript
    file2_content = """
class A {
    public meth(): void {
    }
}
export function bar(): A {
}
    """
    with get_codebase_session(
        tmpdir=tmpdir,
        files={
            file1_name: file1_content,
            file2_name: file2_content,
        },
        programming_language=ProgrammingLanguage.TYPESCRIPT,
    ) as codebase:
        file = codebase.get_file(file1_name)
        square = file.get_symbol("square")
        imp = file.imports[0]
        file2 = codebase.get_file(file2_name)
        bar = file2.get_symbol("bar")
        a = file2.get_symbol("A")
        meth = a.get_method("meth")
        exp = file2.exports[0]
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
        assert resolution.parent_frame.parent_frame.node == exp
        assert resolution.parent_frame.parent_frame.aliased == False
        assert resolution.parent_frame.parent_frame.direct == True
        assert resolution.parent_frame.parent_frame.parent_frame.node == bar
        assert resolution.parent_frame.parent_frame.parent_frame.parent_frame is None
        call = file.function_calls[1]
        call_name = call.get_name()
        call_resolutions = call_name.resolved_type_frames
        assert len(call_resolutions) == 1
        call_resolution = call_resolutions[0]
        assert call_resolution.node == call_name
        assert call_resolution.aliased == False
        assert call_resolution.direct == True
        assert call_resolution.chained == True
        assert call_resolution.parent_frame.node == meth
        assert call_resolution.parent_frame.parent_frame is None
        assert len(meth.usages) == 1


def test_codebase_resolution_aliased_export(tmpdir) -> None:
    file1_name = "file1.ts"
    file2_name = "file2.ts"
    # language=typescript
    file1_content = """
import baz from "./file2";

const square = baz();
square.meth()
    """
    # language=typescript
    file2_content = """
class A {
    public meth(): void {
    }
}
function bar(): A {
}
export default { baz: bar };
    """
    with get_codebase_session(
        tmpdir=tmpdir,
        files={
            file1_name: file1_content,
            file2_name: file2_content,
        },
        programming_language=ProgrammingLanguage.TYPESCRIPT,
    ) as codebase:
        file = codebase.get_file(file1_name)
        square = file.get_symbol("square")
        imp = file.imports[0]
        file2 = codebase.get_file(file2_name)
        bar = file2.get_symbol("bar")
        a = file2.get_symbol("A")
        meth = a.get_method("meth")
        exp = file2.exports[0]
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
        assert resolution.parent_frame.parent_frame.node == exp
        assert resolution.parent_frame.parent_frame.aliased == True
        assert resolution.parent_frame.parent_frame.direct == True
        assert resolution.parent_frame.parent_frame.parent_frame.node == bar
        assert resolution.parent_frame.parent_frame.parent_frame.parent_frame is None
        call = file.function_calls[1]
        call_name = call.get_name()
        call_resolutions = call_name.resolved_type_frames
        call_resolution = call_resolutions[0]
        assert call_resolution.node == call_name
        assert call_resolution.aliased == False
        assert call_resolution.chained == True
        assert call_resolution.direct == True
        assert call_resolution.parent_frame.node == meth
        assert call_resolution.parent_frame.parent_frame is None
        assert len(meth.usages) == 1
