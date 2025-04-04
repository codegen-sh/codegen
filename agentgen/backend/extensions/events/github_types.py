from datetime import datetime
from typing import Optional


class GitHubRepository:
    id: int
    node_id: str
    name: str
    full_name: str
    private: bool


class GitHubAccount:
    login: str
    id: int
    node_id: str
    avatar_url: str
    type: str
    site_admin: bool
    # Other URL fields omitted for brevity
    user_view_type: str


class GitHubInstallation:
    id: int
    client_id: str
    account: GitHubAccount
    repository_selection: str
    access_tokens_url: str
    repositories_url: str
    html_url: str
    app_id: int
    app_slug: str
    target_id: int
    target_type: str
    permissions: dict[str, str]  # e.g. {'actions': 'write', 'checks': 'read', ...}
    events: list[str]
    created_at: datetime
    updated_at: datetime
    single_file_name: Optional[str]
    has_multiple_single_files: bool
    single_file_paths: list[str]
    suspended_by: Optional[str]
    suspended_at: Optional[datetime]


class GitHubUser:
    login: str
    id: int
    node_id: str
    avatar_url: str
    type: str
    site_admin: bool
    # Other URL fields omitted for brevity


class GitHubInstallationEvent:
    action: str
    installation: GitHubInstallation
    repositories: list[GitHubRepository]
    requester: Optional[dict]
    sender: GitHubUser
