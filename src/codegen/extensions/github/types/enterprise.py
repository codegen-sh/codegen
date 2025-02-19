from pydantic import BaseModel


class GitHubEnterprise(BaseModel):
    id: int
    slug: str
    name: str
    node_id: str
    avatar_url: str
    description: str
    website_url: str
    html_url: str
    created_at: str
    updated_at: str
