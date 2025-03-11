import time
from collections import defaultdict, deque
from datetime import datetime
from typing import Optional

import pygit2
from intervaltree import IntervalTree
from pygit2 import Commit, Patch
from pygit2.enums import CheckoutStrategy, DeltaStatus, SortMode

from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.symbol import Symbol


class GitAttributionTracker:
    """Tracks attribution information for code symbols based on git history."""

    def __init__(self, codebase: Codebase, ai_authors: Optional[list[str]] = None):
        """Initialize the attribution tracker.

        Args:
            codebase: The codebase to analyze
            ai_authors: List of author names/emails to track as AI contributors
                        (defaults to ['devin[bot]', 'codegen[bot]'])
        """
        self.codebase = codebase
        self.repo_path = codebase.ctx.projects[0].repo_operator.repo_path
        self.repo = pygit2.Repository(self.repo_path)
        self.org_branch_reference = self.repo.head
        # Default AI authors if none provided
        self.ai_authors = ai_authors or ["devin[bot]", "codegen[bot]"]

        # Cache structures
        self._file_history = {}  # file path -> list of commit info
        self._symbol_history: defaultdict[str, list] = defaultdict(list)  # symbol id -> list of commit info
        self._author_contributions = defaultdict(list)  # author -> list of commit info

        # Track if history has been built
        self._history_built = False

        self._file_symbol_location_state: dict[str, IntervalTree] = {}

        self._commits: deque[Commit]

    def build_history(self, max_commits: Optional[int] = None) -> None:
        """Build the git history for the codebase.

        Args:
            max_commits: Maximum number of commits to process (None for all)
        """
        start_time = time.time()
        print(f"Building git history for {self.repo_path}...")

        # Check if repository exists and has commits
        try:
            head = self.repo.head
        except Exception as e:
            print(f"⚠️ Error accessing repository head: {e}")
            print("This might be a shallow clone or a repository without history.")
            self._history_built = True
            return

        # Walk through commit history
        commit_count = 0
        author_set = set()

        self._commits = deque()
        try:
            for commit in self.repo.walk(self.repo.head.target, SortMode.TIME):
                # Track unique authors
                author_id = f"{commit.author.name} <{commit.author.email}>"
                author_set.add(author_id)
                self._commits.append(commit)
                # Process each diff in the commit
                if len(commit.parents) > 0:
                    try:
                        diff = self.repo.diff(commit.parents[0], commit)
                        self._process_commit(commit, diff)
                    except Exception as e:
                        print(f"Error processing commit {commit.id}: {e}")
                else:
                    # Initial commit (no parents)
                    try:
                        # For initial commit, compare with empty tree
                        diff = commit.tree.diff_to_tree(context_lines=0)
                        self._process_commit(commit, diff)
                    except Exception as e:
                        print(f"Error processing initial commit {commit.id}: {e}")

                commit_count += 1
                if max_commits and commit_count >= max_commits:
                    break

                # Progress indicator
                if commit_count % 100 == 0:
                    print(f"Processed {commit_count} commits...")

        except Exception as e:
            print(f"⚠️ Error walking commit history: {e}")

        self._history_built = True
        elapsed = time.time() - start_time

        # Print diagnostic information
        print(f"Finished building history in {elapsed:.2f} seconds.")
        print(f"Processed {commit_count} commits from {len(author_set)} unique authors.")
        print(f"Found {len(self._file_history)} files with history.")
        print(f"Found {len(self._author_contributions)} contributors.")

        if len(self._author_contributions) > 0:
            print("Top contributors:")
            top_contributors = sorted([(author, len(commits)) for author, commits in self._author_contributions.items()], key=lambda x: x[1], reverse=True)[:5]
            for author, count in top_contributors:
                print(f"  • {author}: {count} commits")
        else:
            print("⚠️ No contributors found. This might be due to:")
            print("  1. Using a shallow clone without history")
            print("  2. Repository access issues")
            print("  3. Empty repository or no commits")

    def _process_commit(self, commit, diff) -> None:
        """Process a single commit and its diff."""
        author_name = commit.author.name
        author_email = commit.author.email
        author_id = f"{author_name} <{author_email}>"
        timestamp = commit.author.time
        commit_id = str(commit.id)

        commit_info = {
            "author": author_name,
            "email": author_email,
            "timestamp": timestamp,
            "commit_id": commit_id,
            "message": commit.message.strip(),
        }

        # Track by author
        self._author_contributions[author_id].append(commit_info)

        # Track by file
        for patch in diff:
            file_path = patch.delta.new_file.path

            # Skip if not a source file we care about
            if not self._is_tracked_file(file_path):
                continue

            if file_path not in self._file_history:
                self._file_history[file_path] = []

            file_commit = commit_info.copy()
            file_commit["file_path"] = file_path
            self._file_history[file_path].append(file_commit)

    def _process_symbol_location_state(self, filepaths: list[str]):
        for filepath in filepaths:
            file = self.codebase.get_file(filepath)
            filetree = IntervalTree()
            try:
                for symbol in file.symbols:
                    symbol: Symbol
                    start_line = symbol.range.start_point.row + 1  # 1 Indexing
                    end_line = symbol.range.end_point.row + 2  # Intervaltree is end non-inclusive
                    filetree.addi(start_line, end_line, symbol)
            except Exception as e:
                pass
            self._file_symbol_location_state[filepath] = filetree

    def _get_symbols_affected_by_patch(self, patch: Patch, filepath):
        if filepath not in self._file_symbol_location_state:
            return []
        symbols_affected = set()
        for hunk in patch.hunks:
            start = hunk.new_start
            end = start + hunk.new_lines  # Intervaltree is end non-inclusive
            for interval in self._file_symbol_location_state[filepath].overlap(start, end):
                symbols_affected.add(interval[2])

        return symbols_affected

    def _is_tracked_file(self, file_path: str) -> bool:
        """Check if a file should be tracked based on extension."""
        # Get file extensions from the codebase
        extensions = self.codebase.ctx.extensions

        # If we can't determine extensions, track common source files
        if not extensions:
            extensions = [".py", ".js", ".ts", ".tsx", ".jsx"]

        return any(file_path.endswith(ext) for ext in extensions)

    def _ensure_history_built(self) -> None:
        """Ensure git history has been built."""
        if not self._history_built:
            self.build_history()

    def map_symbols_to_history(self, force=False) -> None:
        """Map symbols in the codebase to their git history. force ensures a rerun even if data is already found!"""
        self._ensure_history_built()
        if self._symbol_history:
            print("Already built, run with force if you want to rerun anyway!")
            return

        print("Mapping symbols to git history...")
        start_time = time.time()

        print("Stashing any working directory changes...")
        stash_msg = f"Codegen Attribution Stash @ {datetime.now().timestamp()}"
        stash_id = None
        try:
            stash_id = self.repo.stash(self.repo.default_signature, stash_msg, include_untracked=True)
            print("Stashed!")
        except KeyError as e:
            print("Nothing to stash, proceeding.....")
        except Exception as e:
            print("Error encountered attempting to stash the current working state, stopping to preserve work, please manually clean the working directory and try again!")
            raise (e)

        print("Generating initial symbol state...")
        filepaths = [file.filepath for file in self.codebase.files]
        self._process_symbol_location_state(filepaths)

        elapsed = time.time() - start_time
        print(f"Finished initial symbol state generation in {elapsed:.2f} seconds.")
        symbol_tracking_checkpoint = time.time()
        try:
            print("Starting symbol tracking procedure....")
            for commit in self._commits:
                author_name = commit.author.name
                author_email = commit.author.email
                timestamp = commit.author.time
                commit_id = str(commit.id)

                commit_info = {
                    "author": author_name,
                    "email": author_email,
                    "timestamp": timestamp,
                    "commit_id": commit_id,
                    "message": commit.message.strip(),
                }
                commit_previous = commit.parents[0] if commit.parents else None
                if not commit_previous:
                    # If Last commit
                    empty_tree_old = self.repo.TreeBuilder().write()
                    empty_tree = self.repo.get(empty_tree_old)
                    diff = self.repo.diff(empty_tree, commit.tree)
                else:
                    diff = self.repo.diff(commit_previous, commit, context_lines=0)  # We don't need context lines

                if isinstance(diff, Patch):
                    diff = [diff]
                sync_past_filepaths = []  # Files to sync in the past commit
                for patch in diff:
                    filepath = patch.delta.new_file.path
                    if not self._is_tracked_file(filepath):
                        continue  # Ignore files we don't track
                    if not patch.delta.status == DeltaStatus.ADDED:  # Reversed since we're going backwards, if it doesn't exist in the past commits don't sync!
                        sync_past_filepaths.append(filepath)
                    symbols_affected = self._get_symbols_affected_by_patch(patch, filepath)
                    for symbol in symbols_affected:
                        symbol_id = f"{symbol.filepath}:{symbol.name}"  # For future stuff might want to do this more neatly and allow for future dead symbols/renames
                        self._symbol_history[symbol_id].append(commit_info)

                if commit_previous:
                    # If not last commit
                    self.repo.checkout_tree(commit_previous, strategy=CheckoutStrategy.FORCE)
                    self.repo.set_head(commit_previous.id)
                    files = [self.codebase.get_file(fp) for fp in sync_past_filepaths]
                    exclude_state_files = []
                    for file in files:
                        if not isinstance(file, SourceFile):
                            # What kind of pyfiles are not source files? To investigate!
                            exclude_state_files.append(file.filepath)
                            continue
                        file.sync_with_file_content()
                    self._process_symbol_location_state([fp for fp in sync_past_filepaths if fp not in exclude_state_files])

        finally:
            print("Finished, restoring git repo state...")
            self.repo.checkout(self.org_branch_reference, strategy=CheckoutStrategy.FORCE)

            print(f"Restored to latest commit, newest commit id in repo is {self.repo.revparse_single(self.org_branch_reference.name).id}")

            if stash_id:
                # Restoring Working Directory
                print("Restoring working directory changes...")
                found_stash = None
                for idx, stash in enumerate(self.repo.listall_stashes()):
                    if stash_msg in stash.message:
                        found_stash = idx
                        break
                if found_stash == 0:
                    print("Applying stash..")
                    self.repo.stash_apply(0, reinstate_index=True)
                    print("Applied Stash")
                    self.repo.stash_drop(0)
                    print("Stash Removed!")
                else:
                    print("Another stash occured in the meantime,please handle stash resotration manually")
                    print(f"Codebase stash index:{found_stash}")
                    print(f"Codebase stash msg:{stash_msg}")
                    print(f"Codebase stash oid:{stash_id}")

        end_time = time.time()
        elapsed_total = end_time - start_time
        elapsed_symbol_tracking = end_time - symbol_tracking_checkpoint
        print(f"Finished symbol tracking in {elapsed_symbol_tracking:.2f} seconds.")
        print(f"Finished mapping symbols in {elapsed_total:.2f} seconds.")

    def get_symbol_history(self, symbol: Symbol) -> list[dict]:
        """Get the edit history for a symbol.

        Args:
            symbol: The symbol to get history for

        Returns:
            List of commit information dictionaries
        """
        self._ensure_history_built()

        if not hasattr(symbol, "filepath") or not symbol.filepath:
            return []

        symbol_id = f"{symbol.filepath}:{symbol.name}"
        return self._symbol_history.get(symbol_id, [])

    def get_symbol_last_editor(self, symbol: Symbol) -> Optional[str]:
        """Get the last person who edited a symbol.

        Args:
            symbol: The symbol to check

        Returns:
            Author name or None if no history found
        """
        history = self.get_symbol_history(symbol)
        if not history:
            return None

        # Sort by timestamp (newest first) and return the author
        sorted_history = sorted(history, key=lambda x: x["timestamp"], reverse=True)
        return sorted_history[0]["author"]

    def get_ai_contribution_stats(self) -> dict:
        """Get statistics about AI contributions to the codebase.

        Returns:
            Dictionary with AI contribution statistics
        """
        self._ensure_history_built()

        # Count AI commits by file
        ai_file_commits = defaultdict(int)
        total_file_commits = defaultdict(int)

        for file_path, commits in self._file_history.items():
            for commit in commits:
                total_file_commits[file_path] += 1
                if commit["author"] in self.ai_authors or commit["email"] in self.ai_authors:
                    ai_file_commits[file_path] += 1

        # Find files with highest AI contribution percentage
        ai_contribution_percentage = {}
        for file_path, total in total_file_commits.items():
            if total > 0:
                ai_contribution_percentage[file_path] = (ai_file_commits[file_path] / total) * 100

        # Get top files by AI contribution
        top_ai_files = sorted(ai_contribution_percentage.items(), key=lambda x: x[1], reverse=True)[:20]

        # Count total AI commits
        ai_commits = sum(len(commits) for author, commits in self._author_contributions.items() if any(name in author for name in self.ai_authors))

        total_commits = sum(len(commits) for commits in self._author_contributions.values())

        # Calculate AI percentage safely
        if total_commits > 0:
            ai_percentage = (ai_commits / total_commits) * 100
        else:
            ai_percentage = 0.0

        return {
            "total_commits": total_commits,
            "ai_commits": ai_commits,
            "ai_percentage": ai_percentage,
            "top_ai_files": top_ai_files,
            "ai_file_count": len([f for f, p in ai_contribution_percentage.items() if p > 50]),
            "total_file_count": len(total_file_commits),
        }

    def get_ai_touched_symbols(self) -> list[Symbol]:
        """Get all symbols that have been touched by AI authors.

        Returns:
            List of symbols that have been edited by AI authors
        """
        self._ensure_history_built()

        ai_symbols = []

        for symbol in self.codebase.symbols:
            history = self.get_symbol_history(symbol)

            # Check if any commit is from an AI author
            if any(commit["author"] in self.ai_authors or commit["email"] in self.ai_authors for commit in history):
                ai_symbols.append(symbol)

        return ai_symbols

    def get_ai_contribution_timeline(self) -> list[tuple[datetime, int]]:
        """Get a timeline of AI contributions over time.

        Returns:
            List of (datetime, count) tuples showing AI contributions over time
        """
        self._ensure_history_built()

        # Group commits by month
        monthly_counts = defaultdict(int)

        for author, commits in self._author_contributions.items():
            if any(name in author for name in self.ai_authors):
                for commit in commits:
                    # Convert timestamp to year-month
                    dt = datetime.fromtimestamp(commit["timestamp"])
                    month_key = f"{dt.year}-{dt.month:02d}"
                    monthly_counts[month_key] += 1

        # Sort by date
        timeline = sorted(monthly_counts.items())

        # Convert to datetime objects
        return [(datetime.strptime(month, "%Y-%m"), count) for month, count in timeline]
