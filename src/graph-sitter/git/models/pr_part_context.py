from pydantic import BaseModel


class PRPartContext(BaseModel):
    """Represents a GitHub pull request part parsed from a webhook payload"""

    ref: str
    sha: str

    @classmethod
    def from_payload(cls, payload: dict) -> "PRPartContext":
        return cls(ref=payload.get("ref"), sha=payload.get("sha"))
