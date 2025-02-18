from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_file_get_import_string_no_params(tmpdir) -> None:
    content = """
age: int = 25;
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.PYTHON, files={"test.py": content}) as ctx:
        file = ctx.get_file("test.py")

        file_import_string = file.get_import_string()
        assert file_import_string == "from . import test"
