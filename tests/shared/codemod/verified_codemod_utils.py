import base64
import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path

import requests
from pydantic import BaseModel

from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.codemod.constants import GET_CODEMODS_URL_SUFFIX, UPDATE_CODEMOD_DIFF_URL_SUFFIX

logger = logging.getLogger(__name__)


def anonymize_id(id: int) -> str:
    sha = hashlib.sha256(str(id).encode()).hexdigest()
    return base64.urlsafe_b64encode(sha.encode()).decode()[:10]


class CodemodMetadata(BaseModel):
    name: str
    codemod_id: int
    repo_app_id: int
    source: str
    diff: str | None
    codemod_url: str

    @property
    def anonymized_name(self) -> str:
        return anonymize_id(self.codemod_id)


class RepoCodemodMetadata(BaseModel):
    repo_id: int
    language: ProgrammingLanguage
    repo_name: str
    codemods_by_base_commit: dict[str, list[CodemodMetadata]]

    @classmethod
    def from_json_file(cls, file_path: str | Path) -> "RepoCodemodMetadata":
        """Load RepoCodemodMetadata from a JSON file

        Example usage:
            metadata = RepoCodemodMetadata.from_json_file("path/to/metadata.json")
        """
        file_path = Path(file_path)
        with open(file_path) as f:
            data = json.load(f)
        return cls.model_validate(data)

    def filter(self, base_commit: str | None = None, codemod_id: int | None = None) -> None:
        """Filters the contents of this RepoCodemodMetadata instance in-place

        Args:
            base_commit: Optional commit hash to filter by
            codemod_id: Optional codemod ID to filter by

        Example:
            # Filter by commit
            metadata.filter(base_commit="main")

            # Filter by codemod_id
            metadata.filter(codemod_id=123)

            # Filter by both
            metadata.filter(base_commit="main", codemod_id=123)
        """
        # Filter by commit if specified
        if base_commit is not None:
            self.codemods_by_base_commit = {commit: codemods for commit, codemods in self.codemods_by_base_commit.items() if commit == base_commit}

        # Filter by codemod_id if specified
        if codemod_id is not None:
            self.codemods_by_base_commit = {commit: [codemod for codemod in codemods if codemod.codemod_id == codemod_id] for commit, codemods in self.codemods_by_base_commit.items()}
            # Remove empty commits
            self.codemods_by_base_commit = {commit: codemods for commit, codemods in self.codemods_by_base_commit.items() if codemods}

    @property
    def anonymized_name(self) -> str:
        return anonymize_id(self.repo_id)


class CodemodAPI:
    def __init__(self, api_key: str | None = None, modal_prefix: str = "https://codegen-sh"):
        self.api_key = api_key
        self.modal_prefix = modal_prefix
        self.get_codemods_url = f"{self.modal_prefix}--{GET_CODEMODS_URL_SUFFIX}"
        self.update_diff_url = f"{self.modal_prefix}--{UPDATE_CODEMOD_DIFF_URL_SUFFIX}"

    def _get_headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def _make_request(self, url: str, input_data: dict) -> requests.Response:
        """Helper method to make HTTP requests with common headers and error handling"""
        try:
            response = requests.post(
                url,
                json={"input": input_data},
                headers=self._get_headers(),
            )
            if response.status_code != 200:
                logger.error(f"Error making request: {response.status_code} {response.text}")
                msg = f"Error making request: {response.status_code} {response.text}"
                raise Exception(msg)
            return response
        except requests.RequestException as e:
            logger.exception(f"Error making request: {e}")
            raise e

    def get_verified_codemods(self, repo_id: int, codemod_id: int | None = None, base_commit: str | None = None) -> RepoCodemodMetadata:
        """Get verified codemods for a given repo"""
        input_data = {"repo_id": repo_id}
        if codemod_id:
            input_data["codemod_id"] = codemod_id
        if base_commit:
            input_data["base_commit"] = base_commit

        response = self._make_request(self.get_codemods_url, input_data)
        return RepoCodemodMetadata(**response.json())

    def update_snapshot(self, repo_app_id: int, diff: str) -> bool:
        """Send snapshot data to external DB via API
        Returns True if successful, False otherwise
        """
        try:
            self._make_request(self.update_diff_url, {"repo_app_id": repo_app_id, "new_diff": diff})
            return True
        except Exception:
            return False


@dataclass
class SkillTestConfig:
    codemod_id: str | None
    repo_id: str | None
    base_commit: str | None
    api_key: str | None

    @classmethod
    def from_metafunc(cls, metafunc) -> "SkillTestConfig":
        return cls(
            codemod_id=metafunc.config.getoption("--codemod-id"),
            repo_id=metafunc.config.getoption("--repo-id"),
            base_commit=metafunc.config.getoption("--base-commit"),
            api_key=metafunc.config.getoption("--cli-api-key"),
        )


class UpdateDiffInput(BaseModel):
    repo_app_id: int
    new_diff: str
