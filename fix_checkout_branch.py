def checkout_branch(self, branch_name: str | None, *, remote: bool = False, remote_name: str = "origin", create_if_missing: bool = True) -> CheckoutResult:
    """Attempts to check out the branch in the following order:
    - Check out the local branch by name
    - Check out the remote branch if it's been fetched
    - Creates a new branch from the current commit (with create=True)

    NOTE: if branch is already checked out this does nothing.
    TIP: Use remote=True if you want to always try to checkout the branch from a remote

    Args:
    ----
        branch_name (str): Name of the branch to checkout.
        create_if_missing: If the branch doesn't exist, create one
        remote: Checks out a branch from a Remote + tracks the Remote
        force (bool): If True, force checkout by resetting the current branch to HEAD.
                      If False, raise an error if the branch is dirty.

    Raises:
    ------
        GitCommandError: If there's an error with Git operations.
        RuntimeError: If the branch is dirty and force is not set.
    """
    if branch_name is None:
        branch_name = self.default_branch

    try:
        if self.is_branch_checked_out(branch_name):
            if remote:
                # If the branch is already checked out and we want to fetch it from the remote, reset --hard to the remote branch
                logger.info(f"Branch {branch_name} is already checked out locally. Resetting to remote branch: {remote_name}/{branch_name}")
                # TODO: would have to fetch the the remote branch first to retrieve latest changes
                self.git_cli.git.reset("--hard", f"{remote_name}/{branch_name}")
                return CheckoutResult.SUCCESS
            else:
                logger.info(f"Branch {branch_name} is already checked out! Skipping checkout_branch.")
                return CheckoutResult.SUCCESS

        # Check if there are changes that need to be preserved
        needs_stash = self.git_cli.is_dirty()
        if needs_stash:
            logger.info(f"Environment is dirty, stashing changes before checking out branch: {branch_name}.")
            self.stash_push()

        try:
            # If remote=True, create a local branch tracking the remote branch and checkout onto it
            if remote:
                res = self.fetch_remote(remote_name, refspec=f"{branch_name}:{branch_name}")
                if res is FetchResult.SUCCESS:
                    self.git_cli.git.checkout(branch_name)
                    if needs_stash:
                        logger.info(f"Applying stashed changes after checkout to branch: {branch_name}.")
                        self.stash_pop()
                    return CheckoutResult.SUCCESS
                if res is FetchResult.REFSPEC_NOT_FOUND:
                    logger.warning(f"Branch {branch_name} not found in remote {remote_name}. Unable to checkout remote branch.")
                    if needs_stash:
                        logger.info("Restoring stashed changes.")
                        self.stash_pop()
                    return CheckoutResult.NOT_FOUND

            # If the branch already exists, checkout onto it
            if branch_name in self.git_cli.heads:
                self.git_cli.heads[branch_name].checkout()
                if needs_stash:
                    logger.info(f"Applying stashed changes after checkout to branch: {branch_name}.")
                    self.stash_pop()
                return CheckoutResult.SUCCESS

            # If the branch does not exist and create_if_missing=True, create and checkout a new branch from the current commit
            elif create_if_missing:
                logger.info(f"Creating new branch {branch_name} from current commit: {self.git_cli.head.commit.hexsha}")
                new_branch = self.git_cli.create_head(branch_name)
                new_branch.checkout()
                if needs_stash:
                    logger.info(f"Applying stashed changes after checkout to new branch: {branch_name}.")
                    self.stash_pop()
                return CheckoutResult.SUCCESS
            else:
                if needs_stash:
                    logger.info("Restoring stashed changes.")
                    self.stash_pop()
                return CheckoutResult.NOT_FOUND

        except Exception as e:
            # If anything goes wrong, try to restore the stashed changes
            if needs_stash:
                try:
                    logger.info("An error occurred. Attempting to restore stashed changes.")
                    self.stash_pop()
                except Exception as stash_error:
                    logger.exception(f"Failed to restore stashed changes: {stash_error}")
            raise e

    except GitCommandError as e:
        if "fatal: ambiguous argument" in e.stderr:
            logger.warning(f"Branch {branch_name} was not found in remote {remote_name}. Unable to checkout.")
            return CheckoutResult.NOT_FOUND
        else:
            logger.exception(f"Error with Git operations: {e}")
            raise
