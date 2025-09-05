from codegen.sdk.codebase.flagging.groupers.all_grouper import AllGrouper
from codegen.sdk.codebase.flagging.groupers.base_grouper import BaseGrouper
from codegen.sdk.codebase.flagging.groupers.constants import ALL_GROUPERS
from codegen.sdk.codebase.flagging.groupers.enums import GroupBy


def get_grouper_by_group_by(group_by: GroupBy | None) -> type[BaseGrouper]:
    if group_by is None:
        return AllGrouper
    matched_groupers = [x for x in ALL_GROUPERS if x.type == group_by]
    if len(matched_groupers) > 0:
        return matched_groupers[0]
    msg = f"No grouper found for group_by={group_by}. Did you add to ALL_GROUPERS?"
    raise ValueError(msg)
