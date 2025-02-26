"""Dataclasses used by the sandboxes server APIs"""

from pydantic import BaseModel

from codegen.runner.enums.warmup_state import WarmupState
from codegen.runner.models.codemod import BranchConfig, Codemod, CodemodRunResult, CreatedBranch, GroupingConfig

SANDBOX_SERVER_PORT = 4000
EPHEMERAL_SANDBOX_SERVER_PORT = 4001

# APIs
DIFF_ENDPOINT = "/diff"
BRANCH_ENDPOINT = "/branch"
RUN_FUNCTION_ENDPOINT = "/run"

# Ephemeral sandbox apis
RUN_ON_STRING_ENDPOINT = "/run_on_string"


class ServerInfo(BaseModel):
    repo_name: str | None = None
    synced_commit: str | None = None
    warmup_state: WarmupState = WarmupState.PENDING


class GetDiffRequest(BaseModel):
    codemod: Codemod
    max_transactions: int | None = None
    max_seconds: int | None = None


class GetDiffResponse(BaseModel):
    result: CodemodRunResult


class CreateBranchRequest(BaseModel):
    codemod: Codemod
    commit_msg: str
    grouping_config: GroupingConfig
    branch_config: BranchConfig


class CreateBranchResponse(BaseModel):
    results: list[CodemodRunResult] | None = None
    branches: list[CreatedBranch] | None = None
    num_flags: int | None = None
    group_segments: list[str] | None = None


class GetRunOnStringRequest(BaseModel):
    codemod_source: str
    language: str
    files: dict[str, str]


class GetRunOnStringResult(BaseModel):
    result: CodemodRunResult


class RunFunctionRequest(BaseModel):
    codemod_source: str
    function_name: str
    commit: bool = False
