from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_directory_imports(tmpdir) -> None:
    # language=typescript
    content1 = """
    import { a, b } from '../shared';
    import type { IFoo } from './types';
    """
    content2 = """
    import { c } from '../shared';
    import defaultExport from './module';
    """
    with get_codebase_session(
        tmpdir=tmpdir, files={"dir1/file1.ts": content1, "dir1/file2.ts": content2, "dir2/file3.ts": "import { d } from '../shared';"}, programming_language=ProgrammingLanguage.TYPESCRIPT
    ) as codebase:
        dir1 = codebase.get_directory("dir1")
        dir2 = codebase.get_directory("dir2")

        # Test dir1 imports
        assert len(dir1.imports) == 5
        dir1_import_names = {imp.name for imp in dir1.imports}
        assert dir1_import_names == {"a", "b", "IFoo", "c", "defaultExport"}

        # Test dir2 imports
        assert len(dir2.imports) == 1
        assert dir2.imports[0].name == "d"

        # Test get_import method
        assert dir1.get_import("a") is not None
        assert dir1.get_import("d") is None
        assert dir2.get_import("d") is not None


def test_directory_nested_imports(tmpdir) -> None:
    # language=typescript
    content1 = """
    import { a } from './module1';
    """
    content2 = """
    import { b } from '../module2';
    """
    content3 = """
    import { c } from '../../module3';
    """
    with get_codebase_session(
        tmpdir=tmpdir, files={"dir1/file1.ts": content1, "dir1/subdir/file2.ts": content2, "dir1/subdir/deepdir/file3.ts": content3}, programming_language=ProgrammingLanguage.TYPESCRIPT
    ) as codebase:
        dir1 = codebase.get_directory("dir1")
        subdir = codebase.get_directory("dir1/subdir")
        deepdir = codebase.get_directory("dir1/subdir/deepdir")

        # Test imports at each directory level
        assert len(dir1.imports) == 3  # Should include all nested imports
        assert len(subdir.imports) == 2  # Should include its own and deeper imports
        assert len(deepdir.imports) == 1  # Should only include its own imports
