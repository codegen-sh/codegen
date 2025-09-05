from dataclasses import dataclass


@dataclass
class PullRequest:
    """A pull request created by a codemod."""

    url: str
    number: int
    title: str
