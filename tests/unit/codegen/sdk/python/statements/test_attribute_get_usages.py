from codegen.sdk.codebase.factory.get_session import get_codebase_session


def test_attribute_get_local_usages(tmpdir) -> None:
    # language=python
    content = """
class MyClass:
    attr1: str
    attr2: str

    def foo(self):
        self.attr1 = "a"
        self.attr2 = "b"
        return self.attr1 + self.attr2

    def bar(self):
        x = self.attr1 + self.attr2
        return x
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        cls = file.get_class("MyClass")
        attr1 = cls.get_attribute("attr1")
        attr2 = cls.get_attribute("attr2")

        assert len(attr1.local_usages) == 3
        assert len(attr2.local_usages) == 3
