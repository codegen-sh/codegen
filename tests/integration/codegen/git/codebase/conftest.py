import os

import pytest

from codegen.sdk.core.codebase import Codebase


@pytest.fixture
def codebase(tmpdir):
    os.chdir(tmpdir)
    codebase = Codebase.from_repo(repo_full_name="codegen-sh/Kevin-s-Adventure-Game", tmp_dir=tmpdir, language="python")
    yield codebase
