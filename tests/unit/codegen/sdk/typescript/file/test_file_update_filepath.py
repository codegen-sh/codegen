import os

import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_rename_file(tmpdir) -> None:
    # language=typescript
    foo_content = """
export function foo(): number {
    return 1;
}
"""
    # language=typescript
    bar_content = """
import { foo } from 'foo_file';

function bar(): number {
    return foo();
}
"""
    foo_filepath = "foo_file.ts"
    bar_filepath = "bar_file.ts"
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={
            foo_filepath: foo_content,
            bar_filepath: bar_content,
        },
        commit=True,
    ) as codebase:
        foo_file = codebase.get_file(foo_filepath)
        bar_file = codebase.get_file(bar_filepath)
        new_file = "baz_file.ts"
        foo_file.rename(new_file)

    assert not os.path.exists(tmpdir / foo_filepath)
    assert os.path.exists(tmpdir / new_file)
    assert not codebase.has_file(foo_filepath)
    assert codebase.get_file(new_file).filepath == new_file
    assert codebase.get_file(new_file).content == foo_content
    assert len(bar_file.imports) == 1
    assert "import { foo } from 'baz_file';" in bar_file.content


def test_rename_file_no_extension(tmpdir) -> None:
    # language=typescript
    foo_content = """
export function foo(): number {
    return 1;
}
"""
    # language=typescript
    bar_content = """
import { foo } from 'foo_file';

function bar(): number {
    return foo();
}
"""
    foo_filepath = "foo_file.ts"
    bar_filepath = "bar_file.ts"
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={
            foo_filepath: foo_content,
            bar_filepath: bar_content,
        },
        commit=True,
    ) as codebase:
        foo_file = codebase.get_file(foo_filepath)
        bar_file = codebase.get_file(bar_filepath)
        new_file = "baz_file.ts"
        foo_file.rename(new_file)

    assert not os.path.exists(tmpdir / foo_filepath)
    assert os.path.exists(tmpdir / new_file)
    assert not codebase.has_file(foo_filepath)
    assert codebase.get_file(new_file).filepath == new_file
    assert codebase.get_file(new_file).content == foo_content
    assert len(bar_file.imports) == 1
    assert "import { foo } from 'baz_file';" in bar_file.content


@pytest.mark.skip("This should be TODO to enable for all customers.")
def test_rename_file_relative_path(tmpdir) -> None:
    # language=typescript
    foo_content = """
export function foo(): number {
    return 1;
}
"""
    # language=typescript
    bar_content = """
import { foo } from './foo_file';

function bar(): number {
    return foo();
}
"""
    foo_filepath = "foo_file.ts"
    bar_filepath = "bar_file.ts"
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={
            foo_filepath: foo_content,
            bar_filepath: bar_content,
        },
        commit=True,
    ) as codebase:
        foo_file = codebase.get_file(foo_filepath)
        bar_file = codebase.get_file(bar_filepath)
        new_file = "baz_file.ts"
        foo_file.rename(new_file)

    assert not os.path.exists(tmpdir / foo_filepath)
    assert os.path.exists(tmpdir / new_file)
    assert not codebase.has_file(foo_filepath)
    assert codebase.get_file(new_file).filepath == new_file
    assert codebase.get_file(new_file).content == foo_content
    assert len(bar_file.imports) == 1
    assert "import { foo } from './baz_file';" in bar_file.content
