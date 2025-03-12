from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.sdk.codebase.flagging.code_flag import CodeFlag
from codegen.sdk.codebase.flagging.group import Group
from codegen.sdk.codebase.flagging.groupers.base_grouper import BaseGrouper
from codegen.sdk.codebase.flagging.groupers.enums import GroupBy
from codegen.shared.logging.get_logger import get_logger
from codegen.shared.string.csv_utils import comma_separated_to_list, list_to_comma_separated

logger = get_logger(__name__)

DEFAULT_CHUNK_SIZE = 5


class FileChunkGrouper(BaseGrouper):
    """Group flags by a chunk of files.
    Ex: if chunk size is 10 then a Group only contains flags from max 10 unique files.
    TODO: currently only supports a harcoded chunk size of 5.

    Segment is a comma separated list of filenames.
    """

    type: GroupBy = GroupBy.FILE_CHUNK

    @staticmethod
    def create_all_groups(flags: list[CodeFlag], repo_operator: RepoOperator | None = None) -> list[Group]:
        map = {f.filepath: f for f in flags}
        filenames = sorted(map.keys())
        chunks = chunk_list(filenames, DEFAULT_CHUNK_SIZE)
        groups = []
        for idx, chunk in enumerate(chunks):
            chunk_flags = [map[filename] for filename in chunk]
            groups.append(Group(id=idx, group_by=GroupBy.FILE_CHUNK, segment=list_to_comma_separated(chunk), flags=chunk_flags))
        return groups

    @staticmethod
    def create_single_group(flags: list[CodeFlag], segment: str, repo_operator: RepoOperator | None = None) -> Group:
        segment_filepaths = comma_separated_to_list(segment)
        all_segment_flags = [f for f in flags if f.filepath in segment_filepaths]
        if len(all_segment_flags) == 0:
            logger.warning(f"🤷‍♀️ No flags found for FILE_CHUNK segment: {segment_filepaths}")
        return Group(group_by=GroupBy.FILE_CHUNK, segment=segment, flags=all_segment_flags)


def chunk_list(lst: list, chk_size: int) -> list[list[str]]:
    for index in range(0, len(lst), chk_size):
        yield lst[index : index + chk_size]
