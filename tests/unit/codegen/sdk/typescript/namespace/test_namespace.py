from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.typescript.namespace import TSNamespace
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_empty_namespace(tmpdir) -> None:
    """Test basic empty namespace declaration."""
    FILE_NAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
    namespace MyNamespace {} // not exported
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME: FILE_CONTENT}) as codebase:
        file = codebase.get_file(FILE_NAME)
        namespace: TSNamespace = codebase.get_symbol("MyNamespace")
        assert namespace is not None
        assert namespace.name == "MyNamespace"

    # Test exported namespace
    # language=typescript
    FILE_CONTENT = """
    export namespace MyNamespace {} // exported
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME: FILE_CONTENT}) as codebase:
        file = codebase.get_file(FILE_NAME)
        namespace: TSNamespace = codebase.get_symbol("MyNamespace")
        assert namespace is not None
        assert namespace.name == "MyNamespace"


def test_basic_namespace_creation(tmpdir) -> None:
    """Test basic namespace creation and properties."""
    FILE_NAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
    namespace SimpleNamespace {
        export const x = 1;
    }
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME: FILE_CONTENT}) as codebase:
        namespace: TSNamespace = codebase.get_symbol("SimpleNamespace")
        assert namespace is not None
        assert namespace.name == "SimpleNamespace"
        assert len(namespace.symbols) == 1


def test_namespace_basic_symbols(tmpdir) -> None:
    """Test basic symbol access and visibility in namespace."""
    FILE_NAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
    namespace BasicSymbols {
        export const constVar = 1;
        export let letVar = 2;
        const privateVar = 3;
    }
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME: FILE_CONTENT}) as codebase:
        namespace = codebase.get_symbol("BasicSymbols")
        assert namespace is not None

        # Test basic symbol access
        assert namespace.get_symbol("constVar") is not None
        assert namespace.get_symbol("letVar") is not None
        assert namespace.get_symbol("privateVar") is None  # private not accessible

        # Test symbols collection
        assert len(namespace.symbols) == 3


def test_namespace_recursive_symbol_lookup(tmpdir) -> None:
    """Test recursive vs non-recursive symbol lookup."""
    FILE_NAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
    namespace Root {
        export const rootSymbol = 1;
        export namespace Level1 {
            export const level1Symbol = 2;
            export namespace Level2 {
                export const level2Symbol = 3;
            }
        }
    }
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME: FILE_CONTENT}) as codebase:
        root = codebase.get_symbol("Root")

        # Test non-recursive lookup
        assert root.get_symbol("rootSymbol", recursive=False) is not None
        assert root.get_symbol("level1Symbol", recursive=False) is None
        assert root.get_symbol("level2Symbol", recursive=False) is None

        # Test recursive lookup
        assert root.get_symbol("rootSymbol", recursive=True) is not None
        assert root.get_symbol("level1Symbol", recursive=True) is not None
        assert root.get_symbol("level2Symbol", recursive=True) is not None


def test_namespace_functions(tmpdir) -> None:
    """Test function-related namespace APIs."""
    FILE_NAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
    namespace Functions {
        export function func1() { return 1; }
        export function func2() { return 2; }
        function privateFunc() { return 3; }  // not exported
    }
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME: FILE_CONTENT}) as codebase:
        namespace: TSNamespace = codebase.get_symbol("Functions")

        # Test get_function
        assert namespace.get_function("func1") is not None
        assert namespace.get_function("func2") is not None
        assert namespace.get_function("privateFunc") is None

        # Test functions property
        assert len(namespace.functions) == 2
        function_names = {f.name for f in namespace.functions}
        assert function_names == {"func1", "func2"}
        assert all(func.is_exported for func in namespace.functions)


def test_namespace_function_full_name(tmpdir) -> None:
    """Test getting functions using full names."""
    FILE_NAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
    namespace Outer {
        export function shared() { return 1; }
        export namespace Inner {
            export function shared() { return 2; }
            export function unique() { return 3; }
        }
    }
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME: FILE_CONTENT}) as codebase:
        namespace: TSNamespace = codebase.get_symbol("Outer")
        assert namespace is not None

        # Test getting functions by local name
        outer_shared = namespace.get_function("shared", recursive=False)
        assert outer_shared is not None
        inner_shared = namespace.get_function("shared", recursive=True)
        assert inner_shared is not None
        # Without full names, we might get either shared function
        assert outer_shared == inner_shared

        # Test getting functions by full name
        outer_shared = namespace.get_function("shared", use_full_name=True)
        assert outer_shared is not None
        inner_shared = namespace.get_function("Inner.shared", use_full_name=True)
        assert inner_shared is not None
        inner_unique = namespace.get_function("Inner.unique", use_full_name=True)
        assert inner_unique is not None

        # Test non-existent paths
        assert namespace.get_function("NonExistent.shared", use_full_name=True) is None
        assert namespace.get_function("Inner.NonExistent", use_full_name=True) is None


def test_namespace_function_overloading(tmpdir) -> None:
    """Test function overloading within namespace."""
    FILE_NAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
    namespace Math {
        export function calculate(operation: "add", a: number, b: number): number;
        export function calculate(operation: "multiply", a: number, b: number): number;
        export function calculate(operation: string, a: number, b: number): number {
            switch (operation) {
                case "add": return a + b;
                case "multiply": return a * b;
                default: throw new Error(`Operation "${operation}" not supported`);
            }
        }
    }
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME: FILE_CONTENT}) as codebase:
        namespace = codebase.get_symbol("Math")
        calculate = namespace.get_function("calculate")
        assert calculate is not None
        assert calculate.is_exported


def test_namespace_classes(tmpdir) -> None:
    """Test class access and collection in namespace."""
    FILE_NAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
    namespace Classes {
        export class Calculator {
            multiply(a: number, b: number): number {
                return a * b;
            }
        }
        class PrivateClass {}
    }
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME: FILE_CONTENT}) as codebase:
        namespace = codebase.get_symbol("Classes")

        # Test class access
        calc = namespace.get_class("Calculator")
        assert calc is not None
        assert calc.is_exported
        assert namespace.get_class("PrivateClass") is None

        # Test classes collection
        assert len(namespace.classes) == 1
        assert all(cls.is_exported for cls in namespace.classes)


def test_namespace_interfaces(tmpdir) -> None:
    """Test interface access in namespace."""
    FILE_NAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
    namespace Interfaces {
        export interface Operation {
            execute(a: number, b: number): number;
        }
        interface PrivateInterface {}
    }
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME: FILE_CONTENT}) as codebase:
        namespace = codebase.get_symbol("Interfaces")

        # Test interface access
        operation = namespace.get_interface("Operation")
        assert operation is not None
        assert operation.is_exported
        assert namespace.get_interface("PrivateInterface") is None


def test_namespace_types(tmpdir) -> None:
    """Test type alias access in namespace."""
    FILE_NAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
    namespace Types {
        export type NumberPair = [number, number];
        type PrivateType = string;
    }
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME: FILE_CONTENT}) as codebase:
        namespace = codebase.get_symbol("Types")

        # Test type access
        number_pair = namespace.get_type("NumberPair")
        assert number_pair is not None
        assert number_pair.is_exported
        assert namespace.get_type("PrivateType") is None


def test_namespace_enums(tmpdir) -> None:
    """Test enum access in namespace."""
    FILE_NAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
    namespace Enums {
        export enum Operation {
            Add,
            Subtract,
            Multiply
        }
        enum PrivateEnum { A, B }
    }
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME: FILE_CONTENT}) as codebase:
        namespace = codebase.get_symbol("Enums")

        # Test enum access
        operation = namespace.get_enum("Operation")
        assert operation is not None
        assert operation.is_exported
        assert namespace.get_enum("PrivateEnum") is None


def test_namespace_nested_basic(tmpdir) -> None:
    """Test basic nested namespace functionality."""
    FILE_NAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
    namespace Math {
        export namespace Advanced {
            export const PI = 3.14159;
        }
    }
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME: FILE_CONTENT}) as codebase:
        math = codebase.get_symbol("Math")
        advanced = math.get_namespace("Advanced")
        assert advanced is not None
        assert advanced.is_exported
        assert advanced.get_symbol("PI") is not None


def test_namespace_nested_deep(tmpdir) -> None:
    FILE_NAME = "test.ts"
    FILE_CONTENT = """
    namespace A {
        export namespace B {
            export namespace C {
                export const x = 1;
            }
        }
        export const x = 2;
    }
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME: FILE_CONTENT}) as codebase:
        namespace_a: TSNamespace = codebase.get_symbol("A")
        assert namespace_a is not None

        # Test deeply nested symbol access
        namespace_b: TSNamespace = namespace_a.get_namespace("B")
        assert namespace_b is not None
        namespace_c: TSNamespace = namespace_b.get_namespace("C")
        assert namespace_c is not None

        # Test symbol shadowing
        x_in_c = namespace_c.get_symbol("x")
        x_in_a = namespace_a.get_symbol("x")
        assert x_in_c is not None
        assert x_in_a is not None
        assert x_in_c is x_in_a

        # Test get_nested_namespaces
        nested = namespace_a.get_nested_namespaces()
        assert len(nested) == 2  # Should find B and C
        assert all(isinstance(ns, TSNamespace) for ns in nested)
        assert {ns.name for ns in nested} == {"B", "C"}


def test_namespace_imports(tmpdir) -> None:
    """Test importing and using namespaces."""
    FILE_NAME_1 = "math.ts"
    # language=typescript
    FILE_CONTENT_1 = """
    export namespace Math {
        export const PI = 3.14159;
        export function square(x: number) { return x * x; }

        export namespace Advanced {
            export function cube(x: number) { return x * x * x; }
        }
    }
    """

    FILE_NAME_2 = "app.ts"
    # language=typescript
    FILE_CONTENT_2 = """
    import { Math } from './math';

    console.log(Math.PI);
    console.log(Math.square(5));
    console.log(Math.Advanced.cube(3));
    """

    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME_1: FILE_CONTENT_1, FILE_NAME_2: FILE_CONTENT_2}) as codebase:
        math_ns = codebase.get_symbol("Math")
        assert math_ns is not None
        assert math_ns.name == "Math"

        # Test namespace import resolution
        file2 = codebase.get_file(FILE_NAME_2)
        math_import = file2.get_import("Math")
        assert math_import is not None
        assert math_import.is_namespace_import

        # Test nested namespace access
        advanced = math_ns.get_namespace("Advanced")
        assert advanced is not None
        assert advanced.name == "Advanced"
        assert advanced.get_function("cube") is not None
