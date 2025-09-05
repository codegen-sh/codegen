from enum import StrEnum, auto


class SetupOption(StrEnum):
    # always do a fresh clone (if the repo already exists it will delete the dir first)
    CLONE = auto()
    # if the repo already exists, pull latest, else clone
    PULL_OR_CLONE = auto()
    # do nothing (useful if you want to use an existing repo in it's current state)
    SKIP = auto()
    # only initialize the repo
    INIT = auto()


class FetchResult(StrEnum):
    SUCCESS = "SUCCESS"
    REFSPEC_NOT_FOUND = "REFSPEC_NOT_FOUND"


class CheckoutResult(StrEnum):
    SUCCESS = "SUCCESS"
    NOT_FOUND = "BRANCH_NOT_FOUND"


class DiffChangeType(StrEnum):
    ADDED = "A"
    DELETED = "D"
    RENAMED = "R"
    MODIFIED = "M"


class RepoVisibility(StrEnum):
    PRIVATE = auto()
    PUBLIC = auto()
    INTERNAL = auto()
