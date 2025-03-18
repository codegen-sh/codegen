from codegen.sdk.codebase.factory.get_session import get_codebase_session


def test_attribute_rename(tmpdir) -> None:
    # language=python
    content1 = """
import marshmallow as ma
from file2 import OtherClass

class MyClass(ma.Schema):
    a: int
    b: int = 1
    c: OtherClass = OtherClass()

    def __init__(self, x, y, z):
        self.a = x + y + z
"""
    # language=python
    content2 = """
class OtherClass:
    def __init__(self):
        pass
    """
    # language=python
    with get_codebase_session(tmpdir=tmpdir, files={"file1.py": content1, "file2.py": content2}) as codebase:
        file = codebase.get_file("file1.py")
        cls = file.get_class("MyClass")

        cls.get_attribute("a").rename("new_a")
        cls.get_attribute("b").rename("new_b")
        cls.get_attribute("c").rename("new_c")
        codebase.commit()

        cls = file.get_class("MyClass")
        assert cls.get_attribute("new_a") is not None
        assert cls.get_attribute("new_b") is not None
        assert cls.get_attribute("new_c") is not None
        assert (
            file.content
            == """
import marshmallow as ma
from file2 import OtherClass

class MyClass(ma.Schema):
    new_a: int
    new_b: int = 1
    new_c: OtherClass = OtherClass()

    def __init__(self, x, y, z):
        self.new_a = x + y + z
"""
        )
