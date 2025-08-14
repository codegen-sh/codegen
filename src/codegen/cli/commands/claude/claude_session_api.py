"""API client for Claude Code session management."""

import json
import uuid
from typing import Optional

import requests
from .quiet_console import console

from codegen.cli.api.endpoints import API_ENDPOINT
from codegen.cli.auth.token_manager import get_current_token
from codegen.cli.utils.org import resolve_org_id



class ClaudeSessionAPIError(Exception):
    """Exception raised for Claude session API errors."""
    pass


def generate_session_id() -> str:
    """Generate a unique session ID for Claude Code session tracking."""
    return str(uuid.uuid4())


def create_claude_session(session_id: str, org_id: Optional[int] = None) -> Optional[str]:
    """Create a new Claude Code session in the backend.
    
    Args:
        session_id: The session ID to register
        org_id: Organization ID (will be resolved if None)
        
    Returns:
        Agent run ID if successful, None if failed
        
    Raises:
        ClaudeSessionAPIError: If the API call fails
    """
    try:
        # Resolve org_id
        resolved_org_id = resolve_org_id(org_id)
        if resolved_org_id is None:
            console.print("⚠️  Could not resolve organization ID for session creation", style="yellow")
            return None
            
        # Get authentication token
        token = get_current_token()
        if not token:
            console.print("⚠️  No authentication token found for session creation", style="yellow")
            return None
            
        # Prepare API request
        url = f"{API_ENDPOINT.rstrip('/')}/v1/organizations/{resolved_org_id}/claude_code/session"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {"session_id": session_id}
        
        # Make API request
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            try:
                result = response.json()
                agent_run_id = result.get("agent_run_id")
                return agent_run_id
            except (json.JSONDecodeError, KeyError) as e:
                console.print(f"⚠️  Invalid response format from session creation: {e}", style="yellow")
                return None
        else:
            error_msg = f"HTTP {response.status_code}"
            try:
                error_detail = response.json().get("detail", response.text)
                error_msg = f"{error_msg}: {error_detail}"
            except Exception:
                error_msg = f"{error_msg}: {response.text}"
            
            console.print(f"⚠️  Failed to create Claude session: {error_msg}", style="yellow")
            return None
            
    except requests.RequestException as e:
        console.print(f"⚠️  Network error creating Claude session: {e}", style="yellow")
        return None
    except Exception as e:
        console.print(f"⚠️  Unexpected error creating Claude session: {e}", style="yellow")
        return None


def end_claude_session(session_id: str, status: str, org_id: Optional[int] = None) -> bool:
    """End a Claude Code session in the backend.
    
    Args:
        session_id: The session ID to end
        status: Completion status ("COMPLETE" or "ERROR") 
        org_id: Organization ID (will be resolved if None)
        
    Returns:
        True if successful, False if failed
    """
    try:
        # Resolve org_id
        resolved_org_id = resolve_org_id(org_id)
        if resolved_org_id is None:
            console.print("⚠️  Could not resolve organization ID for session completion", style="yellow")
            return False
            
        # Get authentication token
        token = get_current_token()
        if not token:
            console.print("⚠️  No authentication token found for session completion", style="yellow")
            return False
            
        # Prepare API request
        url = f"{API_ENDPOINT.rstrip('/')}/v1/organizations/{resolved_org_id}/claude_code/session/{session_id}/status"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {"status": status}
        
        # Make API request
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            status_emoji = "✅" if status == "COMPLETE" else "❌"
            console.print(f"{status_emoji} Ended Claude session {session_id[:8]}... with status {status}", style="green")
            return True
        else:
            error_msg = f"HTTP {response.status_code}"
            try:
                error_detail = response.json().get("detail", response.text)
                error_msg = f"{error_msg}: {error_detail}"
            except Exception:
                error_msg = f"{error_msg}: {response.text}"
            
            console.print(f"⚠️  Failed to end Claude session: {error_msg}", style="yellow")
            return False
            
    except requests.RequestException as e:
        console.print(f"⚠️  Network error ending Claude session: {e}", style="yellow")
        return False
    except Exception as e:
        console.print(f"⚠️  Unexpected error ending Claude session: {e}", style="yellow")
        return False


def send_claude_session_log(session_id: str, log_entry: dict, org_id: Optional[int] = None) -> bool:
    """Send a log entry to the Claude Code session log endpoint.
    
    Args:
        session_id: The session ID
        log_entry: The log entry to send (dict)
        org_id: Organization ID (will be resolved if None)
        
    Returns:
        True if successful, False if failed
    """
    try:
        # Resolve org_id
        resolved_org_id = resolve_org_id(org_id)
        if resolved_org_id is None:
            console.print("⚠️  Could not resolve organization ID for log sending", style="yellow")
            return False
            
        # Get authentication token
        token = get_current_token()
        if not token:
            console.print("⚠️  No authentication token found for log sending", style="yellow")
            return False
            
        # Prepare API request
        url = f"{API_ENDPOINT.rstrip('/')}/v1/organizations/{resolved_org_id}/claude_code/session/{session_id}/log"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {"log": log_entry}
        
        # Make API request
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return True
        else:
            error_msg = f"HTTP {response.status_code}"
            try:
                error_detail = response.json().get("detail", response.text)
                error_msg = f"{error_msg}: {error_detail}"
            except Exception:
                error_msg = f"{error_msg}: {response.text}"
            
            console.print(f"⚠️  Failed to send log entry: {error_msg}", style="yellow")
            return False
            
    except requests.RequestException as e:
        console.print(f"⚠️  Network error sending log entry: {e}", style="yellow")
        return False
    except Exception as e:
        console.print(f"⚠️  Unexpected error sending log entry: {e}", style="yellow")
        return False


def write_session_hook_data(session_id: str, org_id: Optional[int] = None) -> str:
    """Write session data for Claude hook and create session via API.
    
    This function is called by the Claude hook to both write session data locally
    and create the session in the backend API.
    
    Args:
        session_id: The session ID
        org_id: Organization ID
        
    Returns:
        JSON string to write to the session file
    """
    # Create session in backend API
    agent_run_id = create_claude_session(session_id, org_id)
    
    # Prepare session data
    session_data = {
        "session_id": session_id,
        "agent_run_id": agent_run_id,
        "org_id": resolve_org_id(org_id)
    }
    
    return json.dumps(session_data, indent=2)