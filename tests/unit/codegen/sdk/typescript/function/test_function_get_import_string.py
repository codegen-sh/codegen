from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_function_get_import_string_with_alias(tmpdir) -> None:
    # language=typescript
    src_file = """
function foo() {
    return 1;
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"src.ts": src_file}) as codebase:
        file = codebase.get_file("src.ts")
        foo_function = file.get_symbol("foo")
        import_string = foo_function.get_import_string(alias="bar")
        assert import_string == "import { foo as bar } from 'src';"
