import platform

import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.function import Function
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.utils.normalize import normalize_imports

# All the diff types of JS/TS imports:

# Module import
# import * as module from "./module";

# Named import
# import { foo, bar } from "./module";

# Default import
# import foo from "./module";

# Aliased Named import
# import { foo as baz } from "./module";

# Named with default import
# import foo, { bar, woof as bark } from "./module";

# side effect import
# import "./module";

# type import (also should work with default, alias etc)
# import type DefaultType, { Device, User as u } from "./module";

# Dynamic Import
# const module = await import("./module");


def test_move_to_file_update_all_imports(tmpdir) -> None:
    # ========== [ BEFORE ] ==========
    # language=typescript
    FILE_1_CONTENT = """
export function externalDep() {
    return 42;
}
"""

    # language=typescript
    FILE_2_CONTENT = """
import { externalDep } from 'file1';

function foo() {
    return fooDep() + 1;
}

function fooDep() {
    return 24;
}

export function bar() {
    return externalDep() + barDep();
}

function barDep() {
    return 2;
}
"""

    # language=typescript
    FILE_3_CONTENT = """
import { bar } from 'file2';

export function baz() {
    return bar() + 1;
}
"""

    # ========== [ AFTER ] ==========
    # language=typescript
    EXPECTED_FILE_1_CONTENT = """
export function externalDep() {
    return 42;
}
"""

    # language=typescript
    EXPECTED_FILE_2_CONTENT = """
import { externalDep } from 'file1';

function foo() {
    return fooDep() + 1;
}

function fooDep() {
    return 24;
}
"""

    # language=typescript
    EXPECTED_FILE_3_CONTENT = """
import { externalDep } from 'file1';
import { bar } from 'file3';
export function baz() {
    return bar() + 1;
}

export function barDep() {
    return 2;
}

export function bar() {
    return externalDep() + barDep();
}
"""

    # ===============================
    # TODO: [!HIGH!] Self import of bar in file3
    # TODO: [medium] Why is barDep exported?
    # TODO: [low] Missing newline after import

    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={
            "file1.ts": FILE_1_CONTENT,
            "file2.ts": FILE_2_CONTENT,
            "file3.ts": FILE_3_CONTENT,
        },
    ) as codebase:
        file1 = codebase.get_file("file1.ts")
        file2 = codebase.get_file("file2.ts")
        file3 = codebase.get_file("file3.ts")

        bar = file2.get_function("bar")
        bar.move_to_file(file3, include_dependencies=True, strategy="update_all_imports")

    assert file1.content.strip() == EXPECTED_FILE_1_CONTENT.strip()
    assert file2.content.strip() == EXPECTED_FILE_2_CONTENT.strip()
    assert file3.content.strip() == EXPECTED_FILE_3_CONTENT.strip()


def test_move_to_file_update_all_imports_include_dependencies(tmpdir) -> None:
    # ========== [ BEFORE ] ==========
    # language=typescript
    FILE_1_CONTENT = """
function foo(): number {
    return 1;
}
"""

    # language=typescript
    FILE_2_CONTENT = """
function abc(): string {
    // dependency, gets moved
    return 'abc';
}

export function bar(): string {
    // gets moved
    return abc();
}

function xyz(): number {
    // should stay
    return 3;
}
"""

    # language=typescript
    FILE_3_CONTENT = """
import { bar } from 'file2';

function baz(): string {
    // uses bar
    return bar();
}
"""

    # ========== [ AFTER ] ==========
    # language=typescript
    EXPECTED_FILE_1_CONTENT = """
function foo(): number {
    return 1;
}

export function abc(): string {
    // dependency, gets moved
    return 'abc';
}

export function bar(): string {
    // gets moved
    return abc();
}
"""

    # language=typescript
    EXPECTED_FILE_2_CONTENT = """
function xyz(): number {
    // should stay
    return 3;
}
"""

    # language=typescript
    EXPECTED_FILE_3_CONTENT = """
import { bar } from 'file1';
function baz(): string {
    // uses bar
    return bar();
}
"""

    # ===============================
    # TODO: [medium] Why is abc exported?
    # TODO: [low] Missing newline after import

    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={
            "file1.ts": FILE_1_CONTENT,
            "file2.ts": FILE_2_CONTENT,
            "file3.ts": FILE_3_CONTENT,
        },
    ) as codebase:
        file1 = codebase.get_file("file1.ts")
        file2 = codebase.get_file("file2.ts")
        file3 = codebase.get_file("file3.ts")

        bar_symbol = file2.get_symbol("bar")
        bar_symbol.move_to_file(file1, strategy="update_all_imports", include_dependencies=True)

    assert file1.content.strip() == EXPECTED_FILE_1_CONTENT.strip()
    assert file2.content.strip() == EXPECTED_FILE_2_CONTENT.strip()
    assert file3.content.strip() == EXPECTED_FILE_3_CONTENT.strip()

    # Check new symbol
    new_symbol = file1.get_symbol("bar")
    assert new_symbol.file == file1
    assert new_symbol.name == "bar"
    assert isinstance(new_symbol, Function)


def test_move_to_file_update_all_imports_without_include_dependencies(tmpdir) -> None:
    # ========== [ BEFORE ] ==========
    # language=typescript
    FILE_1_CONTENT = """
function foo(): number {
    return 1;
}
"""

    # language=typescript
    FILE_2_CONTENT = """
function abc(): string {
    // dependency, DOES NOT GET MOVED
    return 'abc';
}

export function bar(): string {
    // gets moved
    return abc();
}

function xyz(): number {
    // should stay
    return 3;
}
"""

    # language=typescript
    FILE_3_CONTENT = """
import { bar } from 'file2';

function baz(): string {
    // uses bar
    return bar();
}
"""

    # ========== [ AFTER ] ==========
    # language=typescript
    EXPECTED_FILE_1_CONTENT = """
import { abc } from 'file2';

function foo(): number {
    return 1;
}

export function bar(): string {
    // gets moved
    return abc();
}
"""

    # language=typescript
    EXPECTED_FILE_2_CONTENT = """
export function abc(): string {
    // dependency, DOES NOT GET MOVED
    return 'abc';
}

function xyz(): number {
    // should stay
    return 3;
}
"""

    # language=typescript
    EXPECTED_FILE_3_CONTENT = """
import { bar } from 'file1';
function baz(): string {
    // uses bar
    return bar();
}
"""

    # ===============================
    # TODO: [low] Missing newline after import

    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={
            "file1.ts": FILE_1_CONTENT,
            "file2.ts": FILE_2_CONTENT,
            "file3.ts": FILE_3_CONTENT,
        },
    ) as codebase:
        file1 = codebase.get_file("file1.ts")
        file2 = codebase.get_file("file2.ts")
        file3 = codebase.get_file("file3.ts")

        bar_symbol = file2.get_symbol("bar")
        bar_symbol.move_to_file(file1, strategy="update_all_imports", include_dependencies=False)

    assert file1.content.strip() == EXPECTED_FILE_1_CONTENT.strip()
    assert file2.content.strip() == EXPECTED_FILE_2_CONTENT.strip()
    assert file3.content.strip() == EXPECTED_FILE_3_CONTENT.strip()

    # Check new symbol
    new_symbol = file1.get_symbol("bar")
    assert new_symbol.file == file1
    assert new_symbol.name == "bar"
    assert isinstance(new_symbol, Function)


def test_move_to_file_add_back_edge(tmpdir) -> None:
    # ========== [ BEFORE ] ==========
    # language=typescript
    FILE_1_CONTENT = """
export function externalDep() {
    return 42;
}
"""

    # language=typescript
    FILE_2_CONTENT = """
import { externalDep } from 'file1';

function foo() {
    return fooDep() + 1;
}

function fooDep() {
    return 24;
}

export function bar() {
    return externalDep() + barDep();
}

function barDep() {
    return 2;
}
"""

    # language=typescript
    FILE_3_CONTENT = """
import { bar } from 'file2';

export function baz() {
    return bar() + 1;
}
"""

    # ========== [ AFTER ] ==========
    # language=typescript
    EXPECTED_FILE_1_CONTENT = """
export function externalDep() {
    return 42;
}
"""

    # language=typescript
    EXPECTED_FILE_2_CONTENT = """
export { bar } from 'file3'
import { externalDep } from 'file1';

function foo() {
    return fooDep() + 1;
}

function fooDep() {
    return 24;
}
"""

    # language=typescript
    EXPECTED_FILE_3_CONTENT = """
import { externalDep } from 'file1';
import { bar } from 'file2';

export function baz() {
    return bar() + 1;
}

export function barDep() {
    return 2;
}

export function bar() {
    return externalDep() + barDep();
}
"""

    # ===============================
    # TODO: [!HIGH!] Creates circular import for bar between file2 and file3
    # TODO: [medium] Missing semicolon in import on file3
    # TODO: [medium] Why did barDep get changed to export?

    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={
            "file1.ts": FILE_1_CONTENT,
            "file2.ts": FILE_2_CONTENT,
            "file3.ts": FILE_3_CONTENT,
        },
    ) as codebase:
        file1 = codebase.get_file("file1.ts")
        file2 = codebase.get_file("file2.ts")
        file3 = codebase.get_file("file3.ts")

        bar = file2.get_function("bar")
        bar.move_to_file(file3, include_dependencies=True, strategy="add_back_edge")

    assert file1.content.strip() == EXPECTED_FILE_1_CONTENT.strip()
    assert file2.content.strip() == EXPECTED_FILE_2_CONTENT.strip()
    assert file3.content.strip() == EXPECTED_FILE_3_CONTENT.strip()


def test_move_to_file_add_back_edge_including_dependencies(tmpdir) -> None:
    # ========== [ BEFORE ] ==========
    # language=typescript
    FILE_1_CONTENT = """
function foo(): number {
    return 1;
}
"""

    # language=typescript
    FILE_2_CONTENT = """
function abc(): string {
    // dependency, gets moved
    return 'abc';
}

export function bar(): string {
    // gets moved
    return abc();
}

function xyz(): number {
    // should stay
    return 3;
}
"""

    # language=typescript
    FILE_3_CONTENT = """
import { bar } from 'file2';

function baz(): string {
    // uses bar
    return bar();
}
"""

    # ========== [ AFTER ] ==========
    # language=typescript
    EXPECTED_FILE_1_CONTENT = """
function foo(): number {
    return 1;
}

export function abc(): string {
    // dependency, gets moved
    return 'abc';
}

export function bar(): string {
    // gets moved
    return abc();
}
"""

    # language=typescript
    EXPECTED_FILE_2_CONTENT = """
export { bar } from 'file1'

function xyz(): number {
    // should stay
    return 3;
}
"""

    # language=typescript
    EXPECTED_FILE_3_CONTENT = """
import { bar } from 'file2';

function baz(): string {
    // uses bar
    return bar();
}
"""

    # ===============================
    # TODO: [medium] Missing semicolon in import on file2
    # TODO: [medium] Why is abc exported?

    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={
            "file1.ts": FILE_1_CONTENT,
            "file2.ts": FILE_2_CONTENT,
            "file3.ts": FILE_3_CONTENT,
        },
    ) as codebase:
        file1 = codebase.get_file("file1.ts")
        file2 = codebase.get_file("file2.ts")
        file3 = codebase.get_file("file3.ts")

        bar_symbol = file2.get_symbol("bar")
        bar_symbol.move_to_file(file1, strategy="add_back_edge", include_dependencies=True)

    assert file1.content.strip() == EXPECTED_FILE_1_CONTENT.strip()
    assert file2.content.strip() == EXPECTED_FILE_2_CONTENT.strip()
    assert file3.content.strip() == EXPECTED_FILE_3_CONTENT.strip()

    # Check new symbol
    new_symbol = file1.get_symbol("bar")
    assert new_symbol.file == file1
    assert new_symbol.name == "bar"
    assert isinstance(new_symbol, Function)


def test_move_to_file_add_back_edge_without_include_dependencies(tmpdir) -> None:
    # ========== [ BEFORE ] ==========
    # language=typescript
    FILE_1_CONTENT = """
function foo(): number {
    return 1;
}
"""

    # language=typescript
    FILE_2_CONTENT = """
function abc(): string {
    // dependency, DOES NOT GET MOVED
    return 'abc';
}

export function bar(): string {
    // gets moved
    return abc();
}

function xyz(): number {
    // should stay
    return 3;
}
"""

    # language=typescript
    FILE_3_CONTENT = """
import { bar } from 'file2';

function baz(): string {
    // uses bar
    return bar();
}
"""

    # ========== [ AFTER ] ==========
    # language=typescript
    EXPECTED_FILE_1_CONTENT = """
import { abc } from 'file2';

function foo(): number {
    return 1;
}

export function bar(): string {
    // gets moved
    return abc();
}
"""

    # language=typescript
    EXPECTED_FILE_2_CONTENT = """
export { bar } from 'file1'

export function abc(): string {
    // dependency, DOES NOT GET MOVED
    return 'abc';
}

function xyz(): number {
    // should stay
    return 3;
}
"""

    # language=typescript
    EXPECTED_FILE_3_CONTENT = """
import { bar } from 'file2';

function baz(): string {
    // uses bar
    return bar();
}
"""

    # ===============================
    # TODO: [medium] Missing semicolon in import on file2

    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={
            "file1.ts": FILE_1_CONTENT,
            "file2.ts": FILE_2_CONTENT,
            "file3.ts": FILE_3_CONTENT,
        },
    ) as codebase:
        file1 = codebase.get_file("file1.ts")
        file2 = codebase.get_file("file2.ts")
        file3 = codebase.get_file("file3.ts")

        bar_symbol = file2.get_symbol("bar")
        bar_symbol.move_to_file(file1, strategy="add_back_edge", include_dependencies=False)

    assert file1.content.strip() == EXPECTED_FILE_1_CONTENT.strip()
    assert file2.content.strip() == EXPECTED_FILE_2_CONTENT.strip()
    assert file3.content.strip() == EXPECTED_FILE_3_CONTENT.strip()

    # Check new symbol
    new_symbol = file1.get_symbol("bar")
    assert new_symbol.file == file1
    assert new_symbol.name == "bar"
    assert isinstance(new_symbol, Function)


def test_move_to_file_duplicate_dependencies(tmpdir) -> None:
    # ========== [ BEFORE ] ==========
    # language=typescript
    FILE_1_CONTENT = """
export function externalDep() {
    return 42;
}
"""

    # language=typescript
    FILE_2_CONTENT = """
import { externalDep } from 'file1';

function foo() {
    return fooDep() + 1;
}

function fooDep() {
    return 24;
}

export function bar() {
    return externalDep() + barDep();
}

function barDep() {
    return 2;
}
"""

    # language=typescript
    FILE_3_CONTENT = """
import { bar } from 'file2';

export function baz() {
    return bar() + 1;
}
"""

    # ========== [ AFTER ] ==========
    # language=typescript
    EXPECTED_FILE_1_CONTENT = """
export function externalDep() {
    return 42;
}
"""

    # language=typescript
    EXPECTED_FILE_2_CONTENT = """
import { externalDep } from 'file1';

function foo() {
    return fooDep() + 1;
}

function fooDep() {
    return 24;
}

export function bar() {
    return externalDep() + barDep();
}
"""

    # language=typescript
    EXPECTED_FILE_3_CONTENT = """
import { externalDep } from 'file1';
import { bar } from 'file2';

export function baz() {
    return bar() + 1;
}

export function barDep() {
    return 2;
}

export function bar() {
    return externalDep() + barDep();
}
"""

    # ===============================
    # TODO: [!HIGH!] Incorrect deletion of bar's import and dependency
    # TODO: [medium] Why is barDep exported?

    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={
            "file1.ts": FILE_1_CONTENT,
            "file2.ts": FILE_2_CONTENT,
            "file3.ts": FILE_3_CONTENT,
        },
    ) as codebase:
        file1 = codebase.get_file("file1.ts")
        file2 = codebase.get_file("file2.ts")
        file3 = codebase.get_file("file3.ts")

        bar = file2.get_function("bar")
        bar.move_to_file(file3, include_dependencies=True, strategy="duplicate_dependencies")

    assert file1.content.strip() == EXPECTED_FILE_1_CONTENT.strip()
    assert file2.content.strip() == EXPECTED_FILE_2_CONTENT.strip()
    assert file3.content.strip() == EXPECTED_FILE_3_CONTENT.strip()


def test_move_to_file_duplicate_dependencies_include_dependencies(tmpdir) -> None:
    # ========== [ BEFORE ] ==========
    # language=typescript
    FILE_1_CONTENT = """
function foo(): number {
    return 1;
}
"""

    # language=typescript
    FILE_2_CONTENT = """
function abc(): string {
    // dependency, gets duplicated
    return 'abc';
}

export function bar(): string {
    // gets duplicated
    return abc();
}

function xyz(): number {
    // should stay
    return 3;
}
"""

    # language=typescript
    FILE_3_CONTENT = """
import { bar } from 'file2';

function baz(): string {
    // uses bar
    return bar();
}
"""

    # ========== [ AFTER ] ==========
    # language=typescript
    EXPECTED_FILE_1_CONTENT = """
function foo(): number {
    return 1;
}

export function abc(): string {
    // dependency, gets duplicated
    return 'abc';
}

export function bar(): string {
    // gets duplicated
    return abc();
}
"""

    # language=typescript
    EXPECTED_FILE_2_CONTENT = """
export function bar(): string {
    // gets duplicated
    return abc();
}

function xyz(): number {
    // should stay
    return 3;
}
"""

    # language=typescript
    EXPECTED_FILE_3_CONTENT = """
import { bar } from 'file2';

function baz(): string {
    // uses bar
    return bar();
}
"""

    # ===============================
    # TODO: [!HIGH!] Incorrect deletion of bar's import and dependency
    # TODO: [medium] Why is abc exported?
    # TODO: [low] Missing newline after import

    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={
            "file1.ts": FILE_1_CONTENT,
            "file2.ts": FILE_2_CONTENT,
            "file3.ts": FILE_3_CONTENT,
        },
    ) as codebase:
        file1 = codebase.get_file("file1.ts")
        file2 = codebase.get_file("file2.ts")
        file3 = codebase.get_file("file3.ts")

        bar_symbol = file2.get_symbol("bar")
        bar_symbol.move_to_file(file1, strategy="duplicate_dependencies", include_dependencies=True)

    assert file1.content.strip() == EXPECTED_FILE_1_CONTENT.strip()
    assert file2.content.strip() == EXPECTED_FILE_2_CONTENT.strip()
    assert file3.content.strip() == EXPECTED_FILE_3_CONTENT.strip()

    # Check new symbol
    new_symbol = file1.get_symbol("bar")
    assert new_symbol.file == file1
    assert new_symbol.name == "bar"
    assert isinstance(new_symbol, Function)


def test_move_to_file_duplicate_dependencies_without_include_dependencies(tmpdir) -> None:
    # ========== [ BEFORE ] ==========
    # language=typescript
    FILE_1_CONTENT = """
function foo(): number {
    return 1;
}
"""

    # language=typescript
    FILE_2_CONTENT = """
function abc(): string {
    // dependency, DOES NOT GET MOVED
    return 'abc';
}

export function bar(): string {
    // gets duplicated
    return abc();
}

function xyz(): number {
    // should stay
    return 3;
}
"""

    # language=typescript
    FILE_3_CONTENT = """
import { bar } from 'file2';

function baz(): string {
    // uses bar
    return bar();
}
"""

    # ========== [ AFTER ] ==========
    # language=typescript
    EXPECTED_FILE_1_CONTENT = """
import { abc } from 'file2';

function foo(): number {
    return 1;
}

export function bar(): string {
    // gets duplicated
    return abc();
}
"""

    # language=typescript
    EXPECTED_FILE_2_CONTENT = """
export function abc(): string {
    // dependency, DOES NOT GET MOVED
    return 'abc';
}

export function bar(): string {
    // gets duplicated
    return abc();
}

function xyz(): number {
    // should stay
    return 3;
}
"""

    # language=typescript
    EXPECTED_FILE_3_CONTENT = """
import { bar } from 'file2';

function baz(): string {
    // uses bar
    return bar();
}
"""

    # ===============================

    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={
            "file1.ts": FILE_1_CONTENT,
            "file2.ts": FILE_2_CONTENT,
            "file3.ts": FILE_3_CONTENT,
        },
    ) as codebase:
        file1 = codebase.get_file("file1.ts")
        file2 = codebase.get_file("file2.ts")
        file3 = codebase.get_file("file3.ts")

        bar_symbol = file2.get_symbol("bar")
        bar_symbol.move_to_file(file1, strategy="duplicate_dependencies", include_dependencies=False)

    assert file1.content.strip() == EXPECTED_FILE_1_CONTENT.strip()
    assert file2.content.strip() == EXPECTED_FILE_2_CONTENT.strip()
    assert file3.content.strip() == EXPECTED_FILE_3_CONTENT.strip()

    # Check new symbol
    new_symbol = file1.get_symbol("bar")
    assert new_symbol.file == file1
    assert new_symbol.name == "bar"
    assert isinstance(new_symbol, Function)


def test_move_to_file_import_star(tmpdir) -> None:
    """Test moving a symbol to a new file, where consumers import it via import *
    and also import other pieces from the original module which aren't moving
    """
    # ========== [ BEFORE ] ==========
    # language=typescript
    SOURCE_FILE_CONTENT = """
export function targetFunction() {
    return "Hello World";
}
"""

    # language=typescript
    DEST_FILE_CONTENT = """
"""

    # language=typescript
    USAGE_FILE_CONTENT = """
import * as source from "./source";
const value1 = source.targetFunction();
const value2 = source.otherFunction();
const value3 = source.targetFunction();
"""

    # ========== [ AFTER ] ==========
    # language=typescript
    EXPECTED_USAGE_FILE_CONTENT = """
import { targetFunction } from 'destination';
import * as source from "./source";
const value1 = targetFunction();
const value2 = source.otherFunction();
const value3 = targetFunction();
"""

    # ===============================

    files = {
        "source.ts": SOURCE_FILE_CONTENT,
        "destination.ts": DEST_FILE_CONTENT,
        "usage.ts": USAGE_FILE_CONTENT,
    }

    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
        source_file = codebase.get_file("source.ts")
        dest_file = codebase.get_file("destination.ts")
        usage_file = codebase.get_file("usage.ts")

        target_function = source_file.get_function("targetFunction")
        target_function.move_to_file(dest_file, include_dependencies=False, strategy="update_all_imports")

    assert usage_file.content.strip() == EXPECTED_USAGE_FILE_CONTENT.strip()


def test_move_to_file_named_import(tmpdir) -> None:
    """Test moving a symbol to a new file, where consumers import it via import { name }
    and also import other pieces from the original module which aren't moving
    """
    # ========== [ BEFORE ] ==========
    # language=typescript
    SOURCE_FILE_CONTENT = """
export function targetFunction() {
    return "Hello World";
}
"""

    # language=typescript
    DEST_FILE_CONTENT = """
"""

    # language=typescript
    USAGE_FILE_CONTENT = """
import { targetFunction, otherFunction } from "./source";
const value = targetFunction();
"""

    # ========== [ AFTER ] ==========
    # language=typescript
    EXPECTED_USAGE_FILE_CONTENT = """
import { targetFunction } from 'destination';
import { otherFunction } from "./source";
const value = targetFunction();
"""

    # ===============================

    files = {
        "source.ts": SOURCE_FILE_CONTENT,
        "destination.ts": DEST_FILE_CONTENT,
        "usage.ts": USAGE_FILE_CONTENT,
    }

    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
        source_file = codebase.get_file("source.ts")
        dest_file = codebase.get_file("destination.ts")
        usage_file = codebase.get_file("usage.ts")

        target_function = source_file.get_function("targetFunction")
        target_function.move_to_file(dest_file, include_dependencies=False, strategy="update_all_imports")

    assert usage_file.content.strip() == EXPECTED_USAGE_FILE_CONTENT.strip()


def test_move_to_file_only_named_import(tmpdir) -> None:
    """Test moving a symbol to a new file, where consumers import it via import {name}
    and don't import anything else removes that whole import line
    """
    # ========== [ BEFORE ] ==========
    # language=typescript
    SOURCE_FILE_CONTENT = """
export function targetFunction() {
    return "Hello World";
}
"""

    # language=typescript
    DEST_FILE_CONTENT = """
"""

    # language=typescript
    USAGE_FILE_CONTENT = """
import { targetFunction } from "./source";
const value = targetFunction();
"""

    # ========== [ AFTER ] ==========
    # language=typescript
    EXPECTED_USAGE_FILE_CONTENT = """
import { targetFunction } from 'destination';
const value = targetFunction();
"""

    # ===============================

    files = {
        "source.ts": SOURCE_FILE_CONTENT,
        "destination.ts": DEST_FILE_CONTENT,
        "usage.ts": USAGE_FILE_CONTENT,
    }

    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
        source_file = codebase.get_file("source.ts")
        dest_file = codebase.get_file("destination.ts")
        usage_file = codebase.get_file("usage.ts")

        target_function = source_file.get_function("targetFunction")
        target_function.move_to_file(dest_file, include_dependencies=False, strategy="update_all_imports")

    assert usage_file.content.strip() == EXPECTED_USAGE_FILE_CONTENT.strip()


def test_move_to_file_include_type_import_dependencies(tmpdir) -> None:
    """Test moving a symbol to a new file with type dependencies"""
    # ========== [ BEFORE ] ==========
    # language=typescript
    TYPES_FILE_CONTENT = """
export type TypeA = {
    prop: string;
}

export type TypeB = {
    value: number;
}

export type TypeC = {
    flag: boolean;
}

export function helper(input: string): string {
    return input.toUpperCase();
}
"""

    # ========== [ BEFORE ] ==========
    # language=typescript
    SOURCE_FILE_CONTENT = """
import type { TypeA, TypeB, TypeC } from "types";
import { helper } from "types";

export function targetFunction(input: TypeA): TypeB {
    const value = helper(input.prop);
    return {
        value: value.length
    };
}
"""

    # language=typescript
    DEST_FILE_CONTENT = """
"""

    # ========== [ AFTER ] ==========
    # language=typescript
    EXPECTED_DEST_FILE_CONTENT = """
import type { TypeA } from 'types';
import { helper } from 'types';
import type { TypeB } from 'types';



export function targetFunction(input: TypeA): TypeB {
    const value = helper(input.prop);
    return {
        value: value.length
    };
}
"""

    # ===============================
    # TODO: [medium] Is the extra new lines here expected behavior?

    files = {
        "types.ts": TYPES_FILE_CONTENT,
        "source.ts": SOURCE_FILE_CONTENT,
        "destination.ts": DEST_FILE_CONTENT,
    }

    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
        source_file = codebase.get_file("source.ts")
        dest_file = codebase.get_file("destination.ts")

        target_function = source_file.get_function("targetFunction")
        target_function.move_to_file(dest_file, include_dependencies=False, strategy="update_all_imports")

    assert normalize_imports(dest_file.content.strip()) == normalize_imports(EXPECTED_DEST_FILE_CONTENT.strip())


def test_move_to_file_imports_local_deps(tmpdir) -> None:
    """Test moving a symbol that has dependencies on local symbols in the same file"""
    # ========== [ BEFORE ] ==========
    # language=typescript
    SOURCE_FILE_CONTENT = """
export function targetFunction(value: number): number {
    return helperFunction(value) * 2;
}

function helperFunction(x: number): number {
    return x + 1;
}
"""

    # language=typescript
    DEST_FILE_CONTENT = """
"""

    # ========== [ AFTER ] ==========
    # language=typescript
    EXPECTED_DEST_FILE_CONTENT = """
import { helperFunction } from 'source';



export function targetFunction(value: number): number {
    return helperFunction(value) * 2;
}
"""

    # language=typescript
    EXPECTED_SOURCE_FILE_CONTENT = """
export function helperFunction(x: number): number {
    return x + 1;
}
"""

    # ===============================
    # TODO: [medium] Is the extra new lines here expected behavior?

    files = {
        "source.ts": SOURCE_FILE_CONTENT,
        "destination.ts": DEST_FILE_CONTENT,
    }

    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
        source_file = codebase.get_file("source.ts")
        dest_file = codebase.get_file("destination.ts")

        target_function = source_file.get_function("targetFunction")
        target_function.move_to_file(dest_file, include_dependencies=False, strategy="update_all_imports")

    assert normalize_imports(dest_file.content.strip()) == normalize_imports(EXPECTED_DEST_FILE_CONTENT.strip())
    assert normalize_imports(source_file.content.strip()) == normalize_imports(EXPECTED_SOURCE_FILE_CONTENT.strip())


def test_function_move_to_file_circular_dependency(tmpdir) -> None:
    # ========== [ BEFORE ] ==========
    # language=typescript
    FILE_1_CONTENT = """
export function foo(): number {
    return bar() + 1;
}

export function bar(): number {
    return foo() + 1;
}
    """

    # ========== [ AFTER ] ==========
    # language=typescript
    EXPECTED_FILE_1_CONTENT = """
export { bar } from 'file2'
export { foo } from 'file2'
"""
    # language=typescript
    EXPECTED_FILE_2_CONTENT = """
export function bar(): number {
    return foo() + 1;
}

export function foo(): number {
    return bar() + 1;
}
"""

    # ===============================
    # TODO: [low] Missing semicolons

    with get_codebase_session(
        tmpdir=tmpdir,
        files={"file1.ts": FILE_1_CONTENT},
        programming_language=ProgrammingLanguage.TYPESCRIPT,
    ) as codebase:
        file1 = codebase.get_file("file1.ts")
        foo = file1.get_function("foo")
        bar = file1.get_function("bar")
        assert bar in foo.dependencies
        assert foo in bar.dependencies

        file2 = codebase.create_file("file2.ts", "")
        foo.move_to_file(file2, include_dependencies=True, strategy="add_back_edge")

    assert file1.content.strip() == EXPECTED_FILE_1_CONTENT.strip()
    assert file2.content.strip() == EXPECTED_FILE_2_CONTENT.strip()


@pytest.mark.skipif(condition=platform.system() != "Linux", reason="Only works on case-sensitive file systems")
def test_function_move_to_file_lower_upper(tmpdir) -> None:
    # ========== [ BEFORE ] ==========
    # language=typescript
    FILE_1_CONTENT = """
export function foo(): number {
    return bar() + 1;
}

export function bar(): number {
    return foo() + 1;
}
    """

    # ========== [ AFTER ] ==========
    # language=typescript
    EXPECTED_FILE_1_CONTENT = """
export { bar } from 'File1'
export { foo } from 'File1'
"""

    # language=typescript
    EXPECTED_FILE_2_CONTENT = """
export function bar(): number {
    return foo() + 1;
}

export function foo(): number {
    return bar() + 1;
}
"""

    # ===============================
    # TODO: [low] Missing semicolons

    with get_codebase_session(
        tmpdir=tmpdir,
        files={"file1.ts": FILE_1_CONTENT},
        programming_language=ProgrammingLanguage.TYPESCRIPT,
    ) as codebase:
        file1 = codebase.get_file("file1.ts")
        foo = file1.get_function("foo")
        bar = file1.get_function("bar")
        assert bar in foo.dependencies
        assert foo in bar.dependencies

        file2 = codebase.create_file("File1.ts", "")
        foo.move_to_file(file2, include_dependencies=True, strategy="add_back_edge")

    assert file1.content.strip() == EXPECTED_FILE_1_CONTENT.strip()
    assert file2.content.strip() == EXPECTED_FILE_2_CONTENT.strip()


def test_function_move_to_file_no_deps(tmpdir) -> None:
    # ========== [ BEFORE ] ==========
    # language=typescript
    FILE_1_CONTENT = """
export function foo(): number {
    return bar() + 1;
}

export function bar(): number {
    return foo() + 1;
}
    """

    # ========== [ AFTER ] ==========
    # language=typescript
    EXPECTED_FILE_1_CONTENT = """
import { foo } from 'File2';
export { foo }

export function bar(): number {
    return foo() + 1;
}
"""
    # language=typescript
    EXPECTED_FILE_2_CONTENT = """
import { bar } from 'file1';


export function foo(): number {
    return bar() + 1;
}
"""

    # ===============================
    # TODO: [medium] Is the extra new lines here expected behavior?
    # TODO: [low] Missing semicolons
    # TOOD: [low] Import and export should be changed to a re-export

    with get_codebase_session(
        tmpdir=tmpdir,
        files={"file1.ts": FILE_1_CONTENT},
        programming_language=ProgrammingLanguage.TYPESCRIPT,
    ) as codebase:
        file1 = codebase.get_file("file1.ts")
        foo = file1.get_function("foo")
        bar = file1.get_function("bar")
        assert bar in foo.dependencies
        assert foo in bar.dependencies

        file2 = codebase.create_file("File2.ts", "")
        foo.move_to_file(file2, include_dependencies=False, strategy="add_back_edge")

    assert file1.content.strip() == EXPECTED_FILE_1_CONTENT.strip()
    assert file2.content.strip() == EXPECTED_FILE_2_CONTENT.strip()


@pytest.mark.skipif(condition=platform.system() != "Linux", reason="Only works on case-sensitive file systems")
def test_function_move_to_file_lower_upper_no_deps(tmpdir) -> None:
    # ========== [ BEFORE ] ==========
    # language=typescript
    FILE_1_CONTENT = """
export function foo(): number {
    return bar() + 1;
}

export function bar(): number {
    return foo() + 1;
}
    """

    # ========== [ AFTER ] ==========
    # language=typescript
    EXPECTED_FILE_1_CONTENT = """
import { foo } from 'File1';
export { foo }

export function bar(): number {
    return foo() + 1;
}
"""

    # language=typescript
    EXPECTED_FILE_2_CONTENT = """
import { bar } from 'file1';


export function foo(): number {
    return bar() + 1;
}
"""

    # ===============================
    # TODO: [medium] Is the extra new lines here expected behavior?
    # TODO: [low] Missing semicolons
    # TOOD: [low] Import and export should be changed to a re-export

    with get_codebase_session(
        tmpdir=tmpdir,
        files={"file1.ts": FILE_1_CONTENT},
        programming_language=ProgrammingLanguage.TYPESCRIPT,
    ) as codebase:
        file1 = codebase.get_file("file1.ts")
        foo = file1.get_function("foo")
        bar = file1.get_function("bar")
        assert bar in foo.dependencies
        assert foo in bar.dependencies

        file2 = codebase.create_file("File1.ts", "")
        foo.move_to_file(file2, include_dependencies=False, strategy="add_back_edge")

    assert file1.content.strip() == EXPECTED_FILE_1_CONTENT.strip()
    assert file2.content.strip() == EXPECTED_FILE_2_CONTENT.strip()
