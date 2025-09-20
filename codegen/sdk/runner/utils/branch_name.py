from uuid import uuid4

from codegen.sdk.codebase.flagging.group import Group


def get_head_branch_name(branch_name: str | None, group: Group | None = None) -> str:
    if branch_name is None:
        branch_name = f"codegen-{uuid4()}"
    if group:
        return f"{branch_name}-group-{group.id}"
    return branch_name
