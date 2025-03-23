"""Utility functions for the integrated CI/CD flow."""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from codegen import Codebase, CodeAgent
from codegen.extensions.clients.linear import LinearClient
from codegen.extensions.tools.github.create_pr import create_pr
from codegen.shared.enums.programming_language import ProgrammingLanguage

from .models import CodeReviewFeedback, DevelopmentPlan, DevelopmentTask, TaskStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_codebase(repo_name: str, language: ProgrammingLanguage) -> Codebase:
    """Create a codebase instance for the given repository.
    
    Args:
        repo_name: The name of the repository (e.g., "owner/repo")
        language: The programming language of the repository
        
    Returns:
        A Codebase instance
    """
    logger.info(f"Creating codebase for {repo_name}")
    return Codebase.from_repo(repo_name, language=language)


def format_linear_message(title: str, description: str) -> str:
    """Format a Linear ticket title and description for the CodeAgent.
    
    Args:
        title: The title of the Linear ticket
        description: The description of the Linear ticket
        
    Returns:
        A formatted message for the CodeAgent
    """
    return f"# {title}\n\n{description}"


def has_codegen_label(data: Dict[str, Any]) -> bool:
    """Check if a Linear issue has the 'Codegen' label.
    
    Args:
        data: The webhook payload from Linear
        
    Returns:
        True if the issue has the 'Codegen' label, False otherwise
    """
    try:
        labels = data.get("data", {}).get("labels", {}).get("nodes", [])
        return any(label.get("name") == "Codegen" for label in labels)
    except (KeyError, AttributeError):
        return False


def process_update_event(data: Dict[str, Any]) -> DevelopmentTask:
    """Process a Linear webhook event and extract issue information.
    
    Args:
        data: The webhook payload from Linear
        
    Returns:
        A DevelopmentTask instance
    """
    issue_data = data.get("data", {})
    issue_id = issue_data.get("id")
    issue_title = issue_data.get("title", "")
    issue_description = issue_data.get("description", "")
    issue_identifier = issue_data.get("identifier", "")
    issue_url = f"https://linear.app/issue/{issue_identifier}"
    
    return DevelopmentTask(
        id=issue_identifier,
        title=issue_title,
        description=issue_description,
        status=TaskStatus.PLANNING,
        linear_id=issue_id,
        linear_url=issue_url,
    )


def analyze_code_complexity(codebase: Codebase, filepath: str) -> int:
    """Analyze the complexity of a file in the codebase.
    
    Args:
        codebase: The codebase instance
        filepath: The path to the file to analyze
        
    Returns:
        A complexity score from 1-10
    """
    # This is a simplified implementation
    # In a real implementation, you would use metrics like cyclomatic complexity
    file = codebase.get_file(filepath)
    if not file:
        return 5  # Default complexity
    
    # Simple heuristic based on file size and number of functions
    lines = file.content.count("\n")
    if lines < 100:
        return 2
    elif lines < 300:
        return 5
    else:
        return 8


def create_development_plan(task: DevelopmentTask, codebase: Codebase) -> DevelopmentPlan:
    """Create a development plan for a task.
    
    Args:
        task: The development task
        codebase: The codebase instance
        
    Returns:
        A development plan
    """
    # In a real implementation, you would use AI to analyze the task and create a plan
    # This is a simplified implementation
    return DevelopmentPlan(
        main_task=task,
        subtasks=[],
        dependencies=[],
        estimated_complexity=5,
        approach="Implement the feature as described in the task",
        risks=["Potential performance impact", "Integration with existing systems"],
    )


def semantic_search(codebase: Codebase, query: str, k: int = 5) -> List[Tuple[str, float]]:
    """Search the codebase using semantic similarity.
    
    Args:
        codebase: The codebase instance
        query: The search query
        k: The number of results to return
        
    Returns:
        A list of (filepath, score) tuples
    """
    from codegen.extensions.tools.semantic_search import semantic_search as search_func
    
    results = search_func(codebase, query, k=k)
    return [(result.filepath, result.score) for result in results.results]


def notify_slack(message: str, channel: str) -> None:
    """Send a notification to Slack.
    
    Args:
        message: The message to send
        channel: The channel to send the message to
    """
    # In a real implementation, you would use the Slack API
    # This is a simplified implementation
    logger.info(f"Slack notification to {channel}: {message}")


def checkout_code_locally(repo_name: str, branch_name: str) -> str:
    """Check out code locally for development.
    
    Args:
        repo_name: The name of the repository (e.g., "owner/repo")
        branch_name: The name of the branch to check out
        
    Returns:
        The path to the checked out code
    """
    # In a real implementation, you would use git to check out the code
    # This is a simplified implementation
    import tempfile
    
    temp_dir = tempfile.mkdtemp()
    logger.info(f"Checked out {repo_name} to {temp_dir}")
    return temp_dir