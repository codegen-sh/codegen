import os

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_get_codebase_session(tmpdir) -> None:
    # READ THIS CONTEXT BEFORE EDITING THIS TEST!
    # Essentially, there was this bug where the file in the base codegen-sdk repo was being edited instead of the file in the tmpdir
    # This test is to ensure that this bug does not happen again.
    # target_file must be a file that shares the same relative path in the codegen-sdk repo

    # Init Test
    target_file = "tests/unit/codegen/sdk/codebase/session/target_python_file.py"
    assert os.path.exists(target_file), f"Target file {target_file} does not exist! Please change this to a file that exists in codegen-sdk"
    target_orig_content = open(target_file).read()

    # Setup dummy test
    try:
        with get_codebase_session(
            tmpdir=tmpdir,
            # NOTE: For this edge case in particular, the final file SHOULD be an invalid python file!
            files={target_file: "This should not be here\n" + target_orig_content},
            programming_language=ProgrammingLanguage.PYTHON,
            verify_output=True,
        ) as codebase:
            file = codebase.get_file(target_file)
            assert file.content is not None
            assert file.content != ""
            assert file.content != target_orig_content
            assert "This should not be here" in file.content
    except SyntaxError:
        pass  # This is expected!

    # Verify the file on codegen-sdk was not edited
    assert open(target_file).read() == target_orig_content
