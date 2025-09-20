from collections.abc import Callable
from difflib import unified_diff
from enum import IntEnum
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from codegen.sdk.codebase.diff_lite import ChangeType, DiffLite

if TYPE_CHECKING:
    from codegen.sdk.core.file import File


class TransactionPriority(IntEnum):
    Remove = 0  # Remove always has highest priority
    Edit = 1  # Edit always comes next (remove and edit are incompatible with each other, so it should error out)
    Insert = 2  # Insert is always the last of the edit operations
    # File operations happen last, since they will mess up all other transactions
    FileAdd = 10
    FileRename = 11
    FileRemove = 12


@runtime_checkable
class ContentFunc(Protocol):
    """A function executed to generate a content block dynamically."""

    def __call__(self) -> str: ...


class Transaction:
    start_byte: int
    end_byte: int
    file_path: Path
    priority: int | tuple
    transaction_order: TransactionPriority
    transaction_counter: int = 0

    def __init__(
        self,
        start_byte: int,
        end_byte: int,
        file_path: Path,
        priority: int | tuple = 0,
        new_content: str | None | Callable[[], str] = None,
    ) -> None:
        self.start_byte = start_byte
        assert self.start_byte >= 0
        self.end_byte = end_byte
        self.file_path = file_path
        self.priority = priority
        self._new_content = new_content
        self.transaction_id = Transaction.transaction_counter

        Transaction.transaction_counter += 1

    def __repr__(self) -> str:
        return f"<Transaction at bytes [{self.start_byte}:{self.end_byte}] on {self.file_path}>"

    def __hash__(self):
        return hash((self.start_byte, self.end_byte, self.file_path, self.priority, self.new_content))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False

        # Check for everything EXCEPT transaction_time
        return (
            self.start_byte == other.start_byte
            and self.end_byte == other.end_byte
            and self.file_path == other.file_path
            and self.priority == other.priority
            and self._new_content == other._new_content
        )

    @property
    def length(self):
        return self.end_byte - self.start_byte

    def execute(self):
        msg = "Transaction.execute() must be implemented by subclasses"
        raise NotImplementedError(msg)

    def get_diff(self) -> DiffLite:
        """Gets the diff produced by this transaction"""
        msg = "Transaction.get_diff() must be implemented by subclasses"
        raise NotImplementedError(msg)

    def diff_str(self):
        """Human-readable string representation of the change"""
        msg = "Transaction.diff_str() must be implemented by subclasses"
        raise NotImplementedError(msg)

    def _to_sort_key(transaction: "Transaction"):
        # Sort by:
        # 1. Descending start_byte
        # 2. Ascending transaction type
        # 3. Ascending priority
        # 4. Descending time of transaction=
        priority = (transaction.priority,) if isinstance(transaction.priority, int) else transaction.priority

        return -transaction.start_byte, transaction.transaction_order.value, priority, -transaction.transaction_id

    @cached_property
    def new_content(self) -> str | None:
        return self._new_content() if isinstance(self._new_content, ContentFunc) else self._new_content


class RemoveTransaction(Transaction):
    transaction_order = TransactionPriority.Remove

    exec_func: Callable[[], None] | None = None

    def __init__(self, start_byte: int, end_byte: int, file: "File", priority: int = 0, exec_func: Callable[[], None] | None = None) -> None:
        super().__init__(start_byte, end_byte, file.path, priority=priority)
        self.file = file
        self.exec_func = exec_func

    def _generate_new_content_bytes(self) -> bytes:
        content_bytes = self.file.content_bytes
        new_content_bytes = content_bytes[: self.start_byte] + content_bytes[self.end_byte :]
        return new_content_bytes

    def execute(self) -> None:
        """Removes the content between start_byte and end_byte"""
        self.file.write_bytes(self._generate_new_content_bytes())
        if self.exec_func:
            self.exec_func()

    def get_diff(self) -> DiffLite:
        """Gets the diff produced by this transaction"""
        return DiffLite(ChangeType.Modified, self.file_path, old_content=self.file.content_bytes)

    def diff_str(self) -> str:
        """Human-readable string representation of the change"""
        diff = "".join(unified_diff(self.file.content.splitlines(True), self._generate_new_content_bytes().decode("utf-8").splitlines(True)))
        return f"Remove {self.length} bytes at bytes ({self.start_byte}, {self.end_byte})\n{diff}"


class InsertTransaction(Transaction):
    transaction_order = TransactionPriority.Insert

    exec_func: Callable[[], None] | None = None

    def __init__(
        self,
        insert_byte: int,
        file: "File",
        new_content: str | Callable[[], str],
        *,
        priority: int | tuple = 0,
        exec_func: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(insert_byte, insert_byte, file.path, priority=priority, new_content=new_content)
        self.insert_byte = insert_byte
        self.file = file
        self.exec_func = exec_func

    def _generate_new_content_bytes(self) -> bytes:
        new_bytes = bytes(self.new_content, encoding="utf-8")
        content_bytes = self.file.content_bytes
        head = content_bytes[: self.insert_byte]
        tail = content_bytes[self.insert_byte :]
        new_content_bytes = head + new_bytes + tail
        return new_content_bytes

    def execute(self) -> None:
        """Inserts new_src at the specified byte_index"""
        self.file.write_bytes(self._generate_new_content_bytes())
        if self.exec_func:
            self.exec_func()

    def get_diff(self) -> DiffLite:
        """Gets the diff produced by this transaction"""
        return DiffLite(ChangeType.Modified, self.file_path, old_content=self.file.content_bytes)

    def diff_str(self) -> str:
        """Human-readable string representation of the change"""
        diff = "".join(unified_diff(self.file.content.splitlines(True), self._generate_new_content_bytes().decode("utf-8").splitlines(True)))
        return f"Insert {len(self.new_content)} bytes at bytes ({self.start_byte}, {self.end_byte})\n{diff}"


class EditTransaction(Transaction):
    transaction_order = TransactionPriority.Edit
    new_content: str

    def __init__(
        self,
        start_byte: int,
        end_byte: int,
        file: "File",
        new_content: str,
        priority: int = 0,
    ) -> None:
        super().__init__(start_byte, end_byte, file.path, priority=priority, new_content=new_content)
        self.file = file

    def _generate_new_content_bytes(self) -> bytes:
        new_bytes = bytes(self.new_content, "utf-8")
        content_bytes = self.file.content_bytes
        new_content_bytes = content_bytes[: self.start_byte] + new_bytes + content_bytes[self.end_byte :]
        return new_content_bytes

    def execute(self) -> None:
        """Edits the entirety of this node's source to new_src"""
        self.file.write_bytes(self._generate_new_content_bytes())

    def get_diff(self) -> DiffLite:
        """Gets the diff produced by this transaction"""
        return DiffLite(ChangeType.Modified, self.file_path, old_content=self.file.content_bytes)

    def diff_str(self) -> str:
        """Human-readable string representation of the change"""
        diff = "".join(unified_diff(self.file.content.splitlines(True), self._generate_new_content_bytes().decode("utf-8").splitlines(True)))
        return f"Edit {self.length} bytes at bytes ({self.start_byte}, {self.end_byte}), src: ({self.new_content[:50]})\n{diff}"

    def break_down(self) -> list[InsertTransaction] | None:
        old = self.file.content_bytes[self.start_byte : self.end_byte]
        new = bytes(self.new_content, "utf-8")
        if old and old in new:
            prefix, suffix = new.split(old, maxsplit=1)
            ret = []
            if suffix:
                ret.append(InsertTransaction(self.end_byte, self.file, suffix.decode("utf-8"), priority=self.priority))
            if prefix:
                ret.append(InsertTransaction(self.start_byte, self.file, prefix.decode("utf-8"), priority=self.priority))
            return ret
        return None


class FileAddTransaction(Transaction):
    transaction_order = TransactionPriority.FileAdd

    def __init__(
        self,
        file_path: Path,
        priority: int = 0,
    ) -> None:
        super().__init__(0, 0, file_path, priority=priority)

    def execute(self) -> None:
        """Adds a new file"""
        pass  # execute is a no-op as the file is immediately added

    def get_diff(self) -> DiffLite:
        """Gets the diff produced by this transaction"""
        return DiffLite(ChangeType.Added, self.file_path)

    def diff_str(self) -> str:
        """Human-readable string representation of the change"""
        return f"Add file at {self.file_path}"


class FileRenameTransaction(Transaction):
    transaction_order = TransactionPriority.FileRename

    def __init__(
        self,
        file: "File",
        new_file_path: str,
        priority: int = 0,
    ) -> None:
        super().__init__(0, 0, file.path, priority=priority, new_content=new_file_path)
        self.new_file_path = file.ctx.to_absolute(new_file_path)
        self.file = file

    def execute(self) -> None:
        """Renames the file"""
        self.file.ctx.io.save_files({self.file.path})
        self.file_path.rename(self.new_file_path)

    def get_diff(self) -> DiffLite:
        """Gets the diff produced by this transaction"""
        return DiffLite(ChangeType.Renamed, self.file_path, self.file_path, self.new_file_path, old_content=self.file.content_bytes)

    def diff_str(self) -> str:
        """Human-readable string representation of the change"""
        return f"Rename file from {self.file_path} to {self.new_file_path}"


class FileRemoveTransaction(Transaction):
    transaction_order = TransactionPriority.FileRemove

    def __init__(
        self,
        file: "File",
        priority: int = 0,
    ) -> None:
        super().__init__(0, 0, file.path, priority=priority)
        self.file = file

    def execute(self) -> None:
        """Removes the file"""
        self.file.ctx.io.delete_file(self.file.path)

    def get_diff(self) -> DiffLite:
        """Gets the diff produced by this transaction"""
        return DiffLite(ChangeType.Removed, self.file_path, old_content=self.file.content_bytes)

    def diff_str(self) -> str:
        """Human-readable string representation of the change"""
        return f"Remove file at {self.file_path}"
