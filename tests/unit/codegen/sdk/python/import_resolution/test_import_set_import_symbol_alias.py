from codegen.sdk.codebase.factory.get_session import get_codebase_session


def test_import_set_import_symbol_alias_from_no_alias(tmpdir) -> None:
    # language=python
    content = """
from my_utils import fb as foo_bar
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        imp = file.get_import("foo_bar")
        imp.set_import_symbol_alias("XYZ")

    # language=python
    assert """from my_utils import fb as XYZ""" in imp.to_file.content


def test_import_set_import_symbol_alias_from_existing_alias(tmpdir) -> None:
    """The alias, NOT the name"""
    # =====[ Simple ]=====
    # language=python
    content = """
import a  # test one
from b.c import d  # test two
from d.f import (g as h, i as j)  # test three
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")

        # =====[ Rename a ]=====
        imp = file.get_import("a")
        imp.set_import_symbol_alias("z")
        file.commit()
        file = imp.to_file
        imp = file.get_import("z")
        assert "import z  # test one" in file.content
        assert imp.alias.source == "z"
        assert imp.symbol_name.source == "z"
        assert imp.module.source == "z"
        file.commit()
        # =====[ Rename b.c ]=====
        imp = file.get_import("d")
        imp.set_import_symbol_alias("ABC")
        file = imp.to_file
        codebase.ctx.commit_transactions()
        imp = file.get_import("ABC")
        assert "from b.c import ABC  # test two" in file.content
        assert imp.alias.source == "ABC"
        assert imp.symbol_name.source == "ABC"
        file.commit()
        # =====[ Rename d.f ]=====
        imp = file.get_import("h")
        imp.set_import_symbol_alias("XYZ")
        file = imp.to_file
        codebase.ctx.commit_transactions()
        imp = file.get_import("XYZ")
        assert "from d.f import (g as XYZ, i as j)  # test three" in file.content
        assert imp.symbol_name.source == "g"
        assert imp.alias.source == "XYZ"
