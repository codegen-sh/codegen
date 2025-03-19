from typing import TYPE_CHECKING

import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.typescript.namespace import TSNamespace


def test_namespace_add_symbol(tmpdir) -> None:
    """Test adding symbols to namespace."""
    FILE_NAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
    namespace MyNamespace {
        export const x = 1;
    }
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME: FILE_CONTENT}) as codebase:
        file = codebase.get_file("test.ts")
        namespace: TSNamespace = codebase.get_symbol("MyNamespace")

        # 1. a) Add new symbol from object, then manually remove the original symbol from the file
        # 1. b) Add new symbol by moving operation
        file.add_symbol_from_source(source="const ya = 2")
        codebase.ctx.commit_transactions()
        new_const = file.get_symbol("ya")

        # Store original location

        # Add to namespace and remove from original location
        namespace.add_symbol(new_const, should_export=True)

        codebase.ctx.commit_transactions()

        # Get fresh reference to namespace
        namespace: TSNamespace = codebase.get_symbol("MyNamespace")

        # Verify symbols were moved correctly
        assert namespace.get_symbol("ya") is not None
        assert namespace.get_symbol("ya").export is not None

        # 2. Add new symbol from string
        code = "const z = 3"
        namespace.add_symbol_from_source(code)
        codebase.ctx.commit_transactions()
        namespace: TSNamespace = codebase.get_symbol("MyNamespace")

        code_symbol = namespace.get_symbol("z", get_private=True)
        # Verify exported symbol
        assert code_symbol is not None
        assert code_symbol.name == "z"

        assert len(namespace.symbols) == 3
        assert {s.name for s in namespace.symbols} == {"x", "ya", "z"}


def test_namespace_remove_symbol(tmpdir) -> None:
    """Test removing symbols from namespace."""
    FILE_NAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
    namespace MyNamespace {
        export const x = 1;
        export const y = 2;
    }
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME: FILE_CONTENT}) as codebase:
        namespace: TSNamespace = codebase.get_symbol("MyNamespace")

        # Remove existing symbol
        removed = namespace.remove_symbol("x")
        codebase.ctx.commit_transactions()
        assert removed is not None
        assert removed.name == "x"

        # Verify symbol was removed
        assert namespace.get_symbol("x") is None
        assert len(namespace.symbols) == 1
        assert namespace.symbols[0].name == "y"

        # Try removing non-existent symbol
        assert namespace.remove_symbol("z") is None


def test_namespace_rename(tmpdir) -> None:
    """Test renaming namespace."""
    FILE_NAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
    namespace OldName {
        export const x = 1;
    }
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME: FILE_CONTENT}) as codebase:
        namespace: TSNamespace = codebase.get_symbol("OldName")

        # Rename namespace
        namespace.rename("NewName")
        codebase.ctx.commit_transactions()

        # Verify rename
        namespace: TSNamespace = codebase.get_symbol("NewName")
        assert namespace.name == "NewName"
        assert codebase.get_symbol("NewName") is namespace
        assert codebase.get_symbol("OldName", optional=True) is None


def test_namespace_export_symbol(tmpdir) -> None:
    """Test exporting symbols in namespace."""
    FILE_NAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
    namespace ExportTest {
        export const external = 123;
        const internal = 123;
    }
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME: FILE_CONTENT}) as codebase:
        namespace: TSNamespace = codebase.get_symbol("ExportTest")

        # Export internal symbol
        namespace.export_symbol("internal")
        codebase.ctx.commit_transactions()

        # Verify export
        namespace: TSNamespace = codebase.get_symbol("ExportTest")
        internal = namespace.get_symbol("internal")
        assert internal is not None
        assert all(symbol.is_exported for symbol in namespace.symbols)

        # Export already exported symbol (no change)
        namespace.export_symbol("external")
        codebase.ctx.commit_transactions()

        namespace: TSNamespace = codebase.get_symbol("ExportTest")
        external = namespace.get_symbol("external")
        assert external is not None
        assert external.is_exported


@pytest.mark.skip("TODO: Symbol Animals is ambiguous in codebase - more than one instance")
def test_namespace_merging(tmpdir) -> None:
    """Test TypeScript namespace merging functionality."""
    FILE_NAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
    namespace Animals {
        export class Dog { bark() {} }
    }

    namespace Animals {  // Merge with previous namespace
        export class Cat { meow() {} }
    }

    namespace Plants {  // Different namespace, should not merge
        export class Tree {}
    }
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME: FILE_CONTENT}) as codebase:
        animals = codebase.get_symbol("Animals")
        assert animals is not None

        # Test merged namespace access
        assert animals.get_class("Dog") is not None
        assert animals.get_class("Cat") is not None

        # Verify merged namespaces
        assert len(animals.merged_namespaces) == 1
        merged = animals.merged_namespaces[0]
        assert merged.name == "Animals"
        assert merged != animals

        # Verify all symbols accessible
        all_symbols = animals.symbols
        assert len(all_symbols) == 2
        assert {s.name for s in all_symbols} == {"Dog", "Cat"}

        # Verify non-merged namespace
        plants = codebase.get_symbol("Plants")
        assert len(plants.merged_namespaces) == 0
