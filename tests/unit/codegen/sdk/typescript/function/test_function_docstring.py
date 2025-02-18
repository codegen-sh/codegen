from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_function_docstring_multiline(tmpdir) -> None:
    FILENAME = "function_test.ts"
    # language=typescript
    FILE_CONTENT = """
/**
 * This is a docstring
*/
function foo() {
    // Function Body
}

/**
* This is a multiline docstring
* @param
* @return
*/
function bar() {
    // Function Body
}
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILENAME: FILE_CONTENT}) as codebase:
        function_symbol = codebase.get_symbol("foo")
        assert "This is a docstring" in function_symbol.docstring.text
        assert "foo" not in function_symbol.docstring.text
        assert "Function Body" not in function_symbol.docstring.text

        function_symbol = codebase.get_symbol("bar")
        assert "This is a multiline docstring" in function_symbol.docstring.text
        assert "@param" in function_symbol.docstring.text
        assert "@return" in function_symbol.docstring.text
        assert "foo" not in function_symbol.docstring.text
        assert "Function Body" not in function_symbol.docstring.text


def test_function_docstring_function_with_parameters(tmpdir) -> None:
    # language=typescript
    comment = """
/**
* Returns the docstring of the function
* @param param1 The first parameter
* @param param2 The second parameter
*/
"""
    FILE_NAME = "test.ts"
    FILE_CONTENT = f"""
{comment.strip()}
export function doAthing(param1: string, param2: number): ReturnValue[] {{
    return []
}}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME: FILE_CONTENT}) as codebase:
        file = codebase.get_file(FILE_NAME)
        func = file.get_function("doAthing")
        assert func.docstring.text == comment.replace("/**", "").replace("*/", "").replace("* ", "").replace("// ", "").strip()


def test_function_docstring_async(tmpdir) -> None:
    # language=typescript
    comment = """
/**
* Returns the docstring of the function
*/
"""
    FILE_NAME = "test.ts"
    FILE_CONTENT = f"""
{comment.strip()}
export async function doAthing(
): Promise<ReturnValue[]> {{
return []
}}
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME: FILE_CONTENT}) as codebase:
        file = codebase.get_file(FILE_NAME)
        func = file.get_function("doAthing")
        assert func.docstring.text == comment.replace("/**", "").replace("*/", "").replace("* ", "").replace("// ", "").strip()


def test_function_docstring_non_async(tmpdir) -> None:
    # language=typescript
    comment = """
/**
* Returns the docstring of the function
*/
"""
    FILE_NAME = "test.ts"
    FILE_CONTENT = f"""
{comment.strip()}
export function doAthing(): ReturnValue[] {{
return []
}}
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME: FILE_CONTENT}) as codebase:
        file = codebase.get_file(FILE_NAME)
        func = file.get_function("doAthing")
        assert func.docstring.text == comment.replace("/**", "").replace("*/", "").replace("* ", "").replace("// ", "").strip()


def test_function_docstring_not_exported(tmpdir) -> None:
    # language=typescript
    comment = """
/**
* Returns the docstring of the function
*/
"""
    FILE_NAME = "test.ts"
    FILE_CONTENT = f"""
{comment.strip()}
function doAthing(): ReturnValue[] {{
return []
}}
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME: FILE_CONTENT}) as codebase:
        file = codebase.get_file(FILE_NAME)
        func = file.get_function("doAthing")
        assert func.docstring.text == comment.replace("/**", "").replace("*/", "").replace("* ", "").replace("// ", "").strip()


def test_function_docstring_no_comments(tmpdir) -> None:
    FILE_NAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
export function doAthing(): ReturnValue[] {
return []
}
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME: FILE_CONTENT}) as codebase:
        file = codebase.get_file(FILE_NAME)
        func = file.get_function("doAthing")
        assert func.docstring is None
