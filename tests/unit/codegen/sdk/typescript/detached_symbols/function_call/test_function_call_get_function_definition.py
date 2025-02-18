import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


# ED_TODO: Requires fix to get_function_definition. Check if that is possible
@pytest.mark.skip("TODO(CG-8779): get this test working")
def test_function_call_get_function_definition_returns_function(tmpdir) -> None:
    src_file = """
function foo() {
    print('foo')
}
"""
    dest_file = """
import { foo } from './src'

function bar() {
    foo()
}
"""

    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"src.ts": src_file, "dest.ts": dest_file}) as ctx:
        src_file = ctx.get_file("src.ts")
        dest_file = ctx.get_file("dest.ts")
        foo_function = src_file.get_symbol("foo")
        dest_foo_fcall = dest_file.get_symbol("bar").function_calls[0]
        assert dest_foo_fcall
        assert dest_foo_fcall.function_definition is foo_function
