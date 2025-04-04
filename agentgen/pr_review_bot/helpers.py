import os
import logging
from logging import getLogger
from typing import Dict, Any, List

from github import Github
from dotenv import load_dotenv

from agentgen.extensions.github.types.events.pull_request import PullRequestLabeledEvent, PullRequestUnlabeledEvent
from agentgen import CodeAgent
from agentgen.extensions.langchain.tools import (
    # GitHub tools
    GithubViewPRTool,
    GithubCreatePRCommentTool,
    GithubCreatePRReviewCommentTool,
    # Basic tools
    ViewFileTool,
    ListDirectoryTool,
    RipGrepTool,
    SearchFilesByNameTool,
    ReflectionTool,
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = getLogger(__name__)

def remove_bot_comments(event: PullRequestUnlabeledEvent) -> Dict[str, Any]:
    """Remove all bot comments from a PR.
    
    Args:
        event: The PR unlabeled event
        
    Returns:
        A dictionary with status and message
    """
    try:
        # Initialize GitHub client
        g = Github(os.getenv("GITHUB_TOKEN"))
        repo_name = f"{event.organization.login}/{event.repository.name}"
        logger.info(f"Removing bot comments from {repo_name} PR #{event.number}")
        
        # Get repository and PR
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(int(event.number))
        
        # Remove PR comments
        comments = pr.get_comments()
        if comments:
            for comment in comments:
                logger.info(f"Checking comment by {comment.user.login}")
                if comment.user.login == "codegen-team":
                    logger.info("Removing PR comment")
                    comment.delete()
        
        # Remove PR review comments
        reviews = pr.get_reviews()
        if reviews:
            for review in reviews:
                logger.info(f"Checking review by {review.user.login}")
                if review.user.login == "codegen-team":
                    logger.info("Removing PR review")
                    review.delete()
        
        # Remove issue comments
        issue_comments = pr.get_issue_comments()
        if issue_comments:
            for comment in issue_comments:
                logger.info(f"Checking issue comment by {comment.user.login}")
                if comment.user.login == "codegen-team":
                    logger.info("Removing issue comment")
                    comment.delete()
        
        return {
            "status": "success",
            "message": f"Successfully removed bot comments from PR #{event.number}"
        }
    except Exception as e:
        logger.exception(f"Error removing bot comments: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

def analyze_codebase(repo_name: str) -> Dict[str, Any]:
    """Analyze the codebase to understand its structure and requirements.
    
    Args:
        repo_name: The repository name in format "owner/repo"
        
    Returns:
        A dictionary with analysis results
    """
    try:
        from codegen import Codebase
        from codegen.configs.models.secrets import SecretsConfig
        
        # Initialize codebase
        codebase = Codebase.from_repo(
            repo_name, 
            language="python", 
            secrets=SecretsConfig(github_token=os.environ["GITHUB_TOKEN"])
        )
        
        # Create tools for analysis
        tools = [
            ViewFileTool(codebase),
            ListDirectoryTool(codebase),
            RipGrepTool(codebase),
            SearchFilesByNameTool(codebase),
            ReflectionTool(codebase),
        ]
        
        # Create agent for analysis
        agent = CodeAgent(codebase=codebase, tools=tools)
        
        # Analyze the codebase
        prompt = f"""
        Analyze the codebase of {repo_name} to understand:
        1. The project's structure and main components
        2. Key dependencies and requirements
        3. Coding standards and patterns used
        
        Provide a concise summary of your findings.
        """
        
        analysis_result = agent.run(prompt)
        
        return {
            "status": "success",
            "analysis": analysis_result
        }
    except Exception as e:
        logger.exception(f"Error analyzing codebase: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

def pr_review_agent(event: PullRequestLabeledEvent) -> Dict[str, Any]:
    """Review a pull request and provide feedback.
    
    Args:
        event: The PR labeled event
        
    Returns:
        A dictionary with review results
    """
    try:
        from codegen import Codebase
        from codegen.configs.models.secrets import SecretsConfig
        
        # Get repository information
        repo_name = f"{event.organization.login}/{event.repository.name}"
        pr_number = event.number
        pr_title = event.pull_request.title
        pr_url = event.pull_request.url
        
        logger.info(f"Reviewing PR #{pr_number} in {repo_name}: {pr_title}")
        
        # Initialize codebase
        codebase = Codebase.from_repo(
            repo_name, 
            language="python", 
            secrets=SecretsConfig(github_token=os.environ["GITHUB_TOKEN"])
        )
        
        # Post initial comment to indicate review is starting
        review_start_message = "🔍 **CodegenBot is reviewing this PR...**\n\nPlease wait while I analyze the changes."
        initial_comment = codebase._op.create_pr_comment(pr_number, review_start_message)
        
        # Define PR review tools
        pr_tools = [
            GithubViewPRTool(codebase),
            GithubCreatePRCommentTool(codebase),
            GithubCreatePRReviewCommentTool(codebase),
            ViewFileTool(codebase),
            ListDirectoryTool(codebase),
            RipGrepTool(codebase),
            SearchFilesByNameTool(codebase),
            ReflectionTool(codebase),
        ]
        
        # Create agent with the defined tools
        agent = CodeAgent(codebase=codebase, tools=pr_tools)
        
        # First, analyze the codebase
        codebase_analysis = analyze_codebase(repo_name)
        
        # Create the review prompt
        prompt = f"""
        You are a senior software engineer reviewing PR #{pr_number}: "{pr_title}" at {pr_url}
        
        First, examine the PR changes using the view_pr tool to understand what has been modified.
        
        Then, analyze the changes to determine:
        1. Do the changes align with the project's requirements and coding standards?
        2. Are there any bugs, edge cases, or potential issues?
        3. Could any parts be implemented more efficiently or clearly?
        4. Are there any security concerns?
        
        For any issues found, add specific inline comments using create_pr_review_comment.
        
        After reviewing all changes, provide a summary comment using create_pr_comment with:
        - A brief overview of what the PR does
        - Key strengths of the implementation
        - Any concerns or suggestions for improvement
        - Whether the PR should be approved or needs changes
        
        Be constructive, specific, and actionable in your feedback.
        """
        
        # Run the agent to review the PR
        agent.run(prompt)
        
        # Delete the initial "reviewing" comment
        initial_comment.delete()
        
        return {
            "status": "success",
            "message": f"Successfully reviewed PR #{pr_number}"
        }
    except Exception as e:
        logger.exception(f"Error reviewing PR: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
