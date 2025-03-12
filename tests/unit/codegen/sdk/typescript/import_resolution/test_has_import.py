from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_import_rename_usage_with_alias(tmpdir) -> None:
    # language=typescript
    content1 = """
import foo2 from 'b';
import * as f2 from 'b/c';
import { bar1 as bar2 } from 'd/f';
import bar from 'd/f';
"""
    with get_codebase_session(tmpdir=tmpdir, files={"file1.ts": content1}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file1.ts")
        assert file.has_import("foo2")
        assert file.has_import("f2")
        assert file.has_import("bar")
        assert file.has_import("bar2")
        assert not file.has_import("foo3")


def test_has_import_with_comment(tmpdir) -> None:
    # language=typescript
    content1 = """
import type {
    A,
    B,
    C,
    D,
    // Some comment
    E,
} from "some/module";
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file1.ts": content1}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file1.ts")
        imports = file.imports
        assert not file.has_import("TEST")
        assert file.has_import("A")
        assert len(imports) == 5
        assert all(x.alias for x in imports)
