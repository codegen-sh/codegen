from pydantic import BaseModel, Field


class GitHubUser(BaseModel):
    login: str
    id: int
    node_id: str
    type: str


class GitHubRepository(BaseModel):
    id: int
    node_id: str
    name: str
    full_name: str
    private: bool
    owner: GitHubUser


class GitHubIssue(BaseModel):
    id: int
    node_id: str
    number: int
    title: str
    body: str | None
    user: GitHubUser
    state: str
    comments: int


class GitHubPullRequest(BaseModel):
    id: int
    node_id: str
    number: int
    title: str
    body: str | None
    user: GitHubUser
    state: str
    head: dict
    base: dict
    merged: bool | None = None


class GitHubEvent(BaseModel):
    action: str | None = None
    issue: GitHubIssue | None = None
    pull_request: GitHubPullRequest | None = None
    repository: GitHubRepository
    sender: GitHubUser


class GitHubWebhookHeaders(BaseModel):
    event_type: str = Field(..., alias="x-github-event")
    delivery_id: str = Field(..., alias="x-github-delivery")
    hook_id: str = Field(..., alias="x-github-hook-id")
    installation_target_id: str = Field(..., alias="x-github-hook-installation-target-id")
    installation_target_type: str = Field(..., alias="x-github-hook-installation-target-type")


class GitHubWebhookPayload(BaseModel):
    headers: GitHubWebhookHeaders
    event: GitHubEvent


class GitHubInstallation(BaseModel):
    code: str
    installation_id: str
    setup_action: str = "install"
