"""Shared utilities and configurations for the enhanced CI/CD flow."""

import os
import logging
from typing import Any, Dict, List, Optional

import modal
from codegen.extensions.events.codegen_app import CodegenApp
from codegen.extensions.clients.linear import LinearClient
from codegen.extensions.clients.github import GitHubClient
from codegen import Codebase, CodeAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Create base image with all dependencies
BASE_IMAGE = (
    modal.Image.debian_slim(python_version="3.13")
    .apt_install("git")
    .pip_install(
        "fastapi[standard]",
        "codegen>=0.26.3",
        "slack_sdk",
        "openai>=1.1.0",
        "anthropic>=0.5.0",
    )
)

# Create shared event bus for component communication
class EventBus:
    """Simple event bus for communication between components."""
    
    def __init__(self):
        self.subscribers = {}
        
    def subscribe(self, event_type: str, callback):
        """Subscribe to an event type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        
    def publish(self, event_type: str, data: Any):
        """Publish an event to all subscribers."""
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                callback(data)

# Create shared state management
class SharedState:
    """Shared state management for the CI/CD flow."""
    
    def __init__(self):
        self.state = {}
        
    def set(self, key: str, value: Any):
        """Set a value in the shared state."""
        self.state[key] = value
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the shared state."""
        return self.state.get(key, default)
        
    def delete(self, key: str):
        """Delete a value from the shared state."""
        if key in self.state:
            del self.state[key]

# Helper functions for Linear integration
def has_codegen_label(data: Dict[str, Any]) -> bool:
    """Check if a Linear issue has the 'Codegen' label."""
    if "labels" not in data or not data["labels"]:
        return False
    
    for label in data["labels"]:
        if label["name"].lower() == "codegen":
            return True
    
    return False

def format_linear_message(title: str, description: str) -> str:
    """Format a Linear issue title and description for the CodeAgent."""
    return f"""
# {title}

{description}

Please implement the changes described above.
"""

# Helper functions for GitHub integration
def create_codebase(repo: str, language: str) -> Codebase:
    """Create a codebase from a GitHub repository."""
    return Codebase.from_repo(repo, language=language)

# Helper functions for Slack integration
def send_slack_message(client, channel: str, message: str, thread_ts: Optional[str] = None):
    """Send a message to a Slack channel."""
    client.chat_postMessage(
        channel=channel,
        text=message,
        thread_ts=thread_ts,
    )

# Create shared CodegenApp instance
def create_app(name: str) -> CodegenApp:
    """Create a CodegenApp instance with the shared image."""
    return CodegenApp(name=name)

# Create shared clients
def create_linear_client() -> LinearClient:
    """Create a Linear client with the access token from environment."""
    return LinearClient(access_token=os.environ["LINEAR_ACCESS_TOKEN"])

def create_github_client() -> GitHubClient:
    """Create a GitHub client with the token from environment."""
    return GitHubClient(token=os.environ["GITHUB_TOKEN"])

# Create shared agent
def create_agent(codebase: Codebase) -> CodeAgent:
    """Create a CodeAgent for the given codebase."""
    return CodeAgent(codebase)