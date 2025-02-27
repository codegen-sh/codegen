from codegen.sdk.codebase.factory.codebase_factory import CodebaseType
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class SandboxRepo:
    """Responsible for managing the state of the git repo stored in the sandbox runner"""

    codebase: CodebaseType

    def __init__(self, codebase: CodebaseType) -> None:
        self.codebase = codebase

    def set_up_base_branch(self, base_branch: str | None) -> None:
        """Set-up base branch by pushing latest highside branch to lowside and checking out the branch."""
        # If base branch is already checked out, do nothing
        if self.codebase.op.is_branch_checked_out(base_branch):
            return

        # fetch the base branch from highside (do not checkout yet)
        highside_remote = self.codebase.op.git_cli.remote(name="origin")
        self.codebase.op.fetch_remote(highside_remote.name, refspec=f"{base_branch}:{base_branch}")

        # checkout the base branch (and possibly sync graph)
        self.codebase.checkout(branch=base_branch)

    def set_up_head_branch(self, head_branch: str, force_push_head_branch: bool):
        """Set-up head branch by pushing latest highside branch to lowside and fetching the branch (so that it can be checked out later)."""
        # If head branch is not specified, do nothing
        if head_branch is None:
            return

        if head_branch and head_branch == self.codebase.default_branch:
            # NOTE: assuming that the main branch is always protected, instead should pull this from github (but it requires admin permissions)
            error = f"Branch {head_branch} is protected and cannot be used as the head branch!"
            logger.error(error)
            raise ValueError(error)

        # If are force pushing the head branch, don't checkout the remote.
        # This will cause set-up group to create a new branch off of master by the same name
        if force_push_head_branch:
            return

        # fetch the head branch from highside (do not checkout yet)
        highside_remote = self.codebase.op.git_cli.remote(name="origin")
        self.codebase.op.fetch_remote(highside_remote.name, refspec=f"{head_branch}:{head_branch}")

    def reset_branch(self, base_branch: str, head_branch: str) -> None:
        logger.info(f"Checking out base branch {base_branch} ...")
        self.codebase.checkout(branch=base_branch, create_if_missing=True)
        # =====[ Checkout head branch ]=====
        logger.info(f"Checking out head branch {head_branch} ...")
        self.codebase.checkout(branch=head_branch, create_if_missing=True)

    def push_changes_to_remote(self, commit_msg: str, head_branch: str, force_push: bool) -> bool:
        """Takes current state of repo and pushes it"""
        # =====[ Stage changes ]=====
        has_staged_commit = self.codebase.git_commit(f"[Codegen] {commit_msg}")
        if not has_staged_commit:
            logger.info("Skipping opening pull request for cm_run b/c the codemod produced no changes")
            return False

        # =====[ Push changes highside ]=====
        highside_remote = self.codebase.op.git_cli.remote(name="origin")
        highside_res = self.codebase.op.push_changes(remote=highside_remote, refspec=f"{head_branch}:{head_branch}", force=force_push)
        return not any(push_info.flags & push_info.ERROR for push_info in highside_res)

    # TODO: move bunch of codebase git operations into this class.
    # The goal is to make the codebase class ONLY allow RepoOperator.
