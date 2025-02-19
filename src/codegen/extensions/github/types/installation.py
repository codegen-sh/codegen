from pydantic import BaseModel


class GitHubInstallation(BaseModel):
    id: int
    node_id: str
