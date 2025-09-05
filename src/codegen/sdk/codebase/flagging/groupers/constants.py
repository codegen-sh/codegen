from codegen.sdk.codebase.flagging.groupers.all_grouper import AllGrouper
from codegen.sdk.codebase.flagging.groupers.app_grouper import AppGrouper
from codegen.sdk.codebase.flagging.groupers.codeowner_grouper import CodeownerGrouper
from codegen.sdk.codebase.flagging.groupers.file_chunk_grouper import FileChunkGrouper
from codegen.sdk.codebase.flagging.groupers.file_grouper import FileGrouper
from codegen.sdk.codebase.flagging.groupers.instance_grouper import InstanceGrouper

ALL_GROUPERS = [
    AllGrouper,
    AppGrouper,
    CodeownerGrouper,
    FileChunkGrouper,
    FileGrouper,
    InstanceGrouper,
]
