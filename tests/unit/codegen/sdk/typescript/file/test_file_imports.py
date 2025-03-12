from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_file_imports_default_import(tmpdir) -> None:
    file = """
import a from './some_file.js';
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")
        imports = file.imports
        assert len(imports) == 1
        assert imports[0].symbol_name.source == "a"
        assert imports[0].alias.source == "a"
        assert imports[0].module.source == "'./some_file.js'"


def test_file_imports_named_import(tmpdir) -> None:
    file = """
import { b, c } from './some_other_file.js';
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")
        imports = file.imports
        assert len(imports) == 2
        assert imports[0].symbol_name.source == "b"
        assert imports[0].alias.source == "b"
        assert imports[0].module.source == "'./some_other_file.js'"
        assert imports[1].symbol_name.source == "c"
        assert imports[1].alias.source == "c"
        assert imports[1].module.source == "'./some_other_file.js'"


def test_file_imports_exports(tmpdir) -> None:
    file = """
export {a, b} from './some_random_file.js'
    """
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")
        exports = file.imports  # TODO: shouldn't this be called export?
        assert len(exports) == 2
        assert exports[0].symbol_name.source == "a"
        assert exports[0].alias.source == "a"
        assert exports[0].module.source == "'./some_random_file.js'"
        assert exports[1].symbol_name.source == "b"
        assert exports[1].alias.source == "b"
        assert exports[1].module.source == "'./some_random_file.js'"


def test_file_imports_aliased_import(tmpdir) -> None:
    file = """
import { a as b } from './some_file.js';
        """
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")
        imports = file.imports
        assert len(imports) == 1
        assert imports[0].symbol_name.source == "a"
        assert imports[0].alias.source == "b"
        assert imports[0].name == "b"
        assert imports[0].module.source == "'./some_file.js'"


def test_file_imports_aliased_exports(tmpdir) -> None:
    file = """
export { a as b } from './some_file.js';
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")
        exports = file.imports
        assert len(exports) == 1
        assert exports[0].symbol_name.source == "a"
        assert exports[0].alias.source == "b"
        assert exports[0].name == "b"
        assert exports[0].module.source == "'./some_file.js'"


def test_file_imports_namespace_import(tmpdir) -> None:
    file = """
import * as React from 'react';
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")
        exports = file.imports
        assert exports[0].symbol_name.source == "* as React"
        assert exports[0].alias.source == "React"
        assert exports[0].name == "React"
        assert exports[0].module.source == "'react'"


def test_file_imports_namespace_export(tmpdir) -> None:
    file = """
export * as React from 'react';
"""
    # TODO: @edward @edo is this correct?
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")
        exports = file.imports
        assert len(exports) == 1
        assert exports[0].symbol_name.source == "* as React"
        assert exports[0].alias.source == "React"
        assert exports[0].name == "React"
        assert exports[0].module.source == "'react'"


def test_file_imports_require_statements(tmpdir) -> None:
    file = """
const pkg1 = require('package1');
const router = pkg1.Router();

const { import1, import2 } = require('./package2');
const pkg3 = require('./package3');

router.get('/path', import1, pkg3.method);

module.exports = router;
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")
        assert "router" not in [x.name for x in file.imports]
        assert "pkg1" in [x.name for x in file.imports]
        assert "pkg3" in [x.name for x in file.imports]
        assert "import1" in [x.name for x in file.imports]
        assert "import2" in [x.name for x in file.imports]


def test_file_imports_dynamic_imports(tmpdir) -> None:
    file = """
const module1 = import('package1').then(module => module.default)
const module2 = await import('package2')
const { import1 } = await import('package3')
const { import2, import3, import4 } = await import(
    'package4'
)
const module3 = await import('package5').then(
    module => module.default,
)
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")
        assert "module2" in [x.name for x in file.imports]
        assert "import1" in [x.name for x in file.imports]
        assert "import2" in [x.name for x in file.imports]
        assert "import3" in [x.name for x in file.imports]
        assert "import4" in [x.name for x in file.imports]
        # TODO: fix dynamic import parsing (CG-8722)
        # assert "module3" in [x.name for x in file.imports]
        assert "module1" in [x.name for x in file.imports]
