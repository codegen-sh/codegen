import pytest

from codegen.sdk.codebase.config import SessionOptions
from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.codebase.transaction_manager import MaxPreviewTimeExceeded, MaxTransactionsExceeded
from codegen.sdk.core.codebase import MaxAIRequestsError
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_max_transactions_exceeded_reached_set_threshold(tmpdir):
    e = MaxTransactionsExceeded("test exception", threshold=1)
    assert str(e) == "test exception"
    assert e.threshold == 1


def test_raise_max_transactions_exceeded_reached_no_threshold(tmpdir):
    with pytest.raises(MaxTransactionsExceeded) as exc_info:
        msg = "test exception"
        raise MaxTransactionsExceeded(msg)
    assert str(exc_info.value) == "test exception"
    assert exc_info.value.threshold is None


def test_raise_max_transactions_exceeded_reached_with_threshold(tmpdir):
    with pytest.raises(MaxTransactionsExceeded) as exc_info:
        msg = "test exception"
        raise MaxTransactionsExceeded(msg, threshold=1)
    assert str(exc_info.value) == "test exception"
    assert exc_info.value.threshold == 1


def test_max_transactions_exceeded_reached(tmpdir):
    with pytest.raises(MaxTransactionsExceeded) as exc_info:
        with get_codebase_session(
            tmpdir=tmpdir,
            files={"file_a.py": "a = 1", "file_b": "b = 1"},
            programming_language=ProgrammingLanguage.PYTHON,
            session_options=SessionOptions(max_transactions=1),
        ) as codebase:
            codebase.get_file("file_a.py").insert_after("a = 2")
            codebase.get_file("file_b.py").insert_after("b = 2")
    assert str(exc_info.value) == "Max transactions reached: 1"
    assert exc_info.value.threshold == 1


def test_max_transactions_exceeded_reached_should_still_commit(tmpdir):
    with pytest.raises(MaxTransactionsExceeded) as exc_info:
        with get_codebase_session(
            tmpdir=tmpdir,
            files={"file_a.py": "a = 1", "file_b": "b = 1"},
            programming_language=ProgrammingLanguage.PYTHON,
            session_options=SessionOptions(max_transactions=1),
        ) as codebase:
            codebase.get_file("file_a.py").insert_after("a = 2")
            codebase.get_file("file_b.py").insert_after("b = 2")
    file = codebase.get_file("file_a.py")
    assert file.content == "a = 1\na = 2"
    assert str(exc_info.value) == "Max transactions reached: 1"
    assert exc_info.value.threshold == 1


def test_max_preview_time_exceeded_reached(tmpdir):
    with pytest.raises(MaxPreviewTimeExceeded) as exc_info:
        with get_codebase_session(
            tmpdir=tmpdir,
            files={"file_a.py": "a = 1", "file_b": "b = 1"},
            programming_language=ProgrammingLanguage.PYTHON,
            session_options=SessionOptions(max_seconds=0),
        ) as codebase:
            codebase.get_file("file_a.py").insert_after("a = 2")
            codebase.get_file("file_b.py").insert_after("a = 3")
    assert str(exc_info.value) == "Max preview time exceeded: True"
    assert exc_info.value.threshold == 0


def test_max_ai_requests_error_reached(tmpdir):
    with pytest.raises(MaxAIRequestsError) as exc_info:
        with get_codebase_session(
            tmpdir=tmpdir,
            files={"file_a.py": "a = 1", "file_b": "b = 1"},
            programming_language=ProgrammingLanguage.PYTHON,
        ) as codebase:
            codebase.set_session_options(max_ai_requests=0)
            codebase.ai("tell me a joke")
    assert str(exc_info.value) == "Maximum number of AI requests reached: 0"
    assert exc_info.value.threshold == 0
