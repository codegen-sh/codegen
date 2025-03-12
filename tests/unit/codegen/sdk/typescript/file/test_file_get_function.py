from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_file_get_function_async_star_function(tmpdir) -> None:
    # language=typescript
    content = """
async function* generator(args: {
    param1: string;
    param2: number;
}) {
    const { param1, param2 } = args;
    yield { param1, param2 };
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        func = file.get_function("generator")
        assert func is not None
        assert func.name == "generator"
