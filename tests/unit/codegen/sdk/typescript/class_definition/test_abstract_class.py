from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_abstract_class_inheritance(tmpdir) -> None:
    # language=typescript
    content = """
abstract class OtherClass {
}

abstract class MyClass extends OtherClass {
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        symbol = codebase.get_symbol("MyClass")
        assert "OtherClass" in [x.name for x in symbol.dependencies]


def test_abstract_class_dependencies_private_attribute(tmpdir) -> None:
    # language=typescript
    content = """
import type { TestType } from './types'

abstract class MyClass {
    private readonly originalConfig: TestType;
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        symbol = codebase.get_symbol("MyClass")
        assert "TestType" in [x.name for x in symbol.dependencies]
