from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.sdk.codebase.flagging.code_flag import CodeFlag
from codegen.sdk.codebase.flagging.group import Group
from codegen.sdk.codebase.flagging.groupers.base_grouper import BaseGrouper
from codegen.sdk.codebase.flagging.groupers.enums import GroupBy
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class FileGrouper(BaseGrouper):
    """Group flags by file.
    Segment is the filename.
    """

    type: GroupBy = GroupBy.FILE

    @staticmethod
    def create_all_groups(flags: list[CodeFlag], repo_operator: RepoOperator | None = None) -> list[Group]:
        groups = []
        filenames = sorted(list({f.filepath for f in flags}))
        for idx, filename in enumerate(filenames):
            filename_flags = [flag for flag in flags if flag.filepath == filename]
            groups.append(Group(id=idx, group_by=GroupBy.FILE, segment=filename, flags=filename_flags))
        return groups

    @staticmethod
    def create_single_group(flags: list[CodeFlag], segment: str, repo_operator: RepoOperator | None = None) -> Group:
        segment_flags = [flag for flag in flags if flag.filepath == segment]
        if len(segment_flags) == 0:
            logger.warning(f"🤷‍♀️ No flags found for FILE segment: {segment}")
        return Group(group_by=GroupBy.FILE, segment=segment, flags=segment_flags)
