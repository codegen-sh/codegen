from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_class_definition_add_attribute_from_source(tmpdir) -> None:
    # language=typescript
    src_content = """
class A {
  a: number;
  b: number;
  constructor(a: number, b: number) {
    this.a = a;
    this.b = b;
  }
}
"""

    with get_codebase_session(tmpdir=tmpdir, files={"src.ts": src_content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        src_file = codebase.get_file("src.ts")
        A = src_file.get_class("A")
        A.add_attribute_from_source("c: number;")
    # language=typescript
    assert (
        src_file.content
        == """
class A {
  a: number;
  b: number;
  c: number;
  constructor(a: number, b: number) {
    this.a = a;
    this.b = b;
  }
}
"""
    )


def test_class_definition_add_source_with_existing_attr(tmpdir) -> None:
    # language=typescript
    content = """
class Foo {
    property = "property";

    constructor(name: string, age: number, email: string, id: number) {
        this.name = name;
        this.age = age;
        this.email = email;
        this.id = id;
        Person.count++;
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        symbol = file.get_class("Foo")
        symbol.add_attribute_from_source("property2 = 'property2';")

    # language=typescript
    assert (
        file.content
        == """
class Foo {
    property = "property";
    property2 = 'property2';

    constructor(name: string, age: number, email: string, id: number) {
        this.name = name;
        this.age = age;
        this.email = email;
        this.id = id;
        Person.count++;
    }
}
    """
    )


def test_class_definition_add_source_with_no_attr(tmpdir) -> None:
    # language=typescript
    content = """
class Foo {
    constructor(name: string, age: number, email: string, id: number) {
        this.name = name;
        this.age = age;
        this.email = email;
        this.id = id;
        Person.count++;
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        symbol = file.get_class("Foo")
        symbol.add_attribute_from_source('property = "property";')

    # language=typescript
    assert (
        file.content
        == """
class Foo {
    property = "property";

    constructor(name: string, age: number, email: string, id: number) {
        this.name = name;
        this.age = age;
        this.email = email;
        this.id = id;
        Person.count++;
    }
}
    """
    )


def test_class_definition_add_source_with_empty_class(tmpdir) -> None:
    # language=typescript
    content = """
class Foo {
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        symbol = file.get_class("Foo")
        symbol.add_attribute_from_source('property = "property";')

    # language=typescript
    assert (
        file.content
        == """
class Foo {
    property = "property";
}
    """
    )
