from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_parameter_default_value(tmpdir) -> None:
    # language=typescript
    content = """
const DEFAULT_VALUE: number = 3;

function foo(x: number = DEFAULT_VALUE): number {
    return x + 1;
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        default_val_var = file.get_global_var("DEFAULT_VALUE")
        function_symbol = file.get_function("foo")

        assert len(function_symbol.parameters) == 1
        param = function_symbol.parameters[0]

        # First Parameter
        assert param.name == "x"
        assert param.is_typed
        assert param.type == "number"
        assert param.value == "DEFAULT_VALUE"

        assert len(default_val_var.usages) == 2
        assert default_val_var.usages[1].match == param.value
        assert default_val_var.usages[0].match.parent_statement == function_symbol.code_block.statements[0]
