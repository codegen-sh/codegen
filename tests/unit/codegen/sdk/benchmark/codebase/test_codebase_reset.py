from pathlib import Path

import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.codebase import Codebase
from codegen.shared.enums.programming_language import ProgrammingLanguage


def generate_files(num_files: int, extension: str = "py") -> dict[str, str]:
    return {f"file{i}.{extension}": f"# comment {i}" for i in range(num_files)}


NUM_FILES = 1000


def setup_codebase(num_files: int, extension: str, tmp_path: Path):
    files = generate_files(num_files, extension)
    with get_codebase_session(files=files, programming_language=ProgrammingLanguage.PYTHON, tmpdir=Path(tmp_path), sync_graph=False) as codebase:
        for file in files:
            codebase.get_file(file).edit(f"# comment2 {file}")
    return codebase, files


def reset_codebase(codebase: Codebase):
    codebase.reset()


@pytest.mark.benchmark(group="sdk-benchmark", min_time=1, max_time=5, disable_gc=True)
@pytest.mark.parametrize("extension", ["txt", "py"])
def test_codebase_reset_stress_test(extension: str, tmp_path, benchmark):
    def setup():
        codebase, _ = setup_codebase(NUM_FILES, extension, tmp_path)
        return ((codebase,), {})

    benchmark.pedantic(reset_codebase, setup=setup)


@pytest.mark.skip("Skipping this test for now")
@pytest.mark.timeout(5, func_only=True)
@pytest.mark.skip(reason="Test is timing out and needs investigation")  # Skip this test for now
@pytest.mark.parametrize("extension", ["txt", "py"])
def test_codebase_reset_correctness(extension: str, tmp_path):
    codebase, files = setup_codebase(NUM_FILES, extension, tmp_path)
    codebase.reset()
    for file, original_content in files.items():
        assert (tmp_path / file).exists()
        assert (tmp_path / file).read_text() == original_content
