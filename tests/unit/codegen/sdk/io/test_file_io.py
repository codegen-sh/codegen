import pytest

from codegen.sdk.codebase.io.file_io import BadWriteError, FileIO


@pytest.fixture
def file_io():
    return FileIO()


def test_write_and_read_bytes(file_io, tmp_path):
    test_file = tmp_path / "test.txt"
    content = b"test content"

    file_io.write_bytes(test_file, content)
    assert file_io.read_bytes(test_file) == content
    assert not test_file.exists()


def test_read_bytes_nonexistent_file(file_io, tmp_path):
    test_file = tmp_path / "test.txt"
    test_content = b"test content"

    # Create a real file
    test_file.write_bytes(test_content)

    # Reading should load from disk
    assert file_io.read_bytes(test_file) == test_content


def test_save_file(file_io, tmp_path):
    test_file = tmp_path / "test.txt"
    content = b"test content"

    file_io.write_bytes(test_file, content)
    file_io.save_files({test_file})

    assert test_file.exists()
    assert test_file.read_bytes() == content


def test_check_changes_with_pending_changes(file_io, tmp_path, caplog):
    test_file = tmp_path / "test.txt"
    file_io.write_bytes(test_file, b"test content")

    file_io.check_changes()

    assert "Directly called file write without calling commit_transactions" in caplog.text


def test_check_changes_no_pending_changes(file_io):
    file_io.check_changes()  # Should not raise any exception


def test_delete_file(file_io, tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_bytes(b"test content")

    file_io.read_bytes(test_file)  # Load into memory
    file_io.delete_file(test_file)

    assert not test_file.exists()
    assert test_file not in file_io.files


def test_read_and_write_bounded(file_io, tmp_path):
    allowed_dir = tmp_path / "allowed"
    file_io.allowed_paths = [allowed_dir]

    allowed_file = allowed_dir / "test.txt"
    content = b"test content"

    file_io.write_bytes(allowed_file, content)
    assert file_io.read_bytes(allowed_file) == content

    with pytest.raises(BadWriteError) as exc_info:
        bad_file = tmp_path / "test.txt"
        file_io.write_bytes(bad_file, content)

    assert "is not within allowed paths" in str(exc_info.value)

    with pytest.raises(BadWriteError) as exc_info:
        bad_file_2 = allowed_dir / ".." / "test2.txt"
        file_io.write_bytes(bad_file_2, content)

    assert "is not within allowed paths" in str(exc_info.value)


def test_read_bounded(file_io, tmp_path):
    allowed_dir = tmp_path / "allowed"
    allowed_dir.mkdir(exist_ok=True)
    file_io.allowed_paths = [allowed_dir]

    allowed_file = allowed_dir / "test.txt"
    content = b"test content"
    allowed_file.write_bytes(content)

    assert file_io.read_bytes(allowed_file) == content

    with pytest.raises(BadWriteError) as exc_info:
        bad_file = tmp_path / "test.txt"
        bad_file.write_bytes(content)
        file_io.read_bytes(bad_file)

    assert "is not within allowed paths" in str(exc_info.value)

    with pytest.raises(BadWriteError) as exc_info:
        bad_file_2 = allowed_dir / ".." / "test2.txt"
        bad_file_2.write_bytes(content)
        file_io.read_bytes(bad_file_2)

    assert "is not within allowed paths" in str(exc_info.value)


def test_delete_file_bounded(file_io, tmp_path):
    allowed_dir = tmp_path / "allowed"
    allowed_dir.mkdir(exist_ok=True)
    file_io.allowed_paths = [allowed_dir]

    allowed_file = allowed_dir / "test.txt"
    allowed_file.write_bytes(b"test content")

    file_io.delete_file(allowed_file)

    with pytest.raises(BadWriteError) as exc_info:
        bad_file = tmp_path / "test.txt"
        bad_file.write_bytes(b"test content")
        file_io.delete_file(bad_file)

    assert "is not within allowed paths" in str(exc_info.value)

    with pytest.raises(BadWriteError) as exc_info:
        bad_file_2 = allowed_dir / ".." / "test2.txt"
        bad_file_2.write_bytes(b"test content")
        file_io.delete_file(bad_file_2)

    assert "is not within allowed paths" in str(exc_info.value)


def test_file_exists_bounded(file_io, tmp_path):
    allowed_dir = tmp_path / "allowed"
    allowed_dir.mkdir(exist_ok=True)
    file_io.allowed_paths = [allowed_dir]

    allowed_file = allowed_dir / "test.txt"
    allowed_file.write_bytes(b"test content")

    assert file_io.file_exists(allowed_file)

    with pytest.raises(BadWriteError) as exc_info:
        bad_file = tmp_path / "test.txt"
        bad_file.write_bytes(b"test content")
        file_io.file_exists(bad_file)

    assert "is not within allowed paths" in str(exc_info.value)

    with pytest.raises(BadWriteError) as exc_info:
        bad_file_2 = allowed_dir / ".." / "test2.txt"
        bad_file_2.write_bytes(b"test content")
        file_io.file_exists(bad_file_2)

    assert "is not within allowed paths" in str(exc_info.value)
