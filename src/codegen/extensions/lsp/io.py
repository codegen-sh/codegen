import pprint
from dataclasses import dataclass
from pathlib import Path

from attr import asdict
from lsprotocol import types
from lsprotocol.types import CreateFile, CreateFileOptions, DeleteFile, Position, Range, RenameFile, TextEdit
from pygls.workspace import TextDocument, Workspace

from codegen.sdk.codebase.io.file_io import FileIO
from codegen.sdk.codebase.io.io import IO
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


@dataclass
class File:
    doc: TextDocument | None
    path: Path
    change: TextEdit | None = None
    other_change: CreateFile | RenameFile | DeleteFile | None = None
    version: int = 0

    @property
    def deleted(self) -> bool:
        return self.other_change is not None and self.other_change.kind == "delete"

    @property
    def created(self) -> bool:
        return self.other_change is not None and self.other_change.kind == "create"

    @property
    def identifier(self) -> types.OptionalVersionedTextDocumentIdentifier:
        return types.OptionalVersionedTextDocumentIdentifier(uri=self.path.as_uri(), version=self.version)


class LSPIO(IO):
    base_io: FileIO
    workspace: Workspace
    files: dict[Path, File]

    def __init__(self, workspace: Workspace):
        self.workspace = workspace
        self.base_io = FileIO()
        self.files = {}

    def _get_doc(self, path: Path) -> TextDocument:
        uri = path.as_uri()
        logger.info(f"Getting document for {uri}")
        return self.workspace.get_text_document(uri)

    def _get_file(self, path: Path) -> File:
        if path not in self.files:
            doc = self._get_doc(path)
            self.files[path] = File(doc=doc, path=path, version=doc.version or 0)
        return self.files[path]

    def read_text(self, path: Path) -> str:
        file = self._get_file(path)
        if file.deleted:
            msg = f"File {path} has been deleted"
            raise FileNotFoundError(msg)
        if file.change:
            return file.change.new_text
        if file.created:
            return ""
        if file.doc is None:
            return self.base_io.read_text(path)
        return file.doc.source

    def read_bytes(self, path: Path) -> bytes:
        file = self._get_file(path)
        if file.deleted:
            msg = f"File {path} has been deleted"
            raise FileNotFoundError(msg)
        if file.change:
            return file.change.new_text.encode("utf-8")
        if file.created:
            return b""
        if file.doc is None:
            return self.base_io.read_bytes(path)
        return file.doc.source.encode("utf-8")

    def write_bytes(self, path: Path, content: bytes) -> None:
        logger.info(f"Writing bytes to {path}")
        start = Position(line=0, character=0)
        file = self._get_file(path)
        if self.file_exists(path):
            lines = self.read_text(path).splitlines()
            if len(lines) == 0:
                end = Position(line=0, character=0)
            else:
                end = Position(line=len(lines) - 1, character=len(lines[-1]))
            file.change = TextEdit(range=Range(start=start, end=end), new_text=content.decode("utf-8"))
        else:
            file.other_change = CreateFile(uri=path.as_uri(), options=CreateFileOptions())
            file.change = TextEdit(range=Range(start=start, end=start), new_text=content.decode("utf-8"))

    def save_files(self, files: set[Path] | None = None) -> None:
        logger.info(f"Saving files {files}")

    def check_changes(self) -> None:
        self.base_io.check_changes()

    def delete_file(self, path: Path) -> None:
        file = self._get_file(path)
        file.other_change = DeleteFile(uri=path.as_uri())
        self.base_io.delete_file(path)

    def file_exists(self, path: Path) -> bool:
        file = self._get_file(path)
        if file.deleted:
            return False
        if file.change:
            return True
        if file.created:
            return True
        if file.doc is None:
            return self.base_io.file_exists(path)
        try:
            file.doc.source
            return True
        except FileNotFoundError:
            return False

    def untrack_file(self, path: Path) -> None:
        self.base_io.untrack_file(path)

    def get_workspace_edit(self) -> types.WorkspaceEdit:
        document_changes = []
        for _, file in self.files.items():
            id = file.identifier
            if file.other_change:
                document_changes.append(file.other_change)
                file.other_change = None
            if file.change:
                document_changes.append(types.TextDocumentEdit(text_document=id, edits=[file.change]))
                file.version += 1
                file.change = None
        logger.info(f"Workspace edit: {pprint.pformat(list(map(asdict, document_changes)))}")
        return types.WorkspaceEdit(document_changes=document_changes)

    def update_file(self, path: Path, version: int | None = None) -> None:
        file = self._get_file(path)
        file.doc = self.workspace.get_text_document(path.as_uri())
        if version is not None:
            file.version = version

    def close_file(self, path: Path) -> None:
        file = self._get_file(path)
        file.doc = None
