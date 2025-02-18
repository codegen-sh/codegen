from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_function_level_gets_nested_function(tmpdir) -> None:
    FILENAME = "function_test.ts"
    # language=typescript
    FILE_CONTENT = """
function f(): void {
    // Empty function body
}

class A {
    foo(): void {
        // Empty method body
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILENAME: FILE_CONTENT}) as codebase:
        # Test top-level function
        function_f = codebase.get_symbol("f")
        assert function_f.code_block.level == 1

        # Test nested methods and functions
        class_A = codebase.get_symbol("A")
        method_foo = class_A.get_method("foo")
        assert method_foo.code_block.level == 2
