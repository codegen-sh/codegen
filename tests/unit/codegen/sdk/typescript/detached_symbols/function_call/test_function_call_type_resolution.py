from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_function_call_name_resolution_unary_expression(tmpdir) -> None:
    # language=typescript
    content = """
import { foo, myVar1, myVar2 } from './file2'

function bar() {
    !foo('str_arg', myVar1).get<string[]>(myVar2, [])
}
    """
    # language=typescript
    content2 = """
export const myVar1 = 5;
export let myVar2 = 7;
export function foo(arg1: string, arg2: number): string[] {
    return ["val1", "val2"]
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"file1.ts": content, "file2.ts": content2}) as codebase:
        file1 = codebase.get_file("file1.ts")
        assert set(file1.get_function("bar").dependencies) == {file1.get_import("foo"), file1.get_import("myVar1"), file1.get_import("myVar2")}
        assert len(file1.get_function("bar").dependencies) == 3
