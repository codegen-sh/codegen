from enum import IntFlag, auto
from typing import TypedDict

from typing_extensions import ReadOnly

from codegen.sdk.shared.decorators.docs import apidoc


@apidoc
class MessageType(IntFlag):
    """Destination of the message

    Attributes:
        CODEGEN: Rendered in the diff preview
        GITHUB: Posted as a comment on the PR
        SLACK: Sent over slack
    """

    CODEGEN = auto()
    GITHUB = auto()
    SLACK = auto()


@apidoc
class FlagKwargs(TypedDict, total=False):
    """Kwargs for the flag_instance method of the Codebase class.

    Attributes:
        message: The message to be displayed in the diff preview or posted as a comment on the PR.
        message_type: Where the message will be sent (CODEGEN, GITHUB, SLACK)
        message_recipient: The recipient of the message.
    """

    message: ReadOnly[str | None]
    message_type: ReadOnly[MessageType]
    message_recipient: ReadOnly[str | None]
