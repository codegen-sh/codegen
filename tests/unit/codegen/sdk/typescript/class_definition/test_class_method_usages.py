from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.detached_symbols.function_call import FunctionCall
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_class_definition_parent_class_names_single(tmpdir) -> None:
    FILENAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
class Point {
  x = 10;
  y = 10;

  scale(n: number): void {
    this.x *= n;
    this.y *= n;
  }
  double(): void {
    this.scale(2);
  }
}
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={FILENAME: FILE_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        point = file.get_symbol("Point")
        scale = point.get_method("scale")
        double = point.get_method("double")
        assert scale.symbol_usages == [double]
        assert len(scale.usages) == 1


def test_class_definition_usages_generic_function(tmpdir) -> None:
    FILENAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
type Constructor<T = {}> = new (...args: any[]) => T;
class Point {
    x = 10;
    y = 10;

    scale(n: number): void {
        this.x *= n;
        this.y *= n;
    }
}
function pop<T>(a: T): T {
    return a;
}
pop(Point).scale(1);
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={FILENAME: FILE_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        point = file.get_symbol("Point")
        scale = point.get_method("scale")
        usage = file.code_block.statements[-1].value
        assert isinstance(usage, FunctionCall)
        assert usage.predecessor.resolved_value == point
        assert len(scale.usages) == 1
        scale.rename("scale2")
    # language=typescript
    assert (
        file.content.strip()
        == """
type Constructor<T = {}> = new (...args: any[]) => T;
class Point {
    x = 10;
    y = 10;

    scale2(n: number): void {
        this.x *= n;
        this.y *= n;
    }
}
function pop<T>(a: T): T {
    return a;
}
pop(Point).scale2(1);
""".strip()
    )


def test_class_definition_usages_generic_class(tmpdir) -> None:
    FILENAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
type Constructor<T = {}> = new (...args: any[]) => T;
class Point {
    x = 10;
    y = 10;

    scale(n: number): void {
        this.x *= n;
        this.y *= n;
    }
}
class List<T> {
    private items: T[] = [];

    pop(): T {
        return this.items.pop();
    }
}
const l: List<Point> = new List();
l.pop().scale(1);
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={FILENAME: FILE_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        point = file.get_symbol("Point")
        scale = point.get_method("scale")
        list = file.get_symbol("List")
        usage = file.code_block.statements[-1].value
        assert isinstance(usage, FunctionCall)
        assert len(list.generics) == 1
        assert usage.predecessor.resolved_value == point
        assert len(scale.usages) == 1
        scale.rename("scale2")
    # language=typescript
    assert (
        file.content.strip()
        == """
type Constructor<T = {}> = new (...args: any[]) => T;
class Point {
    x = 10;
    y = 10;

    scale2(n: number): void {
        this.x *= n;
        this.y *= n;
    }
}
class List<T> {
    private items: T[] = [];

    pop(): T {
        return this.items.pop();
    }
}
const l: List<Point> = new List();
l.pop().scale2(1);
""".strip()
    )


def test_class_definition_usages_stdlib_generic(tmpdir) -> None:
    FILENAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
class Point {
    x = 10;
    y = 10;

    scale(n: number): void {
        this.x *= n;
        this.y *= n;
    }
}
const l: Point[] = [];
l.pop()?.scale(1);
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={FILENAME: FILE_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        point = file.get_symbol("Point")
        scale = point.get_method("scale")
        usage = file.code_block.statements[-1].value
        assert isinstance(usage, FunctionCall)
        assert usage.predecessor.resolved_value == point
        assert len(scale.usages) == 1
        scale.rename("scale2")
    # language=typescript
    assert (
        file.content.strip()
        == """
class Point {
    x = 10;
    y = 10;

    scale2(n: number): void {
        this.x *= n;
        this.y *= n;
    }
}
const l: Point[] = [];
l.pop()?.scale2(1);
""".strip()
    )


def test_class_definition_usages_stdlib_generic_for_loop(tmpdir) -> None:
    FILENAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
class Point {
    x = 10;
    y = 10;

    scale(n: number): void {
        this.x *= n;
        this.y *= n;
    }
}
const l: Point[] = [];
for (const i of l) {
    i.scale(1);
}
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={FILENAME: FILE_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        point = file.get_symbol("Point")
        scale = point.get_method("scale")
        usage = file.code_block.statements[-1].code_block.statements[0].value
        assert isinstance(usage, FunctionCall)
        assert len(scale.usages) == 1
        scale.rename("scale2")
    # language=typescript
    assert (
        file.content.strip()
        == """
class Point {
    x = 10;
    y = 10;

    scale2(n: number): void {
        this.x *= n;
        this.y *= n;
    }
}
const l: Point[] = [];
for (const i of l) {
    i.scale2(1);
}
""".strip()
    )


def test_class_definition_usages_stdlib_generic_dict(tmpdir) -> None:
    FILENAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
class Point {
    x = 10;
    y = 10;

    scale(n: number): void {
        this.x *= n;
        this.y *= n;
    }
}
class Point2 {
    x = 20;
    y = 20;

    scale(n: number): void {
        this.x *= n;
        this.y *= n;
    }
}
const l: Map<Point, Point2> = new Map();
for (const [k, v] of l.entries()) {
    k.scale(1);
    v.scale(1);
}
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={FILENAME: FILE_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        point = file.get_symbol("Point")
        point2 = file.get_symbol("Point2")
        scale = point.get_method("scale")
        scale2 = point2.get_method("scale")
        assert len(scale.usages) == 1
        assert len(scale2.usages) == 1
        scale.rename("scale2")
        scale2.rename("scale3")
    # language=typescript
    assert (
        file.content.strip()
        == """
class Point {
    x = 10;
    y = 10;

    scale2(n: number): void {
        this.x *= n;
        this.y *= n;
    }
}
class Point2 {
    x = 20;
    y = 20;

    scale3(n: number): void {
        this.x *= n;
        this.y *= n;
    }
}
const l: Map<Point, Point2> = new Map();
for (const [k, v] of l.entries()) {
    k.scale2(1);
    v.scale3(1);
}
""".strip()
    )
