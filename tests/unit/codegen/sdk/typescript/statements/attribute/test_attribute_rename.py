from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_attribute_rename(tmpdir) -> None:
    # language=typescript
    content1 = """
import { OtherClass } from './file2'

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
class OtherClass {
    constructor() {
        pass
    }
}
    """
    # language=typescript
    with get_codebase_session(tmpdir=tmpdir, files={"file1.ts": content1, "file2.ts": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file1.ts")
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
import { OtherClass } from './file2'

class MyClass {
    new_a: int;
    new_b: int = 1;
    new_c: OtherClass = OtherClass();

    constructor(x: int, y: int, z: int) {
        this.new_a = x + y + z
    }
}
"""
        )
