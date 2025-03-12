import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.codebase import Codebase
from codegen.shared.enums.programming_language import ProgrammingLanguage


@pytest.fixture
def original(request):
    return request.param


@pytest.fixture
def expected(request):
    return request.param


@pytest.fixture
def programming_language(request):
    return request.param


@pytest.fixture
def codebase(tmp_path, original: dict[str, str], programming_language: ProgrammingLanguage = ProgrammingLanguage.PYTHON):
    with get_codebase_session(files=original, programming_language=programming_language, tmpdir=tmp_path) as codebase:
        yield codebase


@pytest.fixture
def assert_expected(expected: dict[str, str], tmp_path):
    def assert_expected(codebase: Codebase, check_codebase: bool = True) -> None:
        if check_codebase:
            codebase.commit()
        for file in expected:
            assert tmp_path.joinpath(file).exists()
            assert tmp_path.joinpath(file).read_text() == expected[file]
            if check_codebase:
                assert codebase.get_file(file).content.strip() == expected[file].strip()
        if check_codebase:
            for file in codebase.files:
                if file.file.path.exists():
                    assert file.filepath in expected

    return assert_expected
