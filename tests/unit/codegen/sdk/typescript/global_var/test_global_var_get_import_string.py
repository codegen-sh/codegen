from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.enums import ImportType
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_global_var_get_import_string_import_type_star(tmpdir) -> None:
    # language=typescript
    src_file = """
const foo = 1;
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"src.ts": src_file}) as codebase:
        file = codebase.get_file("src.ts")
        foo_global_var = file.get_symbol("foo")
        import_string = foo_global_var.get_import_string(import_type=ImportType.WILDCARD)
        assert import_string == "import * as src from 'src';"
