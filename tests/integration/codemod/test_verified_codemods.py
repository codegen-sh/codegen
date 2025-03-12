import logging
from pathlib import Path
from typing import TypeVar

import pytest
from pytest_snapshot.plugin import Snapshot

from codegen.sdk.core.codebase import Codebase
from codemods.codemod import Codemod
from tests.shared.codemod.codebase_comparison_utils import compare_codebase_diff
from tests.shared.codemod.models import BASE_PATH
from tests.shared.utils.recursion import set_recursion_limit

logger = logging.getLogger(__name__)
DIFF_ROOT = BASE_PATH / ".diffs"
T = TypeVar("T")


@pytest.mark.timeout(120, func_only=True)
def test_verified_codemods(
    verified_codemod: Codemod,
    codebase: Codebase,
    expected: Path,
    tmp_path: Path,
    diff_folder: Path,
    snapshot: Snapshot,
    monkeypatch,
) -> None:
    set_recursion_limit()
    # Patch Codebase.ai to always return "<ai-response>"
    monkeypatch.setattr(codebase, "ai", lambda *args, **kwargs: "<ai-response>")
    verified_codemod.execute(codebase)
    # Codebase logging not functioning, creating an empty file to avoid error
    codebase.create_file(".codemod_logs.txt")
    # Commit changes
    codebase.commit(codebase.ctx.config.codebase.verify_graph)
    compare_codebase_diff(
        codebase=codebase,
        expected_dir=tmp_path,
        expected_diff=expected,
        diff_path=diff_folder,
        snapshot=snapshot,
    )
