import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_file_add_symbol_import_updates_source(tmpdir) -> None:
    # language=python
    content1 = """
import datetime

def foo():
    return datetime.datetime.now()
"""

    # language=python
    content2 = """
def bar():
    return 1
"""
    with get_codebase_session(tmpdir=tmpdir, files={"file1.py": content1, "file2.py": content2}) as codebase:
        file1 = codebase.get_file("file1.py")
        file2 = codebase.get_file("file2.py")

        file2.add_import(file1.get_symbol("foo"))

    assert "import foo" in file2.content


def test_file_add_import_string_no_imports_adds_to_top(tmpdir) -> None:
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


def test_file_add_import_string_adds_before_first_import(tmpdir) -> None:
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
def test_file_add_import_string_adds_remove(tmpdir, sync) -> None:
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


def test_file_add_import_typescript_string_adds_before_first_import(tmpdir) -> None:
    # language=typescript
    content = """
// top level comment

// existing imports below
import { Something } from 'somewhere'

function bar(): number {
    return 1;
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as codebase:
        file = codebase.get_file("test.ts")

        file.add_import("import { NewThing } from 'elsewhere'")

    file_lines = file.content.split("\n")
    assert "import { NewThing } from 'elsewhere'" in file_lines
    assert file_lines.index("import { NewThing } from 'elsewhere'") < file_lines.index("import { Something } from 'somewhere'")


def test_file_add_import_typescript_string_no_imports_adds_to_top(tmpdir) -> None:
    # language=typescript
    content = """
    function bar(): number {
        return 1;
    }
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as codebase:
        file = codebase.get_file("test.ts")

        file.add_import("import { Something } from 'somewhere';")

    file_lines = file.content.split("\n")
    assert "import { Something } from 'somewhere';" in file_lines[0]


def test_file_add_import_typescript_multiple_symbols(tmpdir) -> None:
    FILE1_FILENAME = "file1.ts"
    FILE2_FILENAME = "file2.ts"

    # language=typescript
    FILE1_CONTENT = """
    export function foo(): string {
        return 'foo';
    }

    export function bar(): string {
        return 'bar';
    }
    """

    # language=typescript
    FILE2_CONTENT = """
    function test(): number {
        return 1;
    }
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE1_FILENAME: FILE1_CONTENT, FILE2_FILENAME: FILE2_CONTENT}) as codebase:
        file1 = codebase.get_file(FILE1_FILENAME)
        file2 = codebase.get_file(FILE2_FILENAME)

        # Add multiple symbols one after another
        file2.add_import(file1.get_symbol("foo"))
        file2.add_import(file1.get_symbol("bar"))

    # Updated assertion to check for separate imports since that's the current behavior
    assert "import { foo } from 'file1';" in file2.content
    assert "import { bar } from 'file1';" in file2.content


def test_file_add_import_typescript_default_import(tmpdir) -> None:
    # language=typescript
    content = """
    function bar(): number {
        return 1;
    }
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as codebase:
        file = codebase.get_file("test.ts")

        file.add_import("import React from 'react';")
        file.add_import("import { useState } from 'react';")

    file_lines = file.content.split("\n")
    assert "import React from 'react';" in file_lines
    assert "import { useState } from 'react';" in file_lines


def test_file_add_import_typescript_duplicate_prevention(tmpdir) -> None:
    FILE1_FILENAME = "file1.ts"
    FILE2_FILENAME = "file2.ts"

    # language=typescript
    FILE1_CONTENT = """
    export function foo(): string {
        return 'foo';
    }
    """

    # language=typescript
    FILE2_CONTENT = """
    import { foo } from 'file1';

    function test(): string {
        return foo();
    }
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE1_FILENAME: FILE1_CONTENT, FILE2_FILENAME: FILE2_CONTENT}) as codebase:
        file1 = codebase.get_file(FILE1_FILENAME)
        file2 = codebase.get_file(FILE2_FILENAME)

        # Try to add the same import again
        file2.add_import(file1.get_symbol("foo"))

    # Verify no duplicate import was added
    assert file2.content.count("import { foo }") == 1


def test_file_add_import_string_adds_after_future(tmpdir) -> None:
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


def test_file_add_import_string_adds_after_last_future(tmpdir) -> None:
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


def test_file_add_import_string_adds_after_future_before_non_future(tmpdir) -> None:
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


def test_file_add_import_string_future_import_adds_to_top(tmpdir) -> None:
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
