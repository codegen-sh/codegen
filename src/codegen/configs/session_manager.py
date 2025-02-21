"""Global config to manage different codegen sessions, as well as user auth."""

import json
from pathlib import Path

from codegen.configs.constants import SESSION_FILE


class SessionManager:
    active_session_path: str | None
    sessions: list[str]

    def __init__(self, **kwargs) -> None:
        if SESSION_FILE.exists():
            with open(SESSION_FILE) as f:
                json_config = json.load(f)
                self.sessions = json_config["sessions"]
                self.active_session_path = json_config["active_session_path"]
        else:
            self.sessions = []
            self.active_session_path = None
        super().__init__(**kwargs)

    def get_session(self, session_root_path: Path) -> str | None:
        return next((s for s in self.sessions if s == str(session_root_path)), None)

    def get_active_session(self) -> Path | None:
        if not self.active_session_path:
            return None

        return Path(self.active_session_path)

    def set_active_session(self, session_root_path: Path) -> None:
        if not session_root_path.exists():
            msg = f"Session path does not exist: {session_root_path}"
            raise ValueError(msg)

        self.active_session_path = str(session_root_path)
        if self.active_session_path not in self.sessions:
            self.sessions.append(self.active_session_path)

        self.save()

    def save(self) -> None:
        if not SESSION_FILE.parent.exists():
            SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)

        with open(SESSION_FILE, "w") as f:
            json.dump(self.__dict__(), f)

    def __dict__(self) -> dict:
        return {
            "active_session_path": self.active_session_path,
            "sessions": self.sessions,
        }

    def __str__(self) -> str:
        active = self.active_session_path or "None"
        sessions_str = "\n    ".join(self.sessions) if self.sessions else "None"

        return f"GlobalConfig:\n  Active Session: {active}\n  Sessions:\n    {sessions_str}\n  Global Session:\n    {self.session_config}"


session_manager = SessionManager()
