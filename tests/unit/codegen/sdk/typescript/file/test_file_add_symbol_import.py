from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_file_add_symbol_import_updates_source(tmpdir) -> None:
    FILE1_FILENAME = "file1.ts"
    FILE2_FILENAME = "file2.ts"

    # language=typescript
    FILE1_CONTENT = """
    import moment from 'moment';

    function foo(): string {
        return moment().format();
    }
    """

    # language=typescript
    FILE2_CONTENT = """
    function bar(): number {
        return 1;
    }
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE1_FILENAME: FILE1_CONTENT, FILE2_FILENAME: FILE2_CONTENT}) as codebase:
        file1 = codebase.get_file(FILE1_FILENAME)
        file2 = codebase.get_file(FILE2_FILENAME)

        file2.add_symbol_import(file1.get_symbol("foo"))

    assert "import { foo } from 'file1';" in file2.content
