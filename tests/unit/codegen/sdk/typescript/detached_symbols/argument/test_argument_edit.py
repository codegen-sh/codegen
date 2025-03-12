from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.core.file import SourceFile
    from codegen.sdk.core.function import Function


def test_edit_arg_in_function_call(tmpdir) -> None:
    filename = "test_arg.ts"
    # language=typescript
    file_content = """
function func2(a: number, b: number): number {
    return a + b;
}

function func1(a: number, b: number): number {
    return func2(a, b);
}
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={filename: file_content}) as codebase:
        test_file: SourceFile = codebase.get_file("test_arg.ts")
        test_func_1: Function = test_file.get_symbol("func1")
        test_func_1_call = test_func_1.function_calls[0]
        test_func_1_call.args[0].edit("new_arg")

    assert "func2(new_arg, b)" in test_file.content


def test_edit_multiple_args_in_function_call(tmpdir) -> None:
    filename = "test_arg_sequence.ts"
    # language=typescript
    file_content = """
function func2(a: number, b: number): number {
    return a + b;
}

function func1(a: number, b: number): number {
    return func2(a, b);
}
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={filename: file_content}) as codebase:
        test_file: SourceFile = codebase.get_file("test_arg_sequence.ts")
        test_func_1: Function = test_file.get_symbol("func1")
        test_func_1_call = test_func_1.function_calls[0]
        # NOTE: make the modifications in reverse order.
        test_func_1_call.args[1].edit("new_arg_b")
        test_func_1_call.args[0].edit("new_arg_a")

    assert "func2(new_arg_a, new_arg_b)" in test_file.content


def test_edit_arg_in_recursive_function_call(tmpdir) -> None:
    filename = "test_arg.ts"
    # language=typescript
    file_content = """
export function recursive(a: string, b: string): string | undefined {
    return Object.values(a).find((item) => {
        if (b(item)) {
            return true;
        }
        return recursive(item.value, b);
    });
}

"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={filename: file_content}) as codebase:
        file = codebase.get_file("test_arg.ts")
        symbol = file.get_symbol("recursive")
        assert symbol is not None
        calls = symbol.function_calls
        assert len(calls) > 1
        call = calls[3]
        assert "recursive" in [x.name for x in calls]
        assert "recursive" == call.name
        call.args[0].edit("NEW_ARG")

    assert "NEW_ARG" in file.content
    assert "        return recursive(NEW_ARG, b);" in file.content
    assert "        return recursive(item.value, b);" not in file.content
