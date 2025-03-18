from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.dataclasses.usage import UsageType
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_namespace_same_file_usage(tmpdir) -> None:
    """Test namespace usage within the same file."""
    # language=typescript
    content = """
    namespace MathUtils {
        export const PI = 3.14159;
        export function square(x: number) { return x * x; }
    }

    function calculateArea(radius: number) {
        return MathUtils.PI * MathUtils.square(radius);
    }
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")

        namespace = file.get_symbol("MathUtils")
        pi = namespace.get_symbol("PI")
        square = namespace.get_symbol("square")
        calc_area = file.get_function("calculateArea")

        # Check if namespace is in valid_import_names
        assert "MathUtils" in file.valid_symbol_names
        assert "MathUtils" in namespace.valid_import_names
        assert len(namespace.valid_import_names) == 3  # MathUtils, PI, and square

        # Check usages
        assert {calc_area}.issubset(namespace.symbol_usages)

        # PI has direct usage (export) and chained usage (in calculateArea)
        assert set(pi.symbol_usages(UsageType.DIRECT)) == {pi.export}
        assert set(pi.symbol_usages(UsageType.CHAINED)) == {calc_area}
        assert set(pi.symbol_usages) == {pi.export, calc_area}

        # square has direct usage (export) and chained usage (in calculateArea)
        assert set(square.symbol_usages(UsageType.DIRECT)) == {square.export}
        assert set(square.symbol_usages(UsageType.CHAINED)) == {calc_area}
        assert set(square.symbol_usages) == {square.export, calc_area}

        # Verify attribute resolution
        assert namespace.resolve_attribute("PI") == pi.export
        assert namespace.resolve_attribute("square") == square.export


def test_namespace_cross_file_usage(tmpdir) -> None:
    """Test namespace usage across files with imports."""
    # language=typescript
    content1 = """
    export namespace MathUtils {
        export const PI = 3.14159;
        export function square(x: number) { return x * x; }
        const internal = 123;  // not exported
    }
    """
    # language=typescript
    content2 = """
    import { MathUtils } from './file1';

    function calculateArea(radius: number) {
        return MathUtils.PI * MathUtils.square(radius);
    }

    function calculateVolume(radius: number) {
        const area = calculateArea(radius);
        return area * radius;
    }
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file1.ts": content1, "file2.ts": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file1 = codebase.get_file("file1.ts")
        file2 = codebase.get_file("file2.ts")

        # Get symbols
        namespace = file1.get_symbol("MathUtils")
        pi = namespace.get_symbol("PI")
        square = namespace.get_symbol("square")
        internal = namespace.get_symbol("internal")
        calc_area = file2.get_function("calculateArea")
        calc_volume = file2.get_function("calculateVolume")
        namespace_import = file2.get_import("MathUtils")

        # Check namespace visibility
        assert "MathUtils" in namespace.valid_import_names
        assert "PI" in namespace.valid_import_names
        assert "square" in namespace.valid_import_names
        assert "internal" not in namespace.valid_import_names
        assert internal is None  # private symbol not accessible

        # Check direct vs chained usages
        assert {namespace.export}.issubset(namespace.symbol_usages(UsageType.DIRECT))
        assert {namespace.export, calc_area}.issubset(namespace.symbol_usages)
        assert {pi.export}.issubset(pi.symbol_usages(UsageType.DIRECT))
        assert {pi.export, calc_area}.issubset(pi.symbol_usages)
        assert {calc_area}.issubset(square.symbol_usages(UsageType.CHAINED))

        # Verify attribute resolution
        assert namespace.resolve_attribute("PI") == pi.export
        assert namespace.resolve_attribute("square") == square.export
        assert namespace.resolve_attribute("internal") is None
