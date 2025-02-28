import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_session


def test_file_add_symbol_import_from_string_adds_after_future(tmpdir) -> None:
    # language=python
    content = """
from __future__ import annotations

def foo():
    print("this is foo")
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")

        file.add_import("from sqlalchemy.orm import Session")

    file_lines = file.content.split("\n")
    assert "from __future__ import annotations" in file_lines[1]
    assert "from sqlalchemy.orm import Session" in file_lines[2]


def test_file_add_symbol_import_from_string_adds_after_last_future(tmpdir) -> None:
    # language=python
    content = """
from __future__ import annotations
from __future__ import division

def foo():
    print("this is foo")
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")

        file.add_import("from sqlalchemy.orm import Session")

    file_lines = file.content.split("\n")
    assert "from __future__ import annotations" in file_lines[1]
    assert "from __future__ import division" in file_lines[2]
    assert "from sqlalchemy.orm import Session" in file_lines[3]


def test_file_add_symbol_import_from_string_adds_after_future_before_non_future(tmpdir) -> None:
    # language=python
    content = """
from __future__ import annotations
from typing import List

def foo():
    print("this is foo")
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")

        file.add_import("from sqlalchemy.orm import Session")

    file_lines = file.content.split("\n")
    assert "from __future__ import annotations" in file_lines[1]
    assert "from sqlalchemy.orm import Session" in file_lines[2]
    assert "from typing import List" in file_lines[3]


def test_file_add_symbol_import_from_string_future_import_adds_to_top(tmpdir) -> None:
    # language=python
    content = """
from __future__ import annotations

def foo():
    print("this is foo")
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")

        file.add_import("from __future__ import division")

    file_lines = file.content.split("\n")
    assert "from __future__ import division" in file_lines[1]
    assert "from __future__ import annotations" in file_lines[2]


def test_file_add_symbol_import_from_string_no_imports_adds_to_top(tmpdir) -> None:
    # language=python
    content = """
def foo():
    print("this is foo")
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")

        file.add_import("from sqlalchemy.orm import Session")

    file_lines = file.content.split("\n")
    assert "from sqlalchemy.orm import Session" in file_lines[0]


def test_file_add_symbol_import_from_string_adds_before_first_import(tmpdir) -> None:
    # language=python
    content = """
# top level comment

# adds new import here
from typing import List

def foo():
    print("this is foo")
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")

        file.add_import("from sqlalchemy.orm import Session")

    file_lines = file.content.split("\n")
    assert "from sqlalchemy.orm import Session" in file_lines
    assert file_lines.index("from sqlalchemy.orm import Session") == file_lines.index("from typing import List") - 1


@pytest.mark.parametrize("sync", [True, False])
def test_file_add_symbol_import_from_string_adds_remove(tmpdir, sync) -> None:
    # language=python
    content = """import b

def foo():
    print("this is foo")
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content.strip()}, sync_graph=sync) as codebase:
        file = codebase.get_file("test.py")

        file.add_import("import antigravity")
        file.remove()
    if sync:
        assert not codebase.get_file(file.filepath, optional=True)
