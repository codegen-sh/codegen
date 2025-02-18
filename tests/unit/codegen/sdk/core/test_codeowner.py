from unittest.mock import MagicMock

import pytest

from codegen.sdk.core.codeowner import CodeOwner


# Dummy file objects used for testing CodeOwner.
@pytest.fixture
def fake_files() -> list[MagicMock]:
    file1 = MagicMock()
    file1.owners = ["alice", "bob"]

    file2 = MagicMock()
    file2.owners = ["charlie"]

    file3 = MagicMock()
    file3.owners = ["alice"]

    return [file1, file2, file3]


def test_files_generator_returns_correct_files(fake_files):
    def file_source(*args, **kwargs):
        return fake_files

    codeowner = CodeOwner(file_source, "USERNAME", "alice")
    files = list(codeowner.files_generator())
    # file1 and file3 contain "alice" as one of their owners.
    assert fake_files[0] in files
    assert fake_files[2] in files
    assert fake_files[1] not in files


def test_files_property(fake_files):
    def file_source(*args, **kwargs):
        return fake_files

    codeowner = CodeOwner(file_source, "USERNAME", "alice")
    files = list(codeowner.files)
    # file1 and file3 contain "alice" as one of their owners.
    assert fake_files[0] in files
    assert fake_files[2] in files
    assert fake_files[1] not in files

    assert files == list(codeowner.files())


def test_name_property_and_repr():
    def dummy_source(*args, **kwargs):
        return []

    codeowner = CodeOwner(dummy_source, "TEAM", "dev_team")
    assert codeowner.name == "dev_team"
    rep = repr(codeowner)
    assert "TEAM" in rep and "dev_team" in rep


def test_iter_method(fake_files):
    def file_source(*args, **kwargs):
        return fake_files

    codeowner = CodeOwner(file_source, "USERNAME", "charlie")
    iterated_files = list(codeowner)
    assert iterated_files == [fake_files[1]]


def test_from_parser_method(fake_files):
    # Create a fake parser with a paths attribute.
    fake_parser = MagicMock()
    fake_parser.paths = [
        ("pattern1", "ignored", [("USERNAME", "alice"), ("TEAM", "devs")], "ignored", "ignored"),
        ("pattern2", "ignored", [("EMAIL", "bob@example.com")], "ignored", "ignored"),
    ]

    def file_source(*args, **kwargs):
        return fake_files

    codeowners = CodeOwner.from_parser(fake_parser, file_source)
    assert len(codeowners) == 3
    owner_values = [co.owner_value for co in codeowners]
    assert "alice" in owner_values
    assert "devs" in owner_values
    assert "bob@example.com" in owner_values
