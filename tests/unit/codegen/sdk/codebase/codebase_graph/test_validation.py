from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.codebase.validation import PostInitValidationStatus, post_init_validation
from codegen.sdk.enums import NodeType
from codegen.sdk.extensions.utils import uncache_all


def test_post_init_validation_valid_graph(tmpdir) -> None:
    with get_codebase_session(
        tmpdir=tmpdir,
        files={
            "file.py": "a = 1 + 2",
            "file2.py": "b = 1 + 2",
        },
    ) as codebase:
        assert len(codebase.files) == 2
        assert post_init_validation(codebase) == PostInitValidationStatus.SUCCESS


def test_post_init_validation_no_nodes(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir) as codebase:
        assert post_init_validation(codebase) == PostInitValidationStatus.NO_NODES


def test_post_init_validation_missing_files(tmpdir) -> None:
    with get_codebase_session(
        tmpdir=tmpdir,
        files={
            "file.py": "a = 1 + 2",
            "file2.py": "b = 1 + 2",
        },
    ) as codebase:
        assert len(codebase.files) == 2
        codebase.ctx.remove_node(codebase.files[0].node_id)
        uncache_all()  # Clear codebase.files cache
        assert post_init_validation(codebase) == PostInitValidationStatus.MISSING_FILES


def test_post_init_validation_imports_resolved(tmpdir) -> None:
    # source where only 0.125 imports will resolve
    # language=python
    bar_source = """
from foo2 import f as f2
from foo3 import f as f3
from numpy import np

def b():
    pass
"""
    # language=python
    foo_source = """
from bar import b
from bar2 import b as b2
from bar3 import b as b3
from bar4 import b as b4
from numpy import np

def f():
    pass
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        files={
            "bar.py": bar_source,
            "foo.py": foo_source,
        },
    ) as codebase:
        num_resolved_imports = len([imp for imp in codebase.imports if imp.resolved_symbol and imp.resolved_symbol.node_type != NodeType.EXTERNAL])
        assert num_resolved_imports == 1
        assert len(codebase.imports) == 8
        assert post_init_validation(codebase) == PostInitValidationStatus.LOW_IMPORT_RESOLUTION_RATE
