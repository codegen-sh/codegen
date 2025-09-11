import uuid

from lsprotocol import types
from lsprotocol.types import ProgressToken
from pygls.lsp.server import LanguageServer

from codegen.sdk.codebase.progress.progress import Progress
from codegen.sdk.codebase.progress.stub_task import StubTask
from codegen.sdk.codebase.progress.task import Task


class LSPTask(Task):
    count: int | None

    def __init__(self, server: LanguageServer, message: str, token: ProgressToken, count: int | None = None, create_token: bool = True) -> None:
        self.token = token
        if create_token:
            server.work_done_progress.begin(self.token, types.WorkDoneProgressBegin(title=message))
        self.server = server
        self.message = message
        self.count = count
        self.create_token = create_token

    def update(self, message: str, count: int | None = None) -> None:
        if self.count is not None and count is not None:
            percent = int(count * 100 / self.count)
        else:
            percent = None
        self.server.work_done_progress.report(self.token, types.WorkDoneProgressReport(message=message, percentage=percent))

    def end(self) -> None:
        if self.create_token:
            self.server.work_done_progress.end(self.token, value=types.WorkDoneProgressEnd())


class LSPProgress(Progress[LSPTask | StubTask]):
    initialized = False

    def __init__(self, server: LanguageServer, initial_token: ProgressToken | None = None):
        self.server = server
        self.initial_token = initial_token
        if initial_token is not None:
            self.server.work_done_progress.begin(initial_token, types.WorkDoneProgressBegin(title="Parsing codebase..."))

    def begin_with_token(self, message: str, token: ProgressToken | None = None, *, count: int | None = None, create_token: bool = True) -> LSPTask | StubTask:
        if token is None:
            return StubTask()
        return LSPTask(self.server, message, token, count, create_token=create_token)

    def begin(self, message: str, count: int | None = None) -> LSPTask | StubTask:
        if self.initialized:
            token = str(uuid.uuid4())
            self.server.work_done_progress.create(token).result()
            return LSPTask(self.server, message, token, count, create_token=False)
        return self.begin_with_token(message, self.initial_token, count=None, create_token=False)

    def finish_initialization(self) -> None:
        self.initialized = False  # We can't initiate server work during syncs
        if self.initial_token is not None:
            self.server.work_done_progress.end(self.initial_token, value=types.WorkDoneProgressEnd())
