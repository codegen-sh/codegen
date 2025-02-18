from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_remove_import_removes_from_file_imports(tmpdir) -> None:
    # language=typescript
    content = """
import a from 'b';  // test one
import { d } from 'b/c';  // test two
import { h as g, j as i } from 'd/f';  // test three
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")

        # =====[ Remove a ]=====
        imp = file.get_import("a")
        imp_import_string = imp.get_import_string()
        assert imp_import_string == "import { a } from 'test';"
