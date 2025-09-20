from pydantic import BaseModel


class GithubNamedUserContext(BaseModel):
    """Represents a GitHub user parsed from a webhook payload"""

    login: str
    email: str | None = None

    @classmethod
    def from_payload(cls, payload: dict) -> "GithubNamedUserContext":
        return cls(login=payload.get("login"), email=payload.get("email"))
