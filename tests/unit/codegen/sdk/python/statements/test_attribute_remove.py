from codegen.sdk.codebase.factory.get_session import get_codebase_session


def test_attribute_remove(tmpdir) -> None:
    # language=python
    content = """
class MyClass(ma.Schema):
    a: int
    b: int = 1
    c: OtherClass = OtherClass()
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        cls = file.get_class("MyClass")
        b = cls.get_attribute("b")
        b.remove()
        codebase.commit()

        assert file.content == "\nclass MyClass(ma.Schema):\n    a: int\n    c: OtherClass = OtherClass()\n"
