import os

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_add_symbol_to_file_with_comments(tmpdir) -> None:
    FILE_NAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """/**
* Returns the docstring of the function
* @param param1 The first parameter
* @param param2 The second parameter
*/
function doAthing(): ReturnValue[] {
return []
}
"""
    TARGET_FILE = "target.ts"
    # language=typescript
    TARGET_FILE_CONTENT = """"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME: FILE_CONTENT, TARGET_FILE: TARGET_FILE_CONTENT}, commit=True) as codebase:
        file = codebase.get_file(FILE_NAME)
        target_file = codebase.get_file(TARGET_FILE)
        func = file.get_function("doAthing")
        target_file.add_symbol(symbol=func, should_export=False)

    with open(os.path.join(tmpdir, TARGET_FILE)) as f:
        content = f.read()
        assert content.strip() == FILE_CONTENT.strip()


def test_add_symbol_to_file_with_comments_add_export(tmpdir) -> None:
    FILE_NAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """/**
* Returns the docstring of the function
* @param param1 The first parameter
* @param param2 The second parameter
*/
function doAthing(): ReturnValue[] {
return []
}
"""
    TARGET_FILE = "target.ts"
    # language=typescript
    TARGET_FILE_CONTENT = """"""
    # language=typescript
    EXPECTED_FILE_CONTENT = """/**
* Returns the docstring of the function
* @param param1 The first parameter
* @param param2 The second parameter
*/
export function doAthing(): ReturnValue[] {
return []
}
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME: FILE_CONTENT, TARGET_FILE: TARGET_FILE_CONTENT}, commit=True) as codebase:
        file = codebase.get_file(FILE_NAME)
        target_file = codebase.get_file(TARGET_FILE)
        func = file.get_function("doAthing")
        target_file.add_symbol(symbol=func, should_export=True)

    with open(os.path.join(tmpdir, TARGET_FILE)) as f:
        content = f.read()
        assert content.strip() == EXPECTED_FILE_CONTENT.strip()
