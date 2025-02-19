from pydantic import BaseModel


class GitHubPusher(BaseModel):
    name: str
    email: str
