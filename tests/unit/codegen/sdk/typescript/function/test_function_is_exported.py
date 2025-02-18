from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_function_named_function_is_exported_should_return_true(tmpdir) -> None:
    file = """
export function add_symbol_to_file() {
    let x = new Array([1,2,3,4,5,6,7,8,9,10]);
    return x
}
    """
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")
        add_symbol_to_file = file.get_symbol("add_symbol_to_file")
        assert add_symbol_to_file.is_exported


def test_function_arrow_function_is_exported_should_return_true(tmpdir) -> None:
    file = """
export const exportedEqualsFunction = (arg) => {
    const x = 0
    return arg.equals(x);
}

const equalsFunction = (arg) => {
    return arg.equals(a);
}
    """
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")

        exported_equals_function = file.get_symbol("exportedEqualsFunction")
        assert exported_equals_function.is_exported


def test_function_arrow_function_is_exported_should_return_false(tmpdir) -> None:
    file = """
const equalsFunction = (arg) => {
    return arg.equals(a);
}
    """
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")

        exported_equals_function = file.get_symbol("equalsFunction")
        assert not exported_equals_function.is_exported
