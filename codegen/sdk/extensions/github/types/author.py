from pydantic import BaseModel


class GitHubAuthor(BaseModel):
    name: str
    email: str
    username: str
