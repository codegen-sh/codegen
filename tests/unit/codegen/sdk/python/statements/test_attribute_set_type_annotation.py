from codegen.sdk.codebase.factory.get_session import get_codebase_session


def test_attribute_set_type_annotation_from_none(tmpdir) -> None:
    # language=python
    content = """
import marshmallow as ma

class MySchema(ma.Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)
    boolean_field = fields.Boolean()
    my_custom_field = fields.Boolean(default=False)
"""
    # language=python
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        cls = file.get_class("MySchema")

        id = cls.get_attribute("id")
        name = cls.get_attribute("name")
        my_custom_field = cls.get_attribute("my_custom_field")
        assert not id.assignment.type
        assert not name.assignment.type
        assert not my_custom_field.assignment.type

        id.assignment.set_type_annotation("int")
        name.assignment.set_type_annotation("str")
        my_custom_field.assignment.set_type_annotation("bool")
        codebase.commit()

        cls = file.get_class("MySchema")
        assert cls.get_attribute("id").assignment.type.source == "int"
        assert cls.get_attribute("name").assignment.type.source == "str"
        assert cls.get_attribute("my_custom_field").assignment.type.source == "bool"
        assert (
            file.content
            == """
import marshmallow as ma

class MySchema(ma.Schema):
    id: int = fields.String(required=True)
    name: str = fields.String(required=True)
    boolean_field = fields.Boolean()
    my_custom_field: bool = fields.Boolean(default=False)
"""
        )


def test_attribute_set_type_annotation_from_existing(tmpdir) -> None:
    # language=python
    content = """
import marshmallow as ma

class MySchema(ma.Schema):
    id: int = 0
    name: str = ["a", "b"]
    boolean_field = fields.Boolean()
    my_custom_field: bool = fields.Boolean(default=False)
"""
    # language=python
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        cls = file.get_class("MySchema")

        cls.get_attribute("id").assignment.set_type_annotation("str")
        cls.get_attribute("name").assignment.set_type_annotation("list[str]")
        cls.get_attribute("my_custom_field").assignment.set_type_annotation("int")
        codebase.commit()

        cls = file.get_class("MySchema")
        assert cls.get_attribute("id").assignment.type.source == "str"
        assert cls.get_attribute("name").assignment.type.source == "list[str]"
        assert cls.get_attribute("my_custom_field").assignment.type.source == "int"
        assert (
            file.content
            == """
import marshmallow as ma

class MySchema(ma.Schema):
    id: str = 0
    name: list[str] = ["a", "b"]
    boolean_field = fields.Boolean()
    my_custom_field: int = fields.Boolean(default=False)
"""
        )
