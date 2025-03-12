from codegen.sdk.codebase.factory.get_session import get_codebase_session


def test_update_import_module(tmpdir) -> None:
    """Should update just the module part"""
    # =====[ Simple ]=====
    # language=python
    content = """
import a  # test one
from b.c import d  # test two
from d.f import (g as h, i as j)  # test three
from m import m  # test four
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")

        # =====[ Rename a ]=====
        imp = file.get_import("a")
        imp.set_import_module("z")

    assert "import z  # test one" in file.content
    assert file.get_import("z").module.source == "z"

    # =====[ Rename b.c ]=====
    imp = file.get_import("d")
    imp.set_import_module("x.y.z")
    codebase.ctx.commit_transactions()
    assert "from x.y.z import d  # test two" in file.content
    assert file.get_import("d").module.source == "x.y.z"

    # =====[ Rename d.f ]=====
    imp = file.get_import("h")
    imp.set_import_module("x.y.z")
    codebase.ctx.commit_transactions()
    assert "from x.y.z import (g as h, i as j)  # test three" in file.content
    assert file.get_import("h").module.source == "x.y.z"

    # ===== [ Rename m ]=====
    imp = file.get_import("m")
    imp.set_import_module("z")
    codebase.ctx.commit_transactions()
    assert "from z import m  # test four" in file.content
    assert file.get_import("m").module.source == "z"
