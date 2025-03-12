from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_set_import_symbol_alias_updates_source(tmpdir) -> None:
    """The alias, NOT the name"""
    # =====[ Simple ]=====
    # language=typescript
    content = """
import a from 'b';  // test one
import { d } from 'b/c';  // test two
import { h as g, j as i } from 'd/f';  // test three
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")

        # =====[ Rename a ]=====
        imp = file.get_import("a")
        imp.set_import_symbol_alias("z")

    imp = file.get_import("z")
    assert "import z from 'b';  // test one" in file.content
    assert imp.alias.source == "z"
    assert imp.symbol_name.source == "z"
    file.commit()

    # =====[ Rename b/c ]=====
    imp = file.get_import("d")
    imp.set_import_symbol_alias("ABC")
    codebase.ctx.commit_transactions()
    imp = file.get_import("ABC")
    assert "import { ABC } from 'b/c';  // test two" in file.content
    assert imp.alias.source == "ABC"
    assert imp.symbol_name.source == "ABC"
    file.commit()

    # =====[ Rename d/f ]=====
    imp = file.get_import("g")
    imp.set_import_symbol_alias("XYZ")
    codebase.ctx.commit_transactions()
    imp = file.get_import("XYZ")
    assert "import { h as XYZ, j as i } from 'd/f';  // test three" in file.content
    assert imp.symbol_name.source == "h"
    assert imp.alias.source == "XYZ"
