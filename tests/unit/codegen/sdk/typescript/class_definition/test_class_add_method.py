from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.typescript.class_definition import TSClass
    from codegen.sdk.typescript.file import TSFile


def test_add_method_basic(tmpdir) -> None:
    # language=typescript
    content = """
class Abc {
    static foo(a: number, b: number, c: number): number {
        return a + b + c;
    }
}
"""
    # language=typescript
    content2 = """
static test(): void {
    foo(1, 2, 3);
}
"""

    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        foo = file.get_class("Abc")
        foo.methods.append(content2)

    # language=typescript
    assert (
        file.content
        == """
class Abc {
    static foo(a: number, b: number, c: number): number {
        return a + b + c;
    }

    static test(): void {
        foo(1, 2, 3);
    }
}
"""
    )


def test_add_method_after_method_with_docstring(tmpdir) -> None:
    # language=typescript
    content = """
class Abc {
    /**
     * Adds three numbers.
     *
     * @param a - The first number.
     * @param b - The second number.
     * @param c - The third number.
     * @returns The sum of the three numbers.
     */
    static foo(a: number, b: number, c: number): number {
        return a + b + c;
    }
}
"""
    # language=typescript
    content2 = """
static test(): void {
    foo(1, 2, 3);
}
"""

    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        foo = file.get_class("Abc")
        foo.methods.append(content2)

    # language=typescript
    assert (
        file.content
        == """
class Abc {
    /**
     * Adds three numbers.
     *
     * @param a - The first number.
     * @param b - The second number.
     * @param c - The third number.
     * @returns The sum of the three numbers.
     */
    static foo(a: number, b: number, c: number): number {
        return a + b + c;
    }

    static test(): void {
        foo(1, 2, 3);
    }
}
"""
    )


def test_add_method_multiple_times(tmpdir) -> None:
    # language=typescript
    content = """
class Abc {
    static foo(a: number, b: number, c: number): number {
        return a + b + c;
    }
}
"""
    # language=typescript
    content2 = """
static test(): void {
    foo(1, 2, 3);
}
"""
    # language=typescript
    content3 = """
static test2(): void {
    foo(4, 5, 6);
}
"""

    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        foo = file.get_class("Abc")
        foo.methods.append(content2)
        foo.methods.append(content3)

    # language=typescript
    assert (
        file.content
        == """
class Abc {
    static foo(a: number, b: number, c: number): number {
        return a + b + c;
    }

    static test(): void {
        foo(1, 2, 3);
    }

    static test2(): void {
        foo(4, 5, 6);
    }
}
"""
    )


def test_add_method_out_of_order(tmpdir) -> None:
    # language=typescript
    content = """
class Abc {
    static foo(a: number, b: number, c: number): number {
        return a + b + c;
    }
}
"""
    # language=typescript
    content2 = """
static test2(): void {
    foo(1, 2, 3);
}
"""
    # language=typescript
    content3 = """
static test3(): void {
    foo(4, 5, 6);
}
"""
    # language=typescript
    content4 = """
static test4(): void {
    foo(7, 8, 9);
}
"""

    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        foo = file.get_class("Abc")
        foo.methods.insert(0, content2)
        foo.methods.insert(2, content3)
        foo.methods.insert(0, content4)

    # language=typescript
    assert (
        file.content
        == """
class Abc {

    static test4(): void {
        foo(7, 8, 9);
    }

    static test2(): void {
        foo(1, 2, 3);
    }

    static foo(a: number, b: number, c: number): number {
        return a + b + c;
    }

    static test3(): void {
        foo(4, 5, 6);
    }
}
"""
    )


def test_add_first_method_with_no_methods(tmpdir) -> None:
    # language=typescript
    content = """
@decorator
class Abc {
    attr: string = "test";
}
"""
    # language=typescript
    new_method = """
static test2(): void {
    foo(1, 2, 3);
}
"""

    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        foo = file.get_class("Abc")
        foo.methods.append(new_method)

    # language=typescript
    assert (
        file.content
        == """
@decorator
class Abc {
    attr: string = "test";

    static test2(): void {
        foo(1, 2, 3);
    }
}
"""
    )


def test_append_multiple_method_with_no_methods(tmpdir) -> None:
    # language=typescript
    content = """
@decorator
class Abc {
    attr: string = "test";
}
"""
    # language=typescript
    content2 = """
static test2(): void {
    foo(1, 2, 3);
}
"""
    # language=typescript
    content3 = """
static test3(): void {
    foo(2, 3, 4);
}
"""
    # language=typescript
    content4 = """
static test4(): void {
    foo(4, 5, 6);
}
"""

    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        foo = file.get_class("Abc")
        foo.methods.append(content2)
        foo.methods.append(content3)
        foo.methods.append(content4)

    # language=typescript
    assert (
        file.content
        == """
@decorator
class Abc {
    attr: string = "test";

    static test2(): void {
        foo(1, 2, 3);
    }

    static test3(): void {
        foo(2, 3, 4);
    }

    static test4(): void {
        foo(4, 5, 6);
    }
}
"""
    )


def test_insert_multiple_method_with_no_methods(tmpdir) -> None:
    # language=typescript
    content = """
@decorator
class Abc {
    attr: string = "test";
}
"""
    # language=typescript
    content2 = """
static test2(): void {
    foo(1, 2, 3);
}
"""
    # language=typescript
    content3 = """
static test3(): void {
    foo(2, 3, 4);
}
"""
    # language=typescript
    content4 = """
static test4(): void {
    foo(4, 5, 6);
}
"""

    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        foo = file.get_class("Abc")
        foo.methods.append(content2)
        foo.methods.insert(0, content3)
        foo.methods.insert(0, content4)

    # language=typescript
    assert (
        file.content
        == """
@decorator
class Abc {
    attr: string = "test";

    static test4(): void {
        foo(4, 5, 6);
    }

    static test3(): void {
        foo(2, 3, 4);
    }

    static test2(): void {
        foo(1, 2, 3);
    }
}
"""
    )


def test_insert_methods_out_of_order_with_no_methods(tmpdir) -> None:
    # language=typescript
    content = """
@decorator
class Abc {
    attr: string = "test";
}
"""
    # language=typescript
    content2 = """
static test2(): void {
    foo(1, 2, 3);
}
"""
    # language=typescript
    content3 = """
static test3(): void {
    foo(2, 3, 4);
}
"""
    # language=typescript
    content4 = """
static test4(): void {
    foo(4, 5, 6);
}
"""

    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        foo = file.get_class("Abc")
        foo.methods.insert(2, content2)
        foo.methods.insert(0, content3)
        foo.methods.insert(1, content4)

    # language=typescript
    assert (
        file.content
        == """
@decorator
class Abc {
    attr: string = "test";

    static test3(): void {
        foo(2, 3, 4);
    }

    static test4(): void {
        foo(4, 5, 6);
    }

    static test2(): void {
        foo(1, 2, 3);
    }
}
"""
    )


def test_add_method_with_symbol(tmpdir) -> None:
    # language=typescript
    content = """
class Abc {
    static foo(a: number, b: number, c: number): number {
        return a + b + c;
    }
}
"""
    # language=typescript
    content2 = """
class Efg {
    static test(): void {
        this.foo(1, 2, 3);
    }
}
"""

    with get_codebase_session(tmpdir=tmpdir, files={"file1.ts": content, "file2.ts": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file1: TSFile = codebase.get_file("file1.ts")
        file2: TSFile = codebase.get_file("file2.ts")
        abc = file1.get_class("Abc")
        efg: TSClass = file2.get_class("Efg")
        abc.methods.append(efg.get_method("test"))

    # language=typescript
    assert (
        file1.content
        == """
class Abc {
    static foo(a: number, b: number, c: number): number {
        return a + b + c;
    }

    static test(): void {
        this.foo(1, 2, 3);
    }
}
"""
    )
