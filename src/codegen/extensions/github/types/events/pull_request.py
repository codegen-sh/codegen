from pydantic import BaseModel

from ..base import GitHubRepository, GitHubUser
from ..enterprise import GitHubEnterprise
from ..installation import GitHubInstallation
from ..label import GitHubLabel
from ..organization import GitHubOrganization
from ..pull_request import PullRequest


class PullRequestLabeledEvent(BaseModel):
    action: str  # Will be "labeled"
    number: int
    pull_request: PullRequest
    label: GitHubLabel
    repository: GitHubRepository
    organization: GitHubOrganization
    enterprise: GitHubEnterprise
    sender: GitHubUser
    installation: GitHubInstallation


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
