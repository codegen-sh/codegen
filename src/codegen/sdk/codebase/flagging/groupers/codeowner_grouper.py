from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.sdk.codebase.flagging.code_flag import CodeFlag
from codegen.sdk.codebase.flagging.group import Group
from codegen.sdk.codebase.flagging.groupers.base_grouper import BaseGrouper
from codegen.sdk.codebase.flagging.groupers.enums import GroupBy

DEFAULT_CHUNK_SIZE = 5


class CodeownerGrouper(BaseGrouper):
    """Group flags by CODEOWNERS.

    Parses .github/CODEOWNERS and groups by each possible codeowners

    Segment should be either a github username or github team name.
    """

    type: GroupBy = GroupBy.CODEOWNER

    @staticmethod
    def create_all_groups(flags: list[CodeFlag], repo_operator: RepoOperator | None = None) -> list[Group]:
        owner_to_group: dict[str, Group] = {}
        no_owner_group = Group(group_by=GroupBy.CODEOWNER, segment="@no-owner", flags=[])
        for idx, flag in enumerate(flags):
            flag_owners = repo_operator.codeowners_parser.of(flag.filepath)  # TODO: handle codeowners_parser could be null
            if not flag_owners:
                no_owner_group.flags.append(flag)
                continue
            # NOTE: always use the first owner. ex if the line is /dir @team1 @team2 then use team1
            flag_owner = flag_owners[0][1]
            group = owner_to_group.get(flag_owner, Group(id=idx, group_by=GroupBy.CODEOWNER, segment=flag_owner, flags=[]))
            group.flags.append(flag)
            owner_to_group[flag_owner] = group

        no_owner_group.id = len(owner_to_group)
        return [*list(owner_to_group.values()), no_owner_group]

    @staticmethod
    def create_single_group(flags: list[CodeFlag], segment: str, repo_operator: RepoOperator | None = None) -> Group:
        msg = "TODO: implement single group creation"
        raise NotImplementedError(msg)
