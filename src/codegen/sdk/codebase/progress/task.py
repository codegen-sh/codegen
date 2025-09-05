from abc import ABC, abstractmethod


class Task(ABC):
    @abstractmethod
    def update(self, message: str, count: int | None = None) -> None:
        pass

    @abstractmethod
    def end(self) -> None:
        pass
