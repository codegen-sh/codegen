from dataclasses import dataclass
from typing import Generic, TypeVar

from codegen.sdk.codebase.flagging.enums import MessageType
from codegen.sdk.core.interfaces.editable import Editable

Symbol = TypeVar("Symbol", bound=Editable | None)


@dataclass
class CodeFlag(Generic[Symbol]):
    symbol: Symbol
    message: str | None = None  # a short desc of the code flag/violation. ex: enums should be ordered alphabetically
    message_type: MessageType = MessageType.GITHUB | MessageType.CODEGEN  # where to send the message (either Github or Slack)
    message_recipient: str | None = None  # channel ID or user ID to send the message (if message_type is SLACK)

    @property
    def hash(self) -> str:
        return self.symbol.span.model_dump_json()

    @property
    def filepath(self) -> str:
        return self.symbol.file.filepath if self.symbol else ""

    def __eq__(self, other):
        if self.symbol != other.symbol:
            return False
        if self.message != other.message:
            return False
        if self.message_type != other.message_type:
            return False
        return True

    def __repr__(self):
        return f"<CodeFlag symbol={self.symbol.span} message={self.message} message_type={self.message_type}>"
