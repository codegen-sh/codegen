from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_file_import_statements_includes_require_statements(tmpdir) -> None:
    file = "test.js"
    # language=typescript
    content = """
    const pkg1 = require('package1');
    const router = pkg1.Router();
    import ImportedModule from './module'
    const { import1, import2 } = require('./package2');
    const pkg3 = require('./package3');

    router.get('/path', import1, pkg3.method);

    module.exports = router;
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={file: content}) as codebase:
        file = codebase.get_file(file)
        assert len(file.import_statements) == 4
        assert len(file.imports) == 5
        assert len(file.import_statements[1].imports) == 1
        assert len(file.import_statements[2].imports) == 2


def test_file_import_statements_and_imports(tmpdir) -> None:
    file = "test.ts"
    # language=typescript
    content = """
import { Type1, Type2, Type3 } from "package";
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={file: content}) as codebase:
        file = codebase.get_file(file)
        assert file.has_import("Type2")
        assert [x.name for x in file.imports] == ["Type1", "Type2", "Type3"]
        names = [x.imported_symbol.name for x in file.imports]
        assert "Type1" in names
        assert "Type2" in names
        assert "Type3" in names


def test_file_import_statements_require_statements_binary_expressions(tmpdir) -> None:
    file = "test.js"
    # language=typescript
    content = """
    const pkg = fallback || require('package');
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={file: content}) as codebase:
        file = codebase.get_file(file)
        assert len(file.import_statements) == 1
        assert len(file.imports) == 1
        assert len(file.import_statements[0].imports) == 1
        assert file.imports[0].imported_symbol.name == "pkg"
        assert file.imports[0].name == "pkg"


def test_file_import_statements_require_statements_ternary_expressions(tmpdir) -> None:
    file = "test.js"
    # language=typescript
    content = """
    const pkg = condition ? require('package') : fallback;
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={file: content}) as codebase:
        file = codebase.get_file(file)
        assert len(file.import_statements) == 1
        assert len(file.imports) == 1
        assert len(file.import_statements[0].imports) == 1
        assert file.imports[0].imported_symbol.name == "pkg"
        assert file.imports[0].name == "pkg"
