from pathlib import Path
from typing import TypeVar

import pytest
from pytest_snapshot.plugin import Snapshot

from codegen.sdk.core.codebase import Codebase
from codemods.codemod import Codemod
from tests.shared.codemod.codebase_comparison_utils import compare_codebase_diff
from tests.shared.codemod.models import BASE_PATH

DIFF_ROOT = BASE_PATH / ".diffs"
T = TypeVar("T")


@pytest.mark.timeout(120, func_only=True)
def test_codemods_cloned_repos(codemod: Codemod, codebase: Codebase, expected: Path, tmp_path: Path, diff_folder: Path, snapshot: Snapshot) -> None:
    codemod.execute(codebase)
    codebase.commit(codebase.ctx.config.codebase.verify_graph)
    compare_codebase_diff(codebase=codebase, expected_dir=tmp_path, expected_diff=expected, diff_path=diff_folder, snapshot=snapshot)
    if codebase.ctx.config.codebase.verify_graph:
        codebase.reset()
