from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar

from lsprotocol import types

from codegen.sdk.core.interfaces.editable import Editable

if TYPE_CHECKING:
    from codegen.extensions.lsp.server import CodegenLanguageServer


class CodeAction(ABC):
    name: str
    kind: ClassVar[types.CodeActionKind] = types.CodeActionKind.Refactor

    def __init__(self):
        pass

    @abstractmethod
    def execute(self, server: "CodegenLanguageServer", node: Editable) -> None: ...

    @abstractmethod
    def is_applicable(self, server: "CodegenLanguageServer", node: Editable) -> bool: ...

    def to_command(self, uri: str, range: types.Range) -> types.Command:
        return types.Command(
            title=self.name,
            command=self.command_name(),
            arguments=[uri, range],
        )

    def to_lsp(self, uri: str, range: types.Range) -> types.CodeAction:
        return types.CodeAction(
            title=self.name,
            kind=self.kind,
            data=[self.command_name(), uri, range],
        )

    @classmethod
    def command_name(cls) -> str:
        return f"codegen-{cls.__name__}"
