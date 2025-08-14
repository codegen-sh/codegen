"""Utilities for Claude Code session log management."""

import json
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional


def get_hyphenated_cwd() -> str:
    """Convert current working directory to hyphenated format for Claude log path.
    
    Returns:
        Hyphenated directory name (e.g., "/Users/john/project" -> "users-john-project")
    """
    cwd = os.getcwd()
    # Remove leading slash and replace slashes and spaces with hyphens
    hyphenated = cwd.replace('/', '-').replace(' ', '-')
    # Remove any double hyphens
    hyphenated = re.sub(r'-+', '-', hyphenated)
    return hyphenated


def get_claude_session_log_path(session_id: str) -> Path:
    """Get the path to the Claude session log file.
    
    Args:
        session_id: The Claude session ID
        
    Returns:
        Path to the session log file
    """
    claude_dir = Path.home() / ".claude"
    projects_dir = claude_dir / "projects"
    hyphenated_cwd = get_hyphenated_cwd()
    project_dir = projects_dir / hyphenated_cwd
    
    log_file = project_dir / f"{session_id}.jsonl"
    return log_file


def parse_jsonl_line(line: str) -> Optional[Dict[str, Any]]:
    """Parse a single line from a JSONL file.
    
    Args:
        line: Raw line from JSONL file
        
    Returns:
        Parsed JSON object or None if parsing fails
    """
    line = line.strip()
    if not line:
        return None
        
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


def ensure_log_directory(session_id: str) -> Path:
    """Ensure the log directory exists and return the log file path.
    
    Args:
        session_id: The Claude session ID
        
    Returns:
        Path to the session log file
    """
    log_path = get_claude_session_log_path(session_id)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    return log_path


def read_existing_log_lines(log_path: Path) -> int:
    """Count existing lines in a log file.
    
    Args:
        log_path: Path to the log file
        
    Returns:
        Number of existing lines
    """
    if not log_path.exists():
        return 0
        
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f)
    except (OSError, UnicodeDecodeError):
        return 0


def validate_log_entry(log_entry: Dict[str, Any]) -> bool:
    """Validate a log entry before sending to API.
    
    Args:
        log_entry: The log entry to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(log_entry, dict):
        return False
        
    # Basic validation - ensure it has some content
    if not log_entry:
        return False
        
    # Optionally validate specific fields that Claude Code uses
    # This can be expanded based on actual Claude log format
    return True


def format_log_for_api(log_entry: Dict[str, Any]) -> Dict[str, Any]:
    """Format a log entry for sending to the API.
    
    Args:
        log_entry: Raw log entry from Claude
        
    Returns:
        Formatted log entry ready for API
    """
    # For now, pass through as-is since API expects dict[str, Any]
    # This can be enhanced to transform or filter fields as needed
    return log_entry