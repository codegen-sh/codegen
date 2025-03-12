from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_assignment_statement_get_local_usages(tmpdir) -> None:
    # language=typescript
    content = """
class MyClass {
    attr1: string;
    attr2: string;

    foo(): string {
        this.attr1 = "a";
        this.attr2 = "b";
        return this.attr1 + this.attr2;
    }

    bar(): string {
        const attr1: string = this.attr1 + this.attr2;
        return attr1;
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

        bar = cls.get_method("bar")
        attr1 = bar.code_block.get_local_var_assignment("attr1")
        assert len(attr1.local_usages) == 1
