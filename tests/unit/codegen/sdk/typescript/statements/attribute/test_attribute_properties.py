from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.detached_symbols.function_call import FunctionCall
from codegen.sdk.core.expressions.number import Number
from codegen.sdk.typescript.statements.assignment_statement import TSAssignmentStatement
from codegen.sdk.typescript.statements.attribute import TSAttribute
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_attribute(tmpdir) -> None:
    # language=typescript
    content1 = """
import OtherClass from "./file2"

class MyClass {
    a: int;
    b: int = 1;
    c: OtherClass = OtherClass();

    constructor(x: int, y: int, z: int) {
        this.a = x + y + z
    }
}
"""
    # language=typescript
    content2 = """
export default class OtherClass {
    constructor() {
        pass
    }
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"file1.ts": content1, "file2.ts": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file1.ts")
        cls = file.get_class("MyClass")
        a = cls.get_attribute("a")
        b = cls.get_attribute("b")
        c = cls.get_attribute("c")

        assert a.assignment.type.source == "int"
        assert a.left.source == a.name
        assert a.name == "a"
        assert a.assignment.value is None

        assert b.assignment.type.source == "int"
        assert b.left.source == b.name
        assert b.name == "b"
        assert isinstance(b.assignment.value, Number)
        assert b.assignment.value.source == "1"

        assert c.assignment.type.source == "OtherClass"
        assert c.left.source == c.name
        assert c.name == "c"
        assert isinstance(c.assignment.value, FunctionCall)
        assert c.assignment.value.source == "OtherClass()"
        assert c.assignment.value.function_definition.file.name == "file2"


def test_attributes_with_comments(tmpdir) -> None:
    # language=typescript
    content = """
/**
* Some comment
*/
class A {
    b: int = 1;  // comment
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        symbol = file.get_class("A")
        attrs = symbol.attributes
        assert len(attrs) == 1
        assert attrs[0].name == "b"


def test_attribute_from_code_block(tmpdir) -> None:
    # language=typescript
    content = """
class MyClass {
    a: int;
    b: int = 1;
    c: OtherClass = OtherClass();

    constructor(x: int, y: int, z: int) {
        this.a = x + y + z
    }
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        cls = file.get_class("MyClass")

        b = cls.get_attribute("b")
        assert b.parent.parent.parent == cls
        assert isinstance(b, TSAttribute)
        assert isinstance(b, TSAssignmentStatement)
        assert b.file_node_id == cls.file_node_id
        assert b.ctx == cls.ctx


def test_attribute_from_parent_symbol(tmpdir) -> None:
    # language=typescript
    content = """
type MyType = {
    a: int;
    b: int;
    c: OtherClass;
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        type = file.get_type("MyType")

        b = type.get_attribute("b")
        assert b.parent.parent.parent == type
        assert isinstance(b, TSAttribute)
        assert isinstance(b, TSAssignmentStatement)
        assert b.file_node_id == type.file_node_id
        assert b.ctx == type.ctx


def test_ts_attributes_within_function(tmpdir) -> None:
    # language=typescript
    content = """
class MyClass {
    a: int = 1;

    constructor() {
        pass
    }

    myFunction() {
        const b = 1;
    }
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        cls = file.get_class("MyClass")
        attributes = cls.attributes
        assert len(attributes) == 1
