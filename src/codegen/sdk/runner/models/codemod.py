"""Dataclasses used by the sandbox runners"""

from datetime import datetime

from pydantic import BaseModel

from codegen.sdk.codebase.flagging.groupers.enums import GroupBy
from codegen.sdk.git.models.codemod_context import CodemodContext
from codegen.sdk.git.models.pr_options import PROptions


class Codemod(BaseModel):
    user_code: str
    codemod_context: CodemodContext = CodemodContext()


class GroupingConfig(BaseModel):
    subdirectories: list[str] | None = None
    group_by: GroupBy | None = None
    max_prs: int | None = None


class BranchConfig(BaseModel):
    branch_name: str | None = None
    custom_base_branch: str | None = None
    custom_head_branch: str | None = None
    force_push_head_branch: bool = False


class CodemodRunResult(BaseModel):
    is_complete: bool = False
    observation: str | None = None
    visualization: dict | None = None
    observation_meta: dict | None = None
    base_commit: str | None = None
    logs: str | None = None
    error: str | None = None
    completed_at: datetime | None = None
    highlighted_diff: str | None = None
    pr_options: PROptions | None = None
    flags: list[dict] | None = None


class CreatedBranch(BaseModel):
    base_branch: str
    head_ref: str | None = None


class SandboxRunnerTag(BaseModel):
    repo_id: str
    runner_id: str
