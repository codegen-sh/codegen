from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_rename_import_updates_source(tmpdir) -> None:
    """NOT the alias, just the name"""
    # =====[ Simple ]=====
    # language=typescript
    content = """
import a from 'b';  // test one
import { d } from 'b/c';  // test two
import { h as g, j as i } from 'd/f';  // test three
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test_update_import_name.ts": content}) as codebase:
        file = codebase.get_file("test_update_import_name.ts")

        # =====[ Rename d/f ]=====
        imp = file.get_import("g")
        imp.rename("XYZ")

    imp = file.get_import("g")
    assert "import { XYZ as g, j as i } from 'd/f';  // test three" in file.content
    assert imp.symbol_name.source == "XYZ"

    # =====[ Rename b/c ]=====
    imp = file.get_import("d")
    imp.rename("ABC")
    codebase.ctx.commit_transactions()
    imp = file.get_import("d")
    assert "import { ABC } from 'b/c';  // test two" in file.content
    assert file.get_import("ABC").symbol_name.source == "ABC"

    # =====[ Rename a ]=====
    imp = file.get_import("a")
    imp.rename("z")
    codebase.ctx.commit_transactions()
    assert "import z from 'b';  // test one" in file.content
    assert file.get_import("z").symbol_name.source == "z"
