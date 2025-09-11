from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from codegen.sdk.codebase.progress.task import Task

T = TypeVar("T", bound="Task")


class Progress(ABC, Generic[T]):
    @abstractmethod
    def begin(self, message: str, count: int | None = None) -> T:
        pass
