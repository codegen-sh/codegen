from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_attribute_get_local_usages(tmpdir) -> None:
    # language=typescript
    content = """
class MyClass {
    private attr1: string;
    private attr2: string;

    public foo(): string {
        this.attr1 = "a";
        this.attr2 = "b";
        return this.attr1 + this.attr2;
    }

    public bar(): string {
        let x: string = this.attr1 + this.attr2;
        return x;
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as codebase:
        file = codebase.get_file("test.ts")
        cls = file.get_class("MyClass")
        attr1 = cls.get_attribute("attr1")
        attr2 = cls.get_attribute("attr2")

        assert len(attr1.local_usages) == 3
        assert len(attr2.local_usages) == 3
