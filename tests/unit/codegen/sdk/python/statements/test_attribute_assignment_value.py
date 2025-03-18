from codegen.sdk.codebase.factory.get_session import get_codebase_session


def test_attribute_set_assignment_value(tmpdir) -> None:
    # language=python
    content = """
class MyClass:
    a = 1
    b: int
    c = 3
    return a + b + c
"""
    # language=python
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        my_class = file.get_class("MyClass")
        a = my_class.get_attribute("a")
        a.set_value("2")
        b = my_class.get_attribute("b")
        b.set_value("4")
        b.assignment.type.remove()
        c = my_class.get_attribute("c")
        c.value.insert_after(" + a", newline=False)
        c.assignment.set_type_annotation("int")
        codebase.commit()

        assert (
            file.content
            == """
class MyClass:
    a = 2
    b = 4
    c: int = 3 + a
    return a + b + c
"""
        )
