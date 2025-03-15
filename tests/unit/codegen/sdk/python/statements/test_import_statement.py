from codegen.sdk.codebase.factory.get_session import get_codebase_session


def test_import_statements(tmpdir) -> None:
    # language=python
    content = """
import module1
from package1.module2 import function1, function2
from package2.module3 import Class1
from package3 import Class2 as Alias
"""
    with get_codebase_session(tmpdir=tmpdir, files={"file.py": content}) as codebase:
        file = codebase.get_file("file.py")
        assert len(file.import_statements) == 4
        assert len(file.import_statements[0].imports) == 1
        assert len(file.import_statements[1].imports) == 2
        assert len(file.import_statements[2].imports) == 1
        assert len(file.import_statements[3].imports) == 1


def test_remove_imports(tmpdir) -> None:
    # language=python
    content = """
import module1
from package1.module2 import function1, function2
from package2.module3 import Class1
from package3 import Class2 as Alias
"""
    with get_codebase_session(tmpdir=tmpdir, files={"file.py": content}) as codebase:
        file = codebase.get_file("file.py")
        import_stmt = file.import_statements[1]  # Get statement with multiple imports
        assert len(import_stmt.imports) == 2

        # Remove all imports
        import_stmt.imports.clear()
    assert (
        file.content.strip()
        == """
import module1
from package2.module3 import Class1
from package3 import Class2 as Alias
""".strip()
    )


def test_remove_single_import(tmpdir) -> None:
    # language=python
    content = """
import module1
from package1.module2 import function1, function2
from package2.module3 import Class1
from package3 import Class2 as Alias
"""
    with get_codebase_session(tmpdir=tmpdir, files={"file.py": content}) as codebase:
        file = codebase.get_file("file.py")
        import_stmt = file.import_statements[1]  # Get statement with multiple imports

        # Remove single import
        import_stmt.imports[0].remove()

    assert (
        file.content.strip()
        == """
import module1
from package1.module2 import function2
from package2.module3 import Class1
from package3 import Class2 as Alias
""".strip()
    )


def test_remove_multiline_imports(tmpdir) -> None:
    # language=python
    content = """
from package1.module1 import (
    function1,
    function2,
    function3,
    function4
)
from package2 import module1
"""
    with get_codebase_session(tmpdir=tmpdir, files={"file.py": content}) as codebase:
        file = codebase.get_file("file.py")
        import_stmt = file.import_statements[0]

        # Remove two imports
        import_stmt.imports[1].remove()
        import_stmt.imports[2].remove()

    assert (
        file.content.strip()
        == """
from package1.module1 import (
    function1,
    function4
)
from package2 import module1
""".strip()
    )


def test_remove_entire_multiline_import(tmpdir) -> None:
    # language=python
    content = """
from package1.module1 import (
    function1,
    function2,
    function3
)
from package2 import module1
"""
    with get_codebase_session(tmpdir=tmpdir, files={"file.py": content}) as codebase:
        file = codebase.get_file("file.py")
        import_stmt = file.import_statements[0]

        # Remove entire import statement
        import_stmt.remove()

    assert (
        file.content.strip()
        == """
from package2 import module1
""".strip()
    )
