"""Claude Code session log watcher implementation."""

import time
import threading
from pathlib import Path
from typing import Optional, Callable, Dict, Any

from .quiet_console import console

from .claude_log_utils import (
    get_claude_session_log_path, 
    parse_jsonl_line, 
    read_existing_log_lines,
    validate_log_entry,
    format_log_for_api
)
from .claude_session_api import send_claude_session_log


class ClaudeLogWatcher:
    """Watches Claude Code session log files for new entries and sends them to the API."""
    
    def __init__(
        self, 
        session_id: str, 
        org_id: Optional[int] = None,
        poll_interval: float = 1.0,
        on_log_entry: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        """Initialize the log watcher.
        
        Args:
            session_id: The Claude session ID to watch
            org_id: Organization ID for API calls
            poll_interval: How often to check for new entries (seconds)
            on_log_entry: Optional callback for each new log entry
        """
        self.session_id = session_id
        self.org_id = org_id
        self.poll_interval = poll_interval
        self.on_log_entry = on_log_entry
        
        self.log_path = get_claude_session_log_path(session_id)
        self.last_line_count = 0
        self.is_running = False
        self.watcher_thread: Optional[threading.Thread] = None
        
        # Stats
        self.total_entries_processed = 0
        self.total_entries_sent = 0
        self.total_send_failures = 0
        
    def start(self) -> bool:
        """Start the log watcher in a background thread.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.is_running:
            console.print(f"⚠️  Log watcher for session {self.session_id[:8]}... is already running", style="yellow")
            return False
            
        # Initialize line count
        self.last_line_count = read_existing_log_lines(self.log_path)
        
        self.is_running = True
        self.watcher_thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.watcher_thread.start()
        
        console.print(f"📋 Started log watcher for session {self.session_id[:8]}...", style="green")
        console.print(f"   Log file: {self.log_path}", style="dim")
        console.print(f"   Starting from line: {self.last_line_count + 1}", style="dim")
        
        return True
        
    def stop(self) -> None:
        """Stop the log watcher."""
        if not self.is_running:
            return
            
        self.is_running = False
        
        if self.watcher_thread and self.watcher_thread.is_alive():
            self.watcher_thread.join(timeout=2.0)
            
        console.print(f"📋 Stopped log watcher for session {self.session_id[:8]}...", style="dim")
        console.print(f"   Processed: {self.total_entries_processed} entries", style="dim")
        console.print(f"   Sent: {self.total_entries_sent} entries", style="dim")
        if self.total_send_failures > 0:
            console.print(f"   Failures: {self.total_send_failures} entries", style="yellow")
            
    def _watch_loop(self) -> None:
        """Main watching loop that runs in a background thread."""
        while self.is_running:
            try:
                self._check_for_new_entries()
                time.sleep(self.poll_interval)
            except Exception as e:
                console.print(f"⚠️  Error in log watcher: {e}", style="yellow")
                time.sleep(self.poll_interval * 2)  # Back off on errors
                
    def _check_for_new_entries(self) -> None:
        """Check for new log entries and process them."""
        if not self.log_path.exists():
            return
            
        try:
            current_line_count = read_existing_log_lines(self.log_path)
            
            if current_line_count > self.last_line_count:
                new_entries = self._read_new_lines(self.last_line_count, current_line_count)
                
                for entry in new_entries:
                    self._process_log_entry(entry)
                    
                self.last_line_count = current_line_count
                
        except Exception as e:
            console.print(f"⚠️  Error reading log file: {e}", style="yellow")
            
    def _read_new_lines(self, start_line: int, end_line: int) -> list[Dict[str, Any]]:
        """Read new lines from the log file.
        
        Args:
            start_line: Line number to start from (0-indexed)
            end_line: Line number to end at (0-indexed, exclusive)
            
        Returns:
            List of parsed log entries
        """
        entries = []
        
        try:
            with open(self.log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
                # Read only the new lines
                for i in range(start_line, min(end_line, len(lines))):
                    line = lines[i]
                    entry = parse_jsonl_line(line)
                    
                    if entry is not None:
                        entries.append(entry)
                        
        except (OSError, UnicodeDecodeError) as e:
            console.print(f"⚠️  Error reading log file: {e}", style="yellow")
            
        return entries
        
    def _process_log_entry(self, log_entry: Dict[str, Any]) -> None:
        """Process a single log entry.
        
        Args:
            log_entry: The parsed log entry
        """
        self.total_entries_processed += 1
        
        # Validate the entry
        if not validate_log_entry(log_entry):
            console.print(f"⚠️  Invalid log entry skipped: {log_entry}", style="yellow")
            return
            
        # Format for API
        formatted_entry = format_log_for_api(log_entry)
        
        # Call optional callback
        if self.on_log_entry:
            try:
                self.on_log_entry(formatted_entry)
            except Exception as e:
                console.print(f"⚠️  Error in log entry callback: {e}", style="yellow")
                
        # Send to API
        self._send_log_entry(formatted_entry)
        
    def _send_log_entry(self, log_entry: Dict[str, Any]) -> None:
        """Send a log entry to the API.
        
        Args:
            log_entry: The formatted log entry
        """
        try:
            success = send_claude_session_log(self.session_id, log_entry, self.org_id)
            
            if success:
                self.total_entries_sent += 1
                # Only show verbose output in debug mode
                console.print(f"📤 Sent log entry: {log_entry.get('type', 'unknown')}", style="dim")
            else:
                self.total_send_failures += 1
                
        except Exception as e:
            self.total_send_failures += 1
            console.print(f"⚠️  Failed to send log entry: {e}", style="yellow")
            
    def get_stats(self) -> Dict[str, Any]:
        """Get watcher statistics.
        
        Returns:
            Dictionary with watcher stats
        """
        return {
            "session_id": self.session_id,
            "is_running": self.is_running,
            "log_path": str(self.log_path),
            "log_file_exists": self.log_path.exists(),
            "last_line_count": self.last_line_count,
            "total_entries_processed": self.total_entries_processed,
            "total_entries_sent": self.total_entries_sent,
            "total_send_failures": self.total_send_failures,
            "success_rate": (
                self.total_entries_sent / max(1, self.total_entries_processed) * 100
                if self.total_entries_processed > 0 else 0
            )
        }


class ClaudeLogWatcherManager:
    """Manages multiple log watchers for different sessions."""
    
    def __init__(self):
        self.watchers: Dict[str, ClaudeLogWatcher] = {}
        
    def start_watcher(
        self, 
        session_id: str, 
        org_id: Optional[int] = None,
        poll_interval: float = 1.0,
        on_log_entry: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> bool:
        """Start a log watcher for a session.
        
        Args:
            session_id: The Claude session ID
            org_id: Organization ID for API calls
            poll_interval: How often to check for new entries (seconds)
            on_log_entry: Optional callback for each new log entry
            
        Returns:
            True if started successfully, False otherwise
        """
        if session_id in self.watchers:
            console.print(f"⚠️  Watcher for session {session_id[:8]}... already exists", style="yellow")
            return False
            
        watcher = ClaudeLogWatcher(
            session_id=session_id,
            org_id=org_id,
            poll_interval=poll_interval,
            on_log_entry=on_log_entry
        )
        
        if watcher.start():
            self.watchers[session_id] = watcher
            return True
        return False
        
    def stop_watcher(self, session_id: str) -> None:
        """Stop a log watcher for a session.
        
        Args:
            session_id: The Claude session ID
        """
        if session_id in self.watchers:
            self.watchers[session_id].stop()
            del self.watchers[session_id]
            
    def stop_all_watchers(self) -> None:
        """Stop all active watchers."""
        for session_id in list(self.watchers.keys()):
            self.stop_watcher(session_id)
            
    def get_active_sessions(self) -> list[str]:
        """Get list of active session IDs being watched.
        
        Returns:
            List of session IDs
        """
        return list(self.watchers.keys())
        
    def get_watcher_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get stats for a specific watcher.
        
        Args:
            session_id: The Claude session ID
            
        Returns:
            Watcher stats or None if not found
        """
        if session_id in self.watchers:
            return self.watchers[session_id].get_stats()
        return None
        
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get stats for all active watchers.
        
        Returns:
            Dictionary mapping session IDs to their stats
        """
        return {
            session_id: watcher.get_stats()
            for session_id, watcher in self.watchers.items()
        }