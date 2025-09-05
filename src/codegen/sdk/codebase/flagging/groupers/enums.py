from enum import StrEnum


class GroupBy(StrEnum):
    ALL = "all"
    APP = "app"
    CODEOWNER = "codeowner"
    FILE = "file"
    FILE_CHUNK = "file_chunk"
    HOT_COLD = "hot_cold"
    INSTANCE = "instance"
