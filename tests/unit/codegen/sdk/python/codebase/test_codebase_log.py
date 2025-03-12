from unittest.mock import patch

import pytest

from codegen.sdk.codebase.config import SessionOptions
from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codegen.shared.exceptions.control_flow import MaxPreviewTimeExceeded


def test_log_writes_to_console(tmpdir) -> None:
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
    ) as codebase:
        codebase.log("This is a test log")
        codebase.log("This is another test log")
    console = codebase.console.export_text()
    assert console == "This is a test log\nThis is another test log\n"


@patch("codegen.sdk.core.codebase.MAX_LINES", 1)
def test_log_truncate_at_max_lines(tmpdir) -> None:
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
    ) as codebase:
        codebase.log("1")
        codebase.log("2")
        codebase.log("3")
        codebase.log("4")
    console = codebase.console.export_text()
    assert console == "1\n"


@patch("codegen.sdk.core.codebase.MAX_LINES", 1)
def test_log_max_lines_reached_continues_execution(tmpdir) -> None:
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={"test.py": "a = 0"},
    ) as codebase:
        codebase.log("1")
        codebase.log("2")
        codebase.files[0].edit("a = 1")
        codebase.log("3")
        codebase.log("4")

    console = codebase.console.export_text()
    assert console == "1\n"
    assert codebase.files[0].content == "a = 1"


def test_get_finalized_logs_returns_all_logs(tmpdir) -> None:
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
    ) as codebase:
        codebase.log("1")
        codebase.log("2")
        codebase.log("3")
        codebase.log("4")
    console = codebase.get_finalized_logs()
    assert console == "1\n2\n3\n4\n"


@patch("codegen.sdk.core.codebase.MAX_LINES", 1)
def test_get_finalized_logs_truncate_at_max_lines(tmpdir) -> None:
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
    ) as codebase:
        pass
    codebase.log("1")
    codebase.log("2")
    codebase.log("3")
    codebase.log("4")
    console = codebase.get_finalized_logs()
    assert console == "1\n"


def test_log_raises_max_preview_time_exceeded(tmpdir) -> None:
    with pytest.raises(MaxPreviewTimeExceeded) as exc_info:
        with get_codebase_session(
            tmpdir=tmpdir,
            programming_language=ProgrammingLanguage.PYTHON,
            session_options=SessionOptions(max_seconds=0),
        ) as codebase:
            codebase.log("1")

    assert str(exc_info.value) == "Max preview time exceeded: True"
    assert exc_info.value.threshold == 0
