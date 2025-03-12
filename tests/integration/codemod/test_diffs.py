import ast
import subprocess
from pathlib import Path
from typing import TypeVar

from codegen.sdk.codebase.diff_lite import DiffLite
from codegen.sdk.core.codebase import Codebase
from codegen.sdk.output.utils import stylize_error
from codegen.sdk.tree_sitter_parser import print_errors
from tests.shared.codemod.codebase_comparison_utils import gather_modified_files
from tests.shared.codemod.models import BASE_PATH

DIFF_ROOT = BASE_PATH / ".diffs"
T = TypeVar("T")


def test_codemods_diffs(_codebase: Codebase, expected: Path) -> None:
    """Verify diffs are syntactically valid"""
    verify_diffs(_codebase)
    subprocess.run(["git", "apply", str(expected.absolute())], cwd=_codebase.repo_path)
    verify_diffs(_codebase)


def verify_diffs(_codebase):
    modified = gather_modified_files(_codebase)
    diffs = [DiffLite.from_git_diff(diff) for diff in _codebase.get_diffs()]
    _codebase.ctx.apply_diffs(diffs)
    for file in _codebase.files:
        print_errors(file.filepath, file.content)
        assert not file.ts_node.has_error
    for path, content in modified.items():
        if path.suffix == ".py":
            try:
                ast.parse(content, filename=path)
            except SyntaxError as error:
                stylize_error(path, (error.lineno - 1, error.offset), (error.end_lineno - 1, error.end_offset), _codebase.get_file(path).ts_node, content, error.msg)
                raise error
        # TODO: ts support
