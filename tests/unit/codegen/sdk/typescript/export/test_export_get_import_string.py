from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.enums import ImportType
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_export_get_import_string(tmpdir) -> None:
    # language=typescript
    content1 = """
export function foo() {}
export default function bar() {}
export { foo as renamed } from './other';
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content1}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        exports = file.exports

        # Test named export
        assert exports[0].get_import_string() == "import { foo } from 'test';"
        assert exports[0].get_import_string(alias="myFoo") == "import { foo as myFoo } from 'test';"
        assert exports[0].get_import_string(import_type=ImportType.WILDCARD) == "import * as test from 'test';"

        # Test default export
        assert exports[1].get_import_string() == "import bar from 'test';"
        assert exports[1].get_import_string(alias="myBar") == "import myBar from 'test';"

        # Test reexport
        assert exports[2].get_import_string() == "import { foo as renamed } from './other';"


def test_export_get_import_string_with_type(tmpdir) -> None:
    # language=typescript
    content = """
export type MyType = string;
export interface MyInterface {}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        exports = file.exports

        assert exports[0].get_import_string(is_type_import=True) == "import type { MyType } from 'test';"
        assert exports[1].get_import_string(is_type_import=True) == "import type { MyInterface } from 'test';"


def test_export_get_import_string_edge_cases(tmpdir) -> None:
    # language=typescript
    content = """
// Edge case 1: Export with special characters
export const $special_name$ = 42;

// Edge case 2: Export with reserved keywords as names
export const function = 'not a function';
export const class = 'not a class';

// Edge case 3: Multiple aliases in re-export
export { foo as bar, bar as foo } from './circular';

// Edge case 4: Nested namespace exports
export * as nested from './a';
export { nested as inner } from './b';

// Edge case 5: Complex type exports
export type { Type1 as default } from './types';
export type { default as Type2 } from './types';

// Edge case 6: Mixed type and value exports
export { type TypeA, ValueA } from './mixed';
export { ValueB, type TypeB } from './mixed';
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        exports = file.exports
        for i, export in enumerate(exports):
            print(f"Export {i}: {export.get_import_string()}")
        # Test special characters
        assert exports[0].get_import_string() == "import { $special_name$ } from 'test';"

        # Test reserved keywords
        assert exports[1].get_import_string() == "import { function } from 'test';"
        assert exports[2].get_import_string() == "import { class } from 'test';"

        # Test circular aliases
        assert exports[3].get_import_string() == "import { foo as bar } from './circular';"
        assert exports[4].get_import_string() == "import { bar as foo } from './circular';"

        # Test nested namespaces
        assert exports[5].get_import_string() == "import * as nested from './a';"
        assert exports[6].get_import_string() == "import { nested as inner } from './b';"

        # Test complex type exports
        assert exports[7].get_import_string(is_type_import=True) == "import type { Type1 as default } from './types';"
        assert exports[8].get_import_string(is_type_import=True) == "import type { default as Type2 } from './types';"

        # Test mixed exports
        assert exports[9].get_import_string() == "import { type TypeA, ValueA } from './mixed';"
        assert exports[11].get_import_string() == "import { ValueB, type TypeB } from './mixed';"
