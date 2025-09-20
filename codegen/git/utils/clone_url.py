from urllib.parse import urlparse

from codegen.git.schemas.repo_config import RepoConfig


# TODO: move out doesn't belong here
def url_to_github(url: str, branch: str) -> str:
    clone_url = url.removesuffix(".git").replace("git@github.com:", "github.com/")
    return f"{clone_url}/blob/{branch}"


def get_clone_url_for_repo_config(repo_config: RepoConfig) -> str:
    return f"https://github.com/{repo_config.full_name}.git"


def get_authenticated_clone_url_for_repo_config(repo: RepoConfig, token: str) -> str:
    git_url = get_clone_url_for_repo_config(repo)
    return add_access_token_to_url(git_url, token)


def add_access_token_to_url(url: str, token: str | None) -> str:
    parsed_url = urlparse(url)
    scheme = parsed_url.scheme or "https"
    token_prefix = f"x-access-token:{token}@" if token else ""
    return f"{scheme}://{token_prefix}{parsed_url.netloc}{parsed_url.path}"
