from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_verify_output_python(tmpdir) -> None:
    try:
        with get_codebase_session(
            tmpdir=tmpdir,
            files={"invalid.py": "print('Hello, world!'", "valid.py": "print('Hello, world!')"},
            programming_language=ProgrammingLanguage.PYTHON,
            verify_output=True,
        ) as codebase:
            pass

        # If we reach here, the verify_output failed
        msg = "Verify output failed"
        raise Exception(msg)
    except SyntaxError:
        pass
