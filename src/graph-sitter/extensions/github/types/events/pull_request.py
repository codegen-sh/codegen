from typing import Literal

from pydantic import BaseModel

from ..base import GitHubRepository, GitHubUser
from ..enterprise import GitHubEnterprise
from ..installation import GitHubInstallation
from ..label import GitHubLabel
from ..organization import GitHubOrganization
from ..pull_request import PullRequest


class User(BaseModel):
    id: int
    login: str


class Label(BaseModel):
    id: int
    node_id: str
    url: str
    name: str
    description: str | None = None
    color: str
    default: bool


class SimplePullRequest(BaseModel):
    id: int
    number: int
    state: str
    locked: bool
    title: str
    user: User
    body: str | None = None
    labels: list[Label] = []
    created_at: str
    updated_at: str
    draft: bool = False


class PullRequestLabeledEvent(BaseModel):
    """Simplified version of the PR labeled event for testing"""

    action: Literal["labeled"]
    number: int
    pull_request: PullRequest
    label: Label
    repository: dict  # Simplified for now
    sender: User


class PullRequestOpenedEvent(BaseModel):
    action: str = "opened"  # Always "opened" for this event
    number: int
    pull_request: PullRequest
    repository: GitHubRepository
    organization: GitHubOrganization
    enterprise: GitHubEnterprise
    sender: GitHubUser
    installation: GitHubInstallation


class PullRequestUnlabeledEvent(BaseModel):
    action: str
    number: int
    pull_request: PullRequest
    label: GitHubLabel
    repository: GitHubRepository
    organization: GitHubOrganization
    enterprise: GitHubEnterprise
    sender: GitHubUser
    installation: GitHubInstallation
