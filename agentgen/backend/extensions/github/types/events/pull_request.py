"""
GitHub pull request event types.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class User(BaseModel):
    """GitHub user model."""
    
    login: str
    id: int
    node_id: str
    avatar_url: str
    gravatar_id: str
    url: str
    html_url: str
    followers_url: str
    following_url: str
    gists_url: str
    starred_url: str
    subscriptions_url: str
    organizations_url: str
    repos_url: str
    events_url: str
    received_events_url: str
    type: str
    site_admin: bool


class Label(BaseModel):
    """GitHub label model."""
    
    id: int
    node_id: str
    url: str
    name: str
    color: str
    default: bool
    description: Optional[str] = None


class Repository(BaseModel):
    """GitHub repository model."""
    
    id: int
    node_id: str
    name: str
    full_name: str
    private: bool
    owner: User
    html_url: str
    description: Optional[str] = None
    fork: bool
    url: str
    forks_url: str
    keys_url: str
    collaborators_url: str
    teams_url: str
    hooks_url: str
    issue_events_url: str
    events_url: str
    assignees_url: str
    branches_url: str
    tags_url: str
    blobs_url: str
    git_tags_url: str
    git_refs_url: str
    trees_url: str
    statuses_url: str
    languages_url: str
    stargazers_url: str
    contributors_url: str
    subscribers_url: str
    subscription_url: str
    commits_url: str
    git_commits_url: str
    comments_url: str
    issue_comment_url: str
    contents_url: str
    compare_url: str
    merges_url: str
    archive_url: str
    downloads_url: str
    issues_url: str
    pulls_url: str
    milestones_url: str
    notifications_url: str
    labels_url: str
    releases_url: str
    deployments_url: str
    created_at: str
    updated_at: str
    pushed_at: str
    git_url: str
    ssh_url: str
    clone_url: str
    svn_url: str
    homepage: Optional[str] = None
    size: int
    stargazers_count: int
    watchers_count: int
    language: Optional[str] = None
    has_issues: bool
    has_projects: bool
    has_downloads: bool
    has_wiki: bool
    has_pages: bool
    has_discussions: bool
    forks_count: int
    mirror_url: Optional[str] = None
    archived: bool
    disabled: bool
    open_issues_count: int
    license: Optional[Dict[str, Any]] = None
    allow_forking: bool
    is_template: bool
    web_commit_signoff_required: bool
    topics: List[str]
    visibility: str
    default_branch: str


class Organization(BaseModel):
    """GitHub organization model."""
    
    login: str
    id: int
    node_id: str
    url: str
    repos_url: str
    events_url: str
    hooks_url: str
    issues_url: str
    members_url: str
    public_members_url: str
    avatar_url: str
    description: Optional[str] = None


class PullRequest(BaseModel):
    """GitHub pull request model."""
    
    url: str
    id: int
    node_id: str
    html_url: str
    diff_url: str
    patch_url: str
    issue_url: str
    number: int
    state: str
    locked: bool
    title: str
    user: User
    body: Optional[str] = None
    created_at: str
    updated_at: str
    closed_at: Optional[str] = None
    merged_at: Optional[str] = None
    merge_commit_sha: Optional[str] = None
    assignee: Optional[User] = None
    assignees: List[User] = Field(default_factory=list)
    requested_reviewers: List[User] = Field(default_factory=list)
    requested_teams: List[Dict[str, Any]] = Field(default_factory=list)
    labels: List[Label] = Field(default_factory=list)
    milestone: Optional[Dict[str, Any]] = None
    draft: bool
    commits_url: str
    review_comments_url: str
    review_comment_url: str
    comments_url: str
    statuses_url: str
    head: Dict[str, Any]
    base: Dict[str, Any]
    _links: Dict[str, Any]
    author_association: str
    auto_merge: Optional[Dict[str, Any]] = None
    active_lock_reason: Optional[str] = None


class PullRequestEvent(BaseModel):
    """Base GitHub pull request event model."""
    
    action: str
    number: int
    pull_request: PullRequest
    repository: Repository
    sender: User
    organization: Optional[Organization] = None


class PullRequestOpenedEvent(PullRequestEvent):
    action: str = "opened"


class PullRequestClosedEvent(PullRequestEvent):
    action: str = "closed"


class PullRequestReopenedEvent(PullRequestEvent):
    action: str = "reopened"


class PullRequestLabeledEvent(PullRequestEvent):
    action: str = "labeled"
    label: Label


class PullRequestUnlabeledEvent(PullRequestEvent):
    action: str = "unlabeled"
    label: Label


class PullRequestSynchronizeEvent(PullRequestEvent):
    action: str = "synchronize"
    before: str
    after: str
