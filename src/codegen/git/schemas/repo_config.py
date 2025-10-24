import os.path
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class RepoConfig(BaseModel):
    """Configuration for a repository."""

    name: str
    full_name: Optional[str] = None
    path: Optional[str] = None
    language: Optional[str] = None
    base_dir: str = "/tmp"
    default_branch: Optional[str] = None
    clone_url: Optional[str] = None
    ssh_url: Optional[str] = None
    html_url: Optional[str] = None
    api_url: Optional[str] = None
    token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    ssh_key: Optional[str] = None
    ssh_key_path: Optional[str] = None
    ssh_key_passphrase: Optional[str] = None
    ssh_known_hosts: Optional[str] = None
    ssh_known_hosts_path: Optional[str] = None
    ssh_config: Optional[str] = None
    ssh_config_path: Optional[str] = None
    ssh_agent_socket: Optional[str] = None
    ssh_agent_pid: Optional[str] = None
    ssh_agent_auth_sock: Optional[str] = None
    ssh_agent_auth_sock_path: Optional[str] = None
    ssh_agent_auth_sock_dir: Optional[str] = None
    ssh_agent_auth_sock_file: Optional[str] = None
    ssh_agent_auth_sock_file_path: Optional[str] = None
    ssh_agent_auth_sock_file_dir: Optional[str] = None
    ssh_agent_auth_sock_file_name: Optional[str] = None
    ssh_agent_auth_sock_file_ext: Optional[str] = None
    ssh_agent_auth_sock_file_base: Optional[str] = None
    ssh_agent_auth_sock_file_base_name: Optional[str] = None
    ssh_agent_auth_sock_file_base_ext: Optional[str] = None
    ssh_agent_auth_sock_file_base_dir: Optional[str] = None
    ssh_agent_auth_sock_file_base_path: Optional[str] = None
    ssh_agent_auth_sock_file_base_name_ext: Optional[str] = None
    ssh_agent_auth_sock_file_base_name_dir: Optional[str] = None
    ssh_agent_auth_sock_file_base_name_path: Optional[str] = None
    ssh_agent_auth_sock_file_base_ext_dir: Optional[str] = None
    ssh_agent_auth_sock_file_base_ext_path: Optional[str] = None
    ssh_agent_auth_sock_file_base_dir_path: Optional[str] = None
    ssh_agent_auth_sock_file_base_name_ext_dir: Optional[str] = None
    ssh_agent_auth_sock_file_base_name_ext_path: Optional[str] = None
    ssh_agent_auth_sock_file_base_name_dir_path: Optional[str] = None
    ssh_agent_auth_sock_file_base_ext_dir_path: Optional[str] = None
    ssh_agent_auth_sock_file_base_name_ext_dir_path: Optional[str] = None

    @property
    def organization_name(self) -> Optional[str]:
        """Get the organization name from the full_name."""
        if self.full_name and "/" in self.full_name:
            return self.full_name.split("/")[0]
        return None

    @property
    def repo_path(self) -> Path:
        """Get the path to the repository."""
        if self.organization_name:
            return Path(self.base_dir) / self.organization_name / self.name
        return Path(self.base_dir) / self.name

    @classmethod
    def from_envs(cls, default_repo_config: Optional["RepoConfig"] = None) -> "RepoConfig":
        """Create a RepoConfig from environment variables."""
        name = os.environ.get("REPO_NAME", "")
        full_name = os.environ.get("REPO_FULL_NAME", None)
        path = os.environ.get("REPO_PATH", default_repo_config.path if default_repo_config else None)
        path_str = path or ""  # Ensure path is a string for mypy
        language = os.environ.get("REPO_LANGUAGE", default_repo_config.language if default_repo_config else None)
        language_str = language.upper() if language else "PYTHON"  # Ensure language is a string for mypy
        base_dir = os.environ.get("REPO_BASE_DIR", default_repo_config.base_dir if default_repo_config else "/tmp")
        default_branch = os.environ.get("REPO_DEFAULT_BRANCH", default_repo_config.default_branch if default_repo_config else None)
        clone_url = os.environ.get("REPO_CLONE_URL", default_repo_config.clone_url if default_repo_config else None)
        ssh_url = os.environ.get("REPO_SSH_URL", default_repo_config.ssh_url if default_repo_config else None)
        html_url = os.environ.get("REPO_HTML_URL", default_repo_config.html_url if default_repo_config else None)
        api_url = os.environ.get("REPO_API_URL", default_repo_config.api_url if default_repo_config else None)
        token = os.environ.get("REPO_TOKEN", default_repo_config.token if default_repo_config else None)
        username = os.environ.get("REPO_USERNAME", default_repo_config.username if default_repo_config else None)
        password = os.environ.get("REPO_PASSWORD", default_repo_config.password if default_repo_config else None)
        ssh_key = os.environ.get("REPO_SSH_KEY", default_repo_config.ssh_key if default_repo_config else None)
        ssh_key_path = os.environ.get("REPO_SSH_KEY_PATH", default_repo_config.ssh_key_path if default_repo_config else None)
        ssh_key_passphrase = os.environ.get("REPO_SSH_KEY_PASSPHRASE", default_repo_config.ssh_key_passphrase if default_repo_config else None)
        ssh_known_hosts = os.environ.get("REPO_SSH_KNOWN_HOSTS", default_repo_config.ssh_known_hosts if default_repo_config else None)
        ssh_known_hosts_path = os.environ.get("REPO_SSH_KNOWN_HOSTS_PATH", default_repo_config.ssh_known_hosts_path if default_repo_config else None)
        ssh_config = os.environ.get("REPO_SSH_CONFIG", default_repo_config.ssh_config if default_repo_config else None)
        ssh_config_path = os.environ.get("REPO_SSH_CONFIG_PATH", default_repo_config.ssh_config_path if default_repo_config else None)
        ssh_agent_socket = os.environ.get("REPO_SSH_AGENT_SOCKET", default_repo_config.ssh_agent_socket if default_repo_config else None)
        ssh_agent_pid = os.environ.get("REPO_SSH_AGENT_PID", default_repo_config.ssh_agent_pid if default_repo_config else None)
        ssh_agent_auth_sock = os.environ.get("REPO_SSH_AGENT_AUTH_SOCK", default_repo_config.ssh_agent_auth_sock if default_repo_config else None)
        ssh_agent_auth_sock_path = os.environ.get(
            "REPO_SSH_AGENT_AUTH_SOCK_PATH",
            default_repo_config.ssh_agent_auth_sock_path if default_repo_config else None,
        )
        ssh_agent_auth_sock_dir = os.environ.get(
            "REPO_SSH_AGENT_AUTH_SOCK_DIR",
            default_repo_config.ssh_agent_auth_sock_dir if default_repo_config else None,
        )
        ssh_agent_auth_sock_file = os.environ.get(
            "REPO_SSH_AGENT_AUTH_SOCK_FILE",
            default_repo_config.ssh_agent_auth_sock_file if default_repo_config else None,
        )
        ssh_agent_auth_sock_file_path = os.environ.get(
            "REPO_SSH_AGENT_AUTH_SOCK_FILE_PATH",
            default_repo_config.ssh_agent_auth_sock_file_path if default_repo_config else None,
        )
        ssh_agent_auth_sock_file_dir = os.environ.get(
            "REPO_SSH_AGENT_AUTH_SOCK_FILE_DIR",
            default_repo_config.ssh_agent_auth_sock_file_dir if default_repo_config else None,
        )
        ssh_agent_auth_sock_file_name = os.environ.get(
            "REPO_SSH_AGENT_AUTH_SOCK_FILE_NAME",
            default_repo_config.ssh_agent_auth_sock_file_name if default_repo_config else None,
        )
        ssh_agent_auth_sock_file_ext = os.environ.get(
            "REPO_SSH_AGENT_AUTH_SOCK_FILE_EXT",
            default_repo_config.ssh_agent_auth_sock_file_ext if default_repo_config else None,
        )
        ssh_agent_auth_sock_file_base = os.environ.get(
            "REPO_SSH_AGENT_AUTH_SOCK_FILE_BASE",
            default_repo_config.ssh_agent_auth_sock_file_base if default_repo_config else None,
        )
        ssh_agent_auth_sock_file_base_name = os.environ.get(
            "REPO_SSH_AGENT_AUTH_SOCK_FILE_BASE_NAME",
            default_repo_config.ssh_agent_auth_sock_file_base_name if default_repo_config else None,
        )
        ssh_agent_auth_sock_file_base_ext = os.environ.get(
            "REPO_SSH_AGENT_AUTH_SOCK_FILE_BASE_EXT",
            default_repo_config.ssh_agent_auth_sock_file_base_ext if default_repo_config else None,
        )
        ssh_agent_auth_sock_file_base_dir = os.environ.get(
            "REPO_SSH_AGENT_AUTH_SOCK_FILE_BASE_DIR",
            default_repo_config.ssh_agent_auth_sock_file_base_dir if default_repo_config else None,
        )
        ssh_agent_auth_sock_file_base_path = os.environ.get(
            "REPO_SSH_AGENT_AUTH_SOCK_FILE_BASE_PATH",
            default_repo_config.ssh_agent_auth_sock_file_base_path if default_repo_config else None,
        )
        ssh_agent_auth_sock_file_base_name_ext = os.environ.get(
            "REPO_SSH_AGENT_AUTH_SOCK_FILE_BASE_NAME_EXT",
            default_repo_config.ssh_agent_auth_sock_file_base_name_ext if default_repo_config else None,
        )
        ssh_agent_auth_sock_file_base_name_dir = os.environ.get(
            "REPO_SSH_AGENT_AUTH_SOCK_FILE_BASE_NAME_DIR",
            default_repo_config.ssh_agent_auth_sock_file_base_name_dir if default_repo_config else None,
        )
        ssh_agent_auth_sock_file_base_name_path = os.environ.get(
            "REPO_SSH_AGENT_AUTH_SOCK_FILE_BASE_NAME_PATH",
            default_repo_config.ssh_agent_auth_sock_file_base_name_path if default_repo_config else None,
        )
        ssh_agent_auth_sock_file_base_ext_dir = os.environ.get(
            "REPO_SSH_AGENT_AUTH_SOCK_FILE_BASE_EXT_DIR",
            default_repo_config.ssh_agent_auth_sock_file_base_ext_dir if default_repo_config else None,
        )
        ssh_agent_auth_sock_file_base_ext_path = os.environ.get(
            "REPO_SSH_AGENT_AUTH_SOCK_FILE_BASE_EXT_PATH",
            default_repo_config.ssh_agent_auth_sock_file_base_ext_path if default_repo_config else None,
        )
        ssh_agent_auth_sock_file_base_dir_path = os.environ.get(
            "REPO_SSH_AGENT_AUTH_SOCK_FILE_BASE_DIR_PATH",
            default_repo_config.ssh_agent_auth_sock_file_base_dir_path if default_repo_config else None,
        )
        ssh_agent_auth_sock_file_base_name_ext_dir = os.environ.get(
            "REPO_SSH_AGENT_AUTH_SOCK_FILE_BASE_NAME_EXT_DIR",
            default_repo_config.ssh_agent_auth_sock_file_base_name_ext_dir if default_repo_config else None,
        )
        ssh_agent_auth_sock_file_base_name_ext_path = os.environ.get(
            "REPO_SSH_AGENT_AUTH_SOCK_FILE_BASE_NAME_EXT_PATH",
            default_repo_config.ssh_agent_auth_sock_file_base_name_ext_path if default_repo_config else None,
        )
        ssh_agent_auth_sock_file_base_name_dir_path = os.environ.get(
            "REPO_SSH_AGENT_AUTH_SOCK_FILE_BASE_NAME_DIR_PATH",
            default_repo_config.ssh_agent_auth_sock_file_base_name_dir_path if default_repo_config else None,
        )
        ssh_agent_auth_sock_file_base_ext_dir_path = os.environ.get(
            "REPO_SSH_AGENT_AUTH_SOCK_FILE_BASE_EXT_DIR_PATH",
            default_repo_config.ssh_agent_auth_sock_file_base_ext_dir_path if default_repo_config else None,
        )
        ssh_agent_auth_sock_file_base_name_ext_dir_path = os.environ.get(
            "REPO_SSH_AGENT_AUTH_SOCK_FILE_BASE_NAME_EXT_DIR_PATH",
            default_repo_config.ssh_agent_auth_sock_file_base_name_ext_dir_path if default_repo_config else None,
        )

        return cls(
            name=name,
            full_name=full_name,
            path=path_str,
            language=language_str,
            base_dir=base_dir,
            default_branch=default_branch,
            clone_url=clone_url,
            ssh_url=ssh_url,
            html_url=html_url,
            api_url=api_url,
            token=token,
            username=username,
            password=password,
            ssh_key=ssh_key,
            ssh_key_path=ssh_key_path,
            ssh_key_passphrase=ssh_key_passphrase,
            ssh_known_hosts=ssh_known_hosts,
            ssh_known_hosts_path=ssh_known_hosts_path,
            ssh_config=ssh_config,
            ssh_config_path=ssh_config_path,
            ssh_agent_socket=ssh_agent_socket,
            ssh_agent_pid=ssh_agent_pid,
            ssh_agent_auth_sock=ssh_agent_auth_sock,
            ssh_agent_auth_sock_path=ssh_agent_auth_sock_path,
            ssh_agent_auth_sock_dir=ssh_agent_auth_sock_dir,
            ssh_agent_auth_sock_file=ssh_agent_auth_sock_file,
            ssh_agent_auth_sock_file_path=ssh_agent_auth_sock_file_path,
            ssh_agent_auth_sock_file_dir=ssh_agent_auth_sock_file_dir,
            ssh_agent_auth_sock_file_name=ssh_agent_auth_sock_file_name,
            ssh_agent_auth_sock_file_ext=ssh_agent_auth_sock_file_ext,
            ssh_agent_auth_sock_file_base=ssh_agent_auth_sock_file_base,
            ssh_agent_auth_sock_file_base_name=ssh_agent_auth_sock_file_base_name,
            ssh_agent_auth_sock_file_base_ext=ssh_agent_auth_sock_file_base_ext,
            ssh_agent_auth_sock_file_base_dir=ssh_agent_auth_sock_file_base_dir,
            ssh_agent_auth_sock_file_base_path=ssh_agent_auth_sock_file_base_path,
            ssh_agent_auth_sock_file_base_name_ext=ssh_agent_auth_sock_file_base_name_ext,
            ssh_agent_auth_sock_file_base_name_dir=ssh_agent_auth_sock_file_base_name_dir,
            ssh_agent_auth_sock_file_base_name_path=ssh_agent_auth_sock_file_base_name_path,
            ssh_agent_auth_sock_file_base_ext_dir=ssh_agent_auth_sock_file_base_ext_dir,
            ssh_agent_auth_sock_file_base_ext_path=ssh_agent_auth_sock_file_base_ext_path,
            ssh_agent_auth_sock_file_base_dir_path=ssh_agent_auth_sock_file_base_dir_path,
            ssh_agent_auth_sock_file_base_name_ext_dir=ssh_agent_auth_sock_file_base_name_ext_dir,
            ssh_agent_auth_sock_file_base_name_ext_path=ssh_agent_auth_sock_file_base_name_ext_path,
            ssh_agent_auth_sock_file_base_name_dir_path=ssh_agent_auth_sock_file_base_name_dir_path,
            ssh_agent_auth_sock_file_base_ext_dir_path=ssh_agent_auth_sock_file_base_ext_dir_path,
            ssh_agent_auth_sock_file_base_name_ext_dir_path=ssh_agent_auth_sock_file_base_name_ext_dir_path,
        )

    @classmethod
    def from_repo_path(cls, repo_path: str, full_name: str | None = None) -> "RepoConfig":
        name = os.path.basename(repo_path)
        base_dir = os.path.dirname(repo_path)
        return cls(name=name, base_dir=base_dir, full_name=full_name)

    @property
    def repo_path(self) -> Path:
        # Use organization name in the path if available
        if self.organization_name:
            return Path(f"/tmp/{self.organization_name}/{self.name}")
        # Fall back to the original path format if no organization name is available
        return Path(f"{self.base_dir}/{self.name}")

    @property
    def organization_name(self) -> str | None:
        if self.full_name is not None:
            return self.full_name.split("/")[0]

        return None
