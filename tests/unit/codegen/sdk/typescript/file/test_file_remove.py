import os

import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def tets_remove_existing_file(tmpdir) -> None:
    # language=typescript
    content = """
function foo(bar: number): number {
    return bar;
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        file.remove()

    assert not os.path.exists(file.filepath)


def test_remove_unused_imports_complete_removal(tmpdir):
    content = """
    import { unused1, unused2 } from './module1';
    import type { UnusedType } from './types';

    const x = 5;
    """
    expected = """
    const x = 5;
    """

    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as codebase:
        file = codebase.get_file("test.ts")
        file.remove_unused_imports()
    assert file.content.strip() == expected.strip()


def test_remove_unused_imports_partial_removal(tmpdir):
    content = """
    import { used, unused } from './module1';

    console.log(used);
    """
    expected = """
    import { used } from './module1';

    console.log(used);
    """

    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as codebase:
        file = codebase.get_file("test.ts")
        file.remove_unused_imports()
    assert file.content.strip() == expected.strip()


def test_remove_unused_imports_with_side_effects(tmpdir):
    content = """
    import './styles.css';
    import { unused } from './module1';

    const x = 5;
    """
    expected = """
    import './styles.css';

    const x = 5;
    """

    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as codebase:
        file = codebase.get_file("test.ts")
        file.remove_unused_imports()
    assert file.content.strip() == expected.strip()


def test_remove_unused_imports_with_moved_symbols(tmpdir):
    content1 = """
    import { helper } from './utils';

    export function foo() {
        return helper();
    }
    """
    # The original file should be empty after move since foo was the only content
    expected1 = ""

    content2 = """
    export function helper() {
        return true;
    }
    """

    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"main.ts": content1, "utils.ts": content2}) as codebase:
        main_file = codebase.get_file("main.ts")
        foo = main_file.get_function("foo")

        # Move foo to a new file
        new_file = codebase.create_file("new.ts")
        foo.move_to_file(new_file, cleanup_unused_imports=False)
        codebase.commit()
        # Confirm cleanup false is respected
        assert main_file.content.strip() == "import { helper } from './utils';"

        # Now explicitly remove unused imports after the move
        main_file.remove_unused_imports()
    assert main_file.content.strip() == ""


@pytest.mark.skip(reason="This test is not implemented properly yet")
def test_remove_unused_exports_with_side_effects(tmpdir):
    content = """
import './styles.css';
export const unused = 5;
export function usedFunction() { return true; }

const x = usedFunction();
    """
    expected = """
import './styles.css';
export function usedFunction() { return true; }

const x = usedFunction();
    """

    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as codebase:
        file = codebase.get_file("test.ts")
        file.remove_unused_exports()
    assert file.content.strip() == expected.strip()


@pytest.mark.skip(reason="This test is not implemented properly yet")
def test_remove_unused_exports_with_multiple_types(tmpdir):
    content = """
export const UNUSED_CONSTANT = 42;
export type UnusedType = string;
export interface UnusedInterface {}
export default function main() { return true; }
export function usedFunction() { return true; }
const x = usedFunction();
    """
    # Only value exports that are unused should be removed
    expected = """
export type UnusedType = string;
export interface UnusedInterface {}
export default function main() { return true; }
export function usedFunction() { return true; }
const x = usedFunction();
    """

    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as codebase:
        file = codebase.get_file("test.ts")
        file.remove_unused_exports()
    assert file.content.strip() == expected.strip()


@pytest.mark.skip(reason="This test is not implemented properly yet")
def test_remove_unused_exports_with_reexports(tmpdir):
    content1 = """
export { helper } from './utils';
export { unused } from './other';
export function localFunction() { return true; }
    """
    content2 = """
import { helper } from './main';
const x = helper();
    """
    expected1 = """
export { helper } from './utils';
export function localFunction() { return true; }
    """

    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"main.ts": content1, "other.ts": content2}) as codebase:
        main_file = codebase.get_file("main.ts")
        main_file.remove_unused_exports()
    assert main_file.content.strip() == expected1.strip()


def test_remove_unused_exports_with_moved_and_reexported_symbol(tmpdir):
    content1 = """
export function helper() {
    return true;
}
    """
    content2 = """
import { helper } from './utils';
export { helper };  // This re-export should be preserved as it's used

const x = helper();
    """
    content3 = """
import { helper } from './main';

function useHelper() {
    return helper();
}
    """

    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"utils.ts": content1, "main.ts": content2, "consumer.ts": content3}) as codebase:
        utils_file = codebase.get_file("utils.ts")
        main_file = codebase.get_file("main.ts")
        consumer_file = codebase.get_file("consumer.ts")
        # Move helper to main.ts
        helper = utils_file.get_function("helper")
        helper.move_to_file(main_file)

        # Remove unused exports
        utils_file.remove_unused_exports()
        main_file.remove_unused_exports()

    # The re-export in main.ts should be preserved since it's used by consumer.ts
    assert "export { helper }" in main_file.content
    # The original export in utils.ts should be gone
    assert "export function helper" not in utils_file.content
