from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_rename_function_updates_file_content(tmpdir) -> None:
    # language=typescript
    file = """
function foo(bar: number): number {
    return bar;
}

function baz(): number {
    return foo(1) + foo(1);
}
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as codebase:
        file = codebase.get_file("test.ts")
        symbol = file.get_symbol("foo")
        symbol.rename("XYZ")

    assert "function XYZ(" in file.content
    assert "return XYZ(1) + XYZ(1)" in file.content


def test_rename_function_updates_import_dependencies(tmpdir) -> None:
    DEF_FILENAME = "file_with_symbol_def.ts"
    # language=typescript
    DEF_FILE_CONTENT_INPUT = """
export function greet(name: string): string {
  return `Hello, ${name}!`;
}

export function introduce(name: string, age: number): string {
  const greeting = greet(name);
  return `${greeting} I am ${age} years old.`;
}
"""
    # language=typescript
    DEF_FILE_CONTENT_EXPECTED_OUTPUT = """
export function offender(name: string): string {
  return `Hello, ${name}!`;
}

export function introduce(name: string, age: number): string {
  const greeting = offender(name);
  return `${greeting} I am ${age} years old.`;
}
"""

    USAGE_FILENAME = "file_with_symbol_usage.ts"
    # language=typescript
    USAGE_FILE_CONTENT_INPUT = """
import { greet, introduce } from './file_with_symbol_def';

function main() {
  const name = 'John';
  const age = 25;

  const greeting = greet(name);
  console.log(greeting);

  const introduction = introduce(name, age);
  console.log(introduction);
}
"""
    # language=typescript
    USAGE_FILE_CONTENT_EXPECTED_OUTPUT = """
import { offender, introduce } from './file_with_symbol_def';

function main() {
  const name = 'John';
  const age = 25;

  const greeting = offender(name);
  console.log(greeting);

  const introduction = introduce(name, age);
  console.log(introduction);
}
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={DEF_FILENAME: DEF_FILE_CONTENT_INPUT, USAGE_FILENAME: USAGE_FILE_CONTENT_INPUT}) as codebase:
        symbol_for_rename = codebase.get_symbol("greet")
        symbol_for_rename.rename("offender")

    assert codebase.get_file(DEF_FILENAME).content == DEF_FILE_CONTENT_EXPECTED_OUTPUT
    assert codebase.get_file(USAGE_FILENAME).content == USAGE_FILE_CONTENT_EXPECTED_OUTPUT
