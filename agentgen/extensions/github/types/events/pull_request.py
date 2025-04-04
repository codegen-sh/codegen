"""GitHub pull request event types."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class GitHubUser(BaseModel):
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


class GitHubLabel(BaseModel):
    """GitHub label model."""

    id: int
    node_id: str
    url: str
    name: str
    color: str
    default: bool
    description: Optional[str] = None


class GitHubMilestone(BaseModel):
    """GitHub milestone model."""

    url: str
    html_url: str
    labels_url: str
    id: int
    node_id: str
    number: int
    title: str
    description: Optional[str] = None
    creator: GitHubUser
    open_issues: int
    closed_issues: int
    state: str
    created_at: str
    updated_at: str
    due_on: Optional[str] = None
    closed_at: Optional[str] = None


class GitHubRepository(BaseModel):
    """GitHub repository model."""

    id: int
    node_id: str
    name: str
    full_name: str
    private: bool
    owner: GitHubUser
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
    allow_squash_merge: Optional[bool] = None
    allow_merge_commit: Optional[bool] = None
    allow_rebase_merge: Optional[bool] = None
    allow_auto_merge: Optional[bool] = None
    delete_branch_on_merge: Optional[bool] = None
    allow_update_branch: Optional[bool] = None
    use_squash_pr_title_as_default: Optional[bool] = None
    squash_merge_commit_message: Optional[str] = None
    squash_merge_commit_title: Optional[str] = None
    merge_commit_message: Optional[str] = None
    merge_commit_title: Optional[str] = None


class GitHubOrganization(BaseModel):
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


class GitHubPullRequest(BaseModel):
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
    user: GitHubUser
    body: Optional[str] = None
    created_at: str
    updated_at: str
    closed_at: Optional[str] = None
    merged_at: Optional[str] = None
    merge_commit_sha: Optional[str] = None
    assignee: Optional[GitHubUser] = None
    assignees: List[GitHubUser] = Field(default_factory=list)
    requested_reviewers: List[GitHubUser] = Field(default_factory=list)
    requested_teams: List[Dict[str, Any]] = Field(default_factory=list)
    labels: List[GitHubLabel] = Field(default_factory=list)
    milestone: Optional[GitHubMilestone] = None
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
    """Base class for pull request events."""

    action: str
    number: int
    pull_request: GitHubPullRequest
    repository: GitHubRepository
    organization: GitHubOrganization
    sender: GitHubUser


class PullRequestLabeledEvent(PullRequestEvent):
    """Event triggered when a label is added to a pull request."""

    action: str = "labeled"
    label: GitHubLabel


class PullRequestUnlabeledEvent(PullRequestEvent):
    """Event triggered when a label is removed from a pull request."""

    action: str = "unlabeled"
    label: GitHubLabel