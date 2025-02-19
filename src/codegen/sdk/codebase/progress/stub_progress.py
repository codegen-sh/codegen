from codegen.sdk.codebase.progress.progress import Progress
from codegen.sdk.codebase.progress.stub_task import StubTask


class StubProgress(Progress[StubTask]):
    def begin(self, message: str, count: int | None = None) -> StubTask:
        return StubTask()
