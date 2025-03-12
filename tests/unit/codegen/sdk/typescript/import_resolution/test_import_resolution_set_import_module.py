from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_set_import_module_updates_source(tmpdir) -> None:
    """Should update just the module part"""
    # =====[ Simple ]=====
    # language=typescript
    content = """
    import a from 'b';  // test one
    import { d } from 'b/c';  // test two
    import { h as g, j as i } from 'd/f';  // test three
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as codebase:
        file = codebase.get_file("test.ts")

        # =====[ Rename a ]=====
        file.get_import("a").set_import_module("z")
        codebase.ctx.commit_transactions()

    assert "    import a from 'z';  // test one" in file.content
    assert file.get_import("a").module.source == "'z'"

    # =====[ Rename b/c ]=====
    file.get_import("d").set_import_module("x/y/z")
    codebase.ctx.commit_transactions()
    assert "    import { d } from 'x/y/z';  // test two" in file.content
    assert file.get_import("d").module.source == "'x/y/z'"

    # =====[ Rename d/f ]=====
    file.get_import("g").set_import_module('"x/y/z"')
    codebase.ctx.commit_transactions()
    assert '    import { h as g, j as i } from "x/y/z";  // test three' in file.content
    assert file.get_import("g").module.source == '"x/y/z"'


def test_set_import_module_quote_handling(tmpdir) -> None:
    """Should handle quotes in import paths correctly according to TypeScript standards:
    - Use single quotes by default (TypeScript standard)
    - Fall back to double quotes if path contains single quotes
    - Preserve existing quotes if path is already quoted
    """
    # language=typescript
    content = """
    import normal from "standard/path";  // should convert to single quotes
    import singleQuote from "path/don't/break";  // should use double quotes
    import alreadyQuoted from 'already/quoted/path';  // should preserve quotes
    import doubleQuoted from "double/quoted/path";  // should convert to single quotes
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as codebase:
        file = codebase.get_file("test.ts")

        # Test 1: Normal path should use single quotes (TypeScript standard)
        file.get_import("normal").set_import_module("new/standard/path")
        codebase.ctx.commit_transactions()
        assert "import normal from 'new/standard/path';  // should convert to single quotes" in file.content
        assert file.get_import("normal").module.source == "'new/standard/path'"

        # Test 2: Path with single quote should use double quotes
        file.get_import("singleQuote").set_import_module("new/don't/break/path")
        codebase.ctx.commit_transactions()
        assert 'import singleQuote from "new/don\'t/break/path";  // should use double quotes' in file.content
        assert file.get_import("singleQuote").module.source == '"new/don\'t/break/path"'

        # Test 3: Already quoted path (single quotes) should work
        file.get_import("alreadyQuoted").set_import_module("'new/quoted/path'")
        codebase.ctx.commit_transactions()
        assert "import alreadyQuoted from 'new/quoted/path';  // should preserve quotes" in file.content
        assert file.get_import("alreadyQuoted").module.source == "'new/quoted/path'"

        # Test 4: Already quoted path (double quotes) should work
        file.get_import("doubleQuoted").set_import_module('"another/quoted/path"')
        codebase.ctx.commit_transactions()
        assert '    import doubleQuoted from "another/quoted/path";  // should convert to single quotes' in file.content
        assert file.get_import("doubleQuoted").module.source == '"another/quoted/path"'
