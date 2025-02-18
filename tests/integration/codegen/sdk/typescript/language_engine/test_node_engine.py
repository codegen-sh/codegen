import os

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_node_engine(tmpdir) -> None:
    ts_config = """
{
  "compilerOptions": {
    "target": "es5",
    "module": "commonjs",
    "strict": true
  }
}
"""
    content1 = """
function getUser() {
    return {
        name: 'John',
        age: 30,
        isAdmin: false
    };
}

function calculateArea(width: number, height: number): number {
    return width * height;
}

function getFirstElement<T>(array: T[]): T | null {
    if (array.length === 0) {
        return null;
    }
    return array[0];
}

async function fetchUserData(): Promise<Response> {
    const response = await fetch('https://api.example.com/user');
    return response;
}

function formatName(firstName: string, lastName: string): string {
    return `${firstName} ${lastName}`.trim();
}

function getUserDisplayName() {
    const user = getUser();
    return `${user.name} (${user.age})`;
}

function getSquareArea(size: number) {
    return calculateArea(size, size);
}
"""
    os.chdir(tmpdir)  # TODO: CG-10643
    with get_codebase_session(tmpdir=tmpdir, files={"tsconfig.json": ts_config, "file1.ts": content1}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file1.ts")

        # Manually start the type checker
        # TODO: Make this better
        codebase._enable_experimental_language_engine()

        assert file.get_function("getUser").inferred_return_type == "{ name: string; age: number; isAdmin: boolean; }"
        assert file.get_function("calculateArea").inferred_return_type == "number"
        assert file.get_function("getFirstElement").inferred_return_type == "T | null"
        assert file.get_function("fetchUserData").inferred_return_type == "Promise<Response>"
        assert file.get_function("formatName").inferred_return_type == "string"
        assert file.get_function("getUserDisplayName").inferred_return_type == "string"
        assert file.get_function("getSquareArea").inferred_return_type == "number"
