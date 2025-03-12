from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_attribute_set_type_annotation_from_none(tmpdir) -> None:
    # language=typescript
    content = """
class TestClass {
  public attr1;
  public attr2;
  public attr3;

  constructor(
    attr1: string,
    attr2: number,
    attr3: boolean = false
  ) {
    this.attr1 = attr1;
    this.attr2 = attr2;
    this.attr3 = attr3;
  }
}
"""
    # language=typescript
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        cls = file.get_class("TestClass")

        attr1 = cls.get_attribute("attr1")
        attr2 = cls.get_attribute("attr2")
        attr3 = cls.get_attribute("attr3")
        assert not attr1.type
        assert not attr2.type
        assert not attr3.type

        attr1.assignment.set_type_annotation("string")
        attr2.assignment.set_type_annotation("number")
        attr3.assignment.set_type_annotation("boolean")
        codebase.commit()

        cls = file.get_class("TestClass")
        assert cls.get_attribute("attr1").assignment.type.source == "string"
        assert cls.get_attribute("attr2").assignment.type.source == "number"
        assert cls.get_attribute("attr3").assignment.type.source == "boolean"
        assert (
            file.content
            == """
class TestClass {
  public attr1: string;
  public attr2: number;
  public attr3: boolean;

  constructor(
    attr1: string,
    attr2: number,
    attr3: boolean = false
  ) {
    this.attr1 = attr1;
    this.attr2 = attr2;
    this.attr3 = attr3;
  }
}
"""
        )


def test_attribute_set_type_annotation_from_existing(tmpdir) -> None:
    # language=typescript
    content = """
class TestClass {
  public attr1: string;
  public attr2: number;
  public attr3?: boolean;

  constructor(
    attr1: string,
    attr2: number,
    attr3: boolean = false
  ) {
    this.attr1 = attr1;
    this.attr2 = attr2;
    this.attr3 = attr3;
  }
}
"""
    # language=typescript
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        cls = file.get_class("TestClass")

        attr1 = cls.get_attribute("attr1")
        attr2 = cls.get_attribute("attr2")
        attr3 = cls.get_attribute("attr3")
        assert attr1.type.source == "string"
        assert attr2.type.source == "number"
        assert attr3.type.source == "boolean"

        attr1.assignment.set_type_annotation("string[]")
        attr2.assignment.set_type_annotation("number | null")
        attr3.assignment.set_type_annotation("any")
        codebase.commit()

        cls = file.get_class("TestClass")
        assert cls.get_attribute("attr1").assignment.type.source == "string[]"
        assert cls.get_attribute("attr2").assignment.type.source == "number | null"
        assert cls.get_attribute("attr3").assignment.type.source == "any"
        assert (
            file.content
            == """
class TestClass {
  public attr1: string[];
  public attr2: number | null;
  public attr3?: any;

  constructor(
    attr1: string,
    attr2: number,
    attr3: boolean = false
  ) {
    this.attr1 = attr1;
    this.attr2 = attr2;
    this.attr3 = attr3;
  }
}
"""
        )
