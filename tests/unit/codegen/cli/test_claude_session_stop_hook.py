from contextlib import redirect_stderr, redirect_stdout
from importlib.util import module_from_spec, spec_from_file_location
from io import StringIO
from pathlib import Path


def load_module():
    repo = Path(__file__).resolve().parents[4]
    path = repo / "src" / "codegen" / "cli" / "commands" / "claude" / "config" / "claude_session_stop_hook.py"
    spec = spec_from_file_location("test_codegen_claude_session_stop_hook", path)
    module = module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_stop_hook_stays_silent_on_stdout(monkeypatch):
    module = load_module()
    calls = []
    monkeypatch.setenv("CODEGEN_CLAUDE_SESSION_ID", "session-123")
    monkeypatch.setenv("CODEGEN_CLAUDE_ORG_ID", "42")
    monkeypatch.setattr(module, "update_claude_session_status", lambda session_id, status, org_id: calls.append((session_id, status, org_id)))

    stdout = StringIO()
    stderr = StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = module.main()

    assert code == 0
    assert stdout.getvalue() == ""
    assert stderr.getvalue() == ""
    assert calls == [("session-123", "COMPLETE", 42)]
