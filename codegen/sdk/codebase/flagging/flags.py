from dataclasses import dataclass, field
from typing import TypeVar

from codegen.sdk.codebase.flagging.code_flag import CodeFlag
from codegen.sdk.codebase.flagging.enums import MessageType
from codegen.sdk.codebase.flagging.group import Group
from codegen.sdk.core.interfaces.editable import Editable
from codegen.sdk.shared.decorators.docs import noapidoc

Symbol = TypeVar("Symbol", bound=Editable)


@dataclass
class Flags:
    _flags: list[CodeFlag] = field(default_factory=list)
    _find_mode: bool = False
    _active_group: list[CodeFlag] | None = None

    def flag_instance(
        self,
        symbol: Symbol | None = None,
        message: str | None = None,
        message_type: MessageType = MessageType.GITHUB | MessageType.CODEGEN,
        message_recipient: str | None = None,
    ) -> CodeFlag[Symbol]:
        """Flags a symbol, file or import to enable enhanced tracking of changes and splitting into
        smaller PRs.

        This method should be called once per flaggable entity and should be called before any edits are made to the entity.
        Flags enable tracking of changes and can be used for various purposes like generating pull requests or applying changes selectively.

        Args:
            symbol (TSymbol | None): The symbol to flag. Can be None if just flagging a message.
            message (str | None): Optional message to associate with the flag.
            message_type (MessageType): The type of message. Defaults to MessageType.GITHUB and MessageType.CODEGEN.
            message_recipient (str | None): Optional recipient for the message.

        Returns:
            CodeFlag: A flag object representing the flagged entity.
        """
        flag = CodeFlag(symbol=symbol, message=message, message_type=message_type, message_recipient=message_recipient)
        if self._find_mode:
            self._flags.append(flag)
        return flag

    def should_fix(self, flag: CodeFlag) -> bool:
        """Returns True if the flag should be fixed based on the current mode and active group.

        Used to filter out flags that are not in the active group and determine if the flag should be processed or ignored.

        Args:
            flag (CodeFlag): The code flag to check.

        Returns:
            bool: True if the flag should be fixed, False if it should be ignored.
            Returns False in find mode.
            Returns True if no active group is set.
            Returns True if the flag's hash exists in the active group hashes.
        """
        if self._find_mode:
            return False
        elif self._active_group is None:
            return True
        else:
            return flag.hash in self._active_group_hashes

    @noapidoc
    def set_find_mode(self, find_mode: bool) -> None:
        self._find_mode = find_mode

    @noapidoc
    def set_active_group(self, group: Group) -> None:
        """Will only fix these flags."""
        # TODO - flesh this out more with Group datatype and GroupBy
        self._active_group = group.flags
        self._find_mode = False
        self._active_group_hashes = set(flag.hash for flag in group.flags)
