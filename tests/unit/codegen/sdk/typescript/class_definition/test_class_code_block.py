from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_class_definition_code_block_returns_non_empty(tmpdir) -> None:
    FILENAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
class Foo {
    constructor() {
        if (true) {
            return 1;
        }
        else {
            return 2;
        }
    }
}
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={FILENAME: FILE_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        foo = file.get_symbol("Foo")

        assert foo.code_block
