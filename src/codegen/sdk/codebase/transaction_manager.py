import time
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from codegen.sdk.codebase.diff_lite import ChangeType, DiffLite
from codegen.sdk.codebase.transactions import (
    EditTransaction,
    FileAddTransaction,
    FileRemoveTransaction,
    FileRenameTransaction,
    RemoveTransaction,
    Transaction,
    TransactionPriority,
)
from codegen.shared.exceptions.control_flow import MaxPreviewTimeExceeded, MaxTransactionsExceeded
from codegen.shared.logging.get_logger import get_logger

if TYPE_CHECKING:
    from codegen.sdk.core.file import File


logger = get_logger(__name__)


class TransactionError(Exception):
    pass


class TransactionManager:
    """Responsible for handling `Transaction` objects - basically an atomic modification of a codebase.

    This is used by the Codebase class to queue up transactions and then commit them in bulk.
    """

    # Unsorted list of transactions, grouped by file
    # TODO: consider using SortedList for better performance
    queued_transactions: dict[Path, list[Transaction]]
    pending_undos: set[Callable[[], None]]
    _commiting: bool = False
    max_transactions: int | None = None  # None = no limit
    stopwatch_start = None
    stopwatch_max_seconds: int | None = None  # None = no limit

    def __init__(self) -> None:
        self.queued_transactions = dict()
        self.pending_undos = set()

    def sort_transactions(self) -> None:
        for file_path, file_transactions in self.queued_transactions.items():
            file_transactions.sort(key=Transaction._to_sort_key)

    def clear_transactions(self) -> None:
        """Should be called between tests to remove any potential extraneous transactions. Makes sure we reset max_transactions as well."""
        if len(self.queued_transactions) > 0:
            logger.warning("Not all transactions have been committed")
            self.queued_transactions.clear()
        for undo in self.pending_undos:
            undo()
        self.pending_undos.clear()
        self.set_max_transactions(None)
        self.reset_stopwatch()

    def _format_transactions(self, transactions: list[Transaction]) -> str:
        return "\n".join([">" * 100 + f"\n[ID: {t.transaction_id}]: {t.diff_str()}" + "<" * 100 for t in transactions])

    def get_transactions_str(self) -> str:
        """Returns a human-readable string representation of the transactions"""
        return "\n\n\n".join([f"{file_path}:\n{self._format_transactions(transactions)}" for file_path, transactions in self.queued_transactions.items()])

    ####################################################################################################################
    # Transation Limits
    ####################################################################################################################

    def get_num_transactions(self) -> int:
        """Returns total number of transactions created to date"""
        return sum([len(transactions) for transactions in self.queued_transactions.values()])

    def set_max_transactions(self, max_transactions: int | None = None) -> None:
        self.max_transactions = max_transactions

    def max_transactions_exceeded(self) -> bool:
        """Util method to check if the max transactions limit has been exceeded."""
        if self.max_transactions is None:
            return False
        return self.get_num_transactions() >= self.max_transactions

    ####################################################################################################################
    # Stopwatch
    ####################################################################################################################

    def reset_stopwatch(self, max_seconds: int | None = None) -> int:
        self.stopwatch_start = time.time()
        self.stopwatch_max_seconds = max_seconds

    def is_time_exceeded(self) -> bool:
        if self.stopwatch_max_seconds is None:
            return False
        else:
            num_seconds = time.time() - self.stopwatch_start
            return num_seconds > self.stopwatch_max_seconds

    ####################################################################################################################
    # Transaction Creation
    ####################################################################################################################

    def add_file_add_transaction(self, filepath: Path) -> None:
        t = FileAddTransaction(filepath)
        self.add_transaction(t)

    def add_file_rename_transaction(self, file: "File", new_filepath: str) -> None:
        t = FileRenameTransaction(file, new_filepath)
        self.add_transaction(t)

    def add_file_remove_transaction(self, file: "File") -> None:
        t = FileRemoveTransaction(file)
        self.add_transaction(t)

    def add_transaction(self, transaction: Transaction, dedupe: bool = True, solve_conflicts: bool = True) -> bool:
        # Get the list of transactions for the file
        file_path = transaction.file_path
        if file_path not in self.queued_transactions:
            self.queued_transactions[file_path] = []
        file_queue = self.queued_transactions[file_path]

        # Dedupe transactions
        if dedupe and transaction in file_queue:
            logger.debug(f"Transaction already exists in queue: {transaction}")
            return False
        # Solve conflicts
        if new_transaction := self._resolve_conflicts(transaction, file_queue, solve_conflicts=solve_conflicts):
            file_queue.append(new_transaction)

        self.check_limits()
        return True

    def check_limits(self):
        self.check_max_transactions()
        self.check_max_preview_time()

    def check_max_transactions(self):
        # =====[ Max transactions ]=====
        # max_transactions is set so that long-running codemods terminate early so we can quickly surface a subset
        # of the results to the user. This may result in errors that do not get covered.
        if self.max_transactions_exceeded():
            logger.info(f"Max transactions reached: {self.max_transactions}. Stopping codemod.")
            msg = f"Max transactions reached: {self.max_transactions}"
            raise MaxTransactionsExceeded(msg, threshold=self.max_transactions)

    def check_max_preview_time(self):
        # =====[ Max preview time ]=====
        # This is to prevent the preview from taking too long. We want to keep it at like ~5s in the frontend during debugging
        if self.is_time_exceeded():
            logger.info(f"Max preview time exceeded: {self.stopwatch_max_seconds}. Stopping codemod.")
            msg = f"Max preview time exceeded: {self.is_time_exceeded()}"
            raise MaxPreviewTimeExceeded(msg, threshold=self.stopwatch_max_seconds)

    ####################################################################################################################
    # Commit
    ####################################################################################################################

    def to_commit(self, files: set[Path] | None = None) -> set[Path]:
        """Get node ids of files to commit"""
        if files is None:
            return set(self.queued_transactions.keys())
        return files.intersection(self.queued_transactions)

    def commit(self, files: set[Path]) -> list[DiffLite]:
        """Execute transactions in bulk for each file, in reverse order of start_byte.
        Returns the list of diffs that were committed.
        """
        if self._commiting:
            logger.warn("Skipping commit, already committing")
            return []
        self._commiting = True
        try:
            diffs: list[DiffLite] = []
            if not self.queued_transactions or len(self.queued_transactions) == 0:
                return diffs

            self.sort_transactions()

            # TODO: raise error if two transactions byte ranges overlap with each other
            if len(files) > 3:
                num_transactions = sum([len(self.queued_transactions[file_path]) for file_path in files])
                logger.info(f"Committing {num_transactions} transactions for {len(files)} files")
            else:
                for file in files:
                    logger.info(f"Committing {len(self.queued_transactions[file])} transactions for {file}")
            for file_path in files:
                file_transactions = self.queued_transactions.pop(file_path, [])
                modified = False
                for transaction in file_transactions:
                    # Add diff IF the file is a source file
                    diff = transaction.get_diff()
                    if diff.change_type == ChangeType.Modified:
                        if not modified:
                            modified = True
                            diffs.append(diff)
                    else:
                        diffs.append(diff)
                    transaction.execute()
            return diffs
        finally:
            self._commiting = False

    ####################################################################################################################
    # Conflict Resolution
    ####################################################################################################################

    def _resolve_conflicts(self, transaction: Transaction, file_queue: list[Transaction], solve_conflicts: bool = True) -> Transaction | None:
        def break_down(to_break: EditTransaction) -> bool:
            if new_transactions := to_break.break_down():
                try:
                    insert_idx = file_queue.index(to_break)
                    file_queue.pop(insert_idx)
                except ValueError:
                    insert_idx = len(file_queue)
                for new_transaction in new_transactions:
                    if broken_down := self._resolve_conflicts(new_transaction, file_queue, solve_conflicts=solve_conflicts):
                        file_queue.insert(insert_idx, broken_down)
                return True
            return False

        try:
            conflicts = self._get_conflicts(transaction)
            if solve_conflicts and conflicts:
                # Check if the current transaction completely overlaps with any existing transaction
                if (completely_overlapping := self._get_overlapping_conflicts(transaction)) is not None:
                    # If it does, check the overlapping transaction's type
                    # If the overlapping transaction is a remove, remove the current transaction
                    if isinstance(completely_overlapping, RemoveTransaction):
                        return None
                    # If the overlapping transaction is an edit, raise an error
                    elif isinstance(completely_overlapping, EditTransaction):
                        if break_down(completely_overlapping):
                            return transaction

                        raise TransactionError()
                else:
                    # If current transaction is deleted, remove all conflicting transactions
                    if isinstance(transaction, RemoveTransaction):
                        for t in conflicts:
                            file_queue.remove(t)
                    # If current transaction is edit, raise an error
                    elif isinstance(transaction, EditTransaction):
                        if break_down(transaction):
                            return None
                        raise TransactionError()

            # Add to priority queue and rebuild the queue
            return transaction
        except TransactionError as e:
            logger.exception(e)
            msg = (
                f"Potential conflict detected in file {transaction.file_path}!\n"
                "Attempted to perform code modification:\n"
                "\n"
                f"{self._format_transactions([transaction])}\n"
                "\n"
                "That potentially conflicts with the following other modifications:\n"
                "\n"
                f"{self._format_transactions(conflicts)}\n"
                "\n"
                "Aborting!\n"
                "\n"
                f"[Conflict Detected] Potential Modification Conflict in File {transaction.file_path}!"
            )
            raise TransactionError(msg)

    def get_transactions_at_range(self, file_path: Path, start_byte: int, end_byte: int, transaction_order: TransactionPriority | None = None, *, combined: bool = False) -> list[Transaction]:
        """Returns list of queued transactions that matches the given filtering criteria.

        Args:
            combined: Return a list of transactions which collectively apply to the given range
        """
        matching_transactions = []
        if file_path not in self.queued_transactions:
            return matching_transactions

        for t in self.queued_transactions[file_path]:
            if t.start_byte == start_byte:
                if t.end_byte == end_byte:
                    if transaction_order is None or t.transaction_order == transaction_order:
                        matching_transactions.append(t)
                elif combined and t.start_byte != t.end_byte:
                    if other := self.get_transactions_at_range(t.file_path, t.end_byte, end_byte, transaction_order, combined=combined):
                        return [t, *other]

        return matching_transactions

    def _get_conflicts(self, transaction: Transaction) -> list[Transaction]:
        """Returns all transactions that overlap with the given transaction"""
        overlapping_transactions = []
        queued_transactions = list(self.queued_transactions[transaction.file_path])
        for t in queued_transactions:
            if transaction.start_byte < t.end_byte and transaction.end_byte > t.start_byte:
                overlapping_transactions.append(t)
        return overlapping_transactions

    def _get_overlapping_conflicts(self, transaction: Transaction) -> Transaction | None:
        """Returns the transaction that completely overlaps with the given transaction"""
        for t in self.queued_transactions[transaction.file_path]:
            if transaction.start_byte >= t.start_byte and transaction.end_byte <= t.end_byte:
                return t
        return None
