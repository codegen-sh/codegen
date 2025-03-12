import pytest

from codegen.sdk.codebase.config import SessionOptions
from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codegen.shared.exceptions.control_flow import MaxPreviewTimeExceeded, MaxTransactionsExceeded


def test_check_max_preview_time_exceeded(tmpdir):
    with pytest.raises(MaxPreviewTimeExceeded) as exc_info:
        with get_codebase_session(
            tmpdir=tmpdir,
            files={"file_a.py": "a = 1", "file_b": "b = 1"},
            programming_language=ProgrammingLanguage.PYTHON,
            session_options=SessionOptions(max_seconds=0),
        ) as codebase:
            codebase.ctx.transaction_manager.check_max_preview_time()

    assert str(exc_info.value) == "Max preview time exceeded: True"
    assert exc_info.value.threshold == 0


def test_check_max_preview_time_exceeded_set_session_options(tmpdir):
    with get_codebase_session(
        tmpdir=tmpdir,
        files={"file_a.py": "a = 1", "file_b": "b = 1"},
        programming_language=ProgrammingLanguage.PYTHON,
    ) as codebase:
        with pytest.raises(MaxPreviewTimeExceeded) as exc_info:
            codebase.set_session_options(max_seconds=0)
            codebase.ctx.transaction_manager.check_max_preview_time()

    assert str(exc_info.value) == "Max preview time exceeded: True"
    assert exc_info.value.threshold == 0


def test_check_max_transactions_exceeded(tmpdir):
    with pytest.raises(MaxTransactionsExceeded) as exc_info:
        with get_codebase_session(
            tmpdir=tmpdir,
            files={"file_a.py": "a = 1", "file_b": "b = 1"},
            programming_language=ProgrammingLanguage.PYTHON,
            session_options=SessionOptions(max_transactions=0),
        ) as codebase:
            codebase.ctx.transaction_manager.check_max_transactions()

    assert str(exc_info.value) == "Max transactions reached: 0"
    assert exc_info.value.threshold == 0


def test_check_max_transactions_exceeded_set_session_options(tmpdir):
    with get_codebase_session(
        tmpdir=tmpdir,
        files={"file_a.py": "a = 1", "file_b": "b = 1"},
        programming_language=ProgrammingLanguage.PYTHON,
    ) as codebase:
        with pytest.raises(MaxTransactionsExceeded) as exc_info:
            codebase.set_session_options(max_transactions=0)
            codebase.ctx.transaction_manager.check_max_transactions()

    assert str(exc_info.value) == "Max transactions reached: 0"
    assert exc_info.value.threshold == 0
