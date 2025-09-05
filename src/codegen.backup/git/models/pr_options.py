from pydantic import BaseModel

from codegen.shared.decorators.docs import apidoc


@apidoc
class PROptions(BaseModel):
    """Options for generating a PR.

    Attributes:
        title: The title of the pull request.
        body: The body content of the pull request.
        labels: A list of labels to be added to the pull request.
        force_push_head_branch: Whether to force push the head branch.
    """

    title: str | None = None
    body: str | None = None
    labels: list[str] | None = None  # TODO: not used until we add labels to GithubPullRequestModel
    force_push_head_branch: bool | None = None
