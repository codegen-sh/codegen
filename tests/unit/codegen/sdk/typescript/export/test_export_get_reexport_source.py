from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_reexport_symbol(tmpdir) -> None:
    # language=typescript
    content = """
export { foo } from './m';                  // named re-export
export { default } from './m';              // default re-export
export { bar as baz } from './m';           // aliased re-export
export * from './m';                        // wildcard re-export
export * as namespace from './m';           // namespace re-export
export type { Type } from './m';            // type re-export
export function localFoo() {}               // local export (not re-export)
"""
    # language=typescript
    module_content = """
export const foo = 'foo';
export default function defaultFn() {}
export const bar = 'bar';
export type Type = string;
"""
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content, "m.ts": module_content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        exports = file.exports

        # Named re-export
        assert exports[0].reexport_symbol() == file.imports[0]

        # Default re-export
        assert exports[1].reexport_symbol() == file.imports[1]

        # Aliased re-export
        assert exports[2].reexport_symbol() == file.imports[2]

        # Wildcard re-export
        assert exports[3].reexport_symbol() == file.imports[3]

        # Namespace re-export
        assert exports[4].reexport_symbol() == file.imports[4]

        # Type re-export
        assert exports[5].reexport_symbol() == file.imports[5]

        # Local export (not a re-export)
        assert exports[6].reexport_symbol() is None


def test_reexport_symbol_with_multiple_exports(tmpdir) -> None:
    # language=typescript
    content = """
import { foo, bar } from './m';
export { foo, bar };                // local re-export
export { foo as fooz } from './m';  // direct re-export
"""
    # language=typescript
    module_content = """
export const foo = 'foo';
export const bar = 'bar';
"""
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content, "m.ts": module_content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        exports = file.exports

        # Local re-exports
        assert exports[0].reexport_symbol() == file.imports[0]  # foo
        assert exports[1].reexport_symbol() == file.imports[1]  # bar

        # Direct re-export
        assert exports[2].reexport_symbol() == file.imports[2]  # foo as fooz


def test_reexport_symbol_edge_cases(tmpdir) -> None:
    # language=typescript
    content = """
// Edge case 1: Circular re-exports
export { a as b } from './circular1';
export { b as a } from './circular2';

// Edge case 2: Re-export with multiple levels
export { x } from './level1';  // level1 re-exports from level2, which re-exports from level3

// Edge case 3: Re-export with type modifiers
export { type T1, type T2 as T3 } from './types';

// Edge case 4: Mixed default and named re-exports
export { default as name1, name2 as default } from './mixed';

// Edge case 5: Re-export with namespace collision
export * as ns from './ns1';
export * as ns from './ns2';
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        exports = file.exports

        # Test circular re-exports
        assert exports[0].reexport_symbol() is not None
        assert exports[1].reexport_symbol() is not None
        assert exports[0].reexport_symbol() != exports[1].reexport_symbol()

        # Test multi-level re-exports
        assert exports[2].reexport_symbol() is not None

        # Test type re-exports
        assert exports[3].reexport_symbol() is not None
        assert exports[4].reexport_symbol() is not None

        # Test mixed default/named re-exports
        assert exports[5].reexport_symbol() is not None
        assert exports[6].reexport_symbol() is not None

        # Test namespace collisions
        assert exports[7].reexport_symbol() is not None
        assert exports[8].reexport_symbol() is not None
        assert exports[7].reexport_symbol() != exports[8].reexport_symbol()
