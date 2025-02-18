from codegen.sdk.codebase.progress.task import Task


class StubTask(Task):
    def update(self, message: str, count: int | None = None) -> None:
        pass

    def end(self) -> None:
        pass
