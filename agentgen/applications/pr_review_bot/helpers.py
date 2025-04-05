"""
Helper functions for the PR Review Bot.
"""

import os
import sys
import logging
import traceback
from logging import getLogger
from typing import Dict, List, Any, Optional
from github import Github
from github.Repository import Repository
from github.PullRequest import PullRequest
from github.ContentFile import ContentFile
from agentgen import Codebase
from agentgen.configs.models.secrets import SecretsConfig

# Add the agentgen directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
agentgen_dir = os.path.abspath(os.path.join(current_dir, "../.."))
sys.path.insert(0, agentgen_dir)

from agentgen.agents.code_agent import CodeAgent
from agentgen.extensions.langchain.tools import (
    # Github
    GithubViewPRTool,
    GithubCreatePRCommentTool,
    GithubCreatePRReviewCommentTool,
)
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("pr_review_bot.log"),
        logging.StreamHandler()
    ]
)
logger = getLogger("pr_review_bot")

# Load environment variables
load_dotenv()

def get_github_client(token: str) -> Github:
    """Get a GitHub client instance."""
    return Github(token)

def get_repository(github_client: Github, repo_name: str) -> Repository:
    """Get a GitHub repository instance."""
    return github_client.get_repo(repo_name)

def get_pull_request(repo: Repository, pr_number: int) -> PullRequest:
    """Get a GitHub pull request instance."""
    return repo.get_pull(pr_number)

def remove_bot_comments(event) -> Dict[str, Any]:
    """
    Remove bot comments from a pull request.
    
    Args:
        event: GitHub webhook event
        
    Returns:
        Result of the operation
    """
    try:
        # Get repository and PR information
        repo_name = event["repository"]["full_name"]
        pr_number = event["pull_request"]["number"]
        
        # Get GitHub client
        g = Github(os.environ.get("GITHUB_TOKEN", ""))
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        
        # Remove PR comments
        comments = pr.get_comments()
        removed_count = 0
        
        if comments:
            for comment in comments:
                if comment.user.login == "github-actions[bot]" or comment.user.login == "codegen-team":
                    comment.delete()
                    removed_count += 1
        
        # Remove PR reviews
        reviews = pr.get_reviews()
        if reviews:
            for review in reviews:
                if review.user.login == "github-actions[bot]" or review.user.login == "codegen-team":
                    review.delete()
                    removed_count += 1
        
        # Remove issue comments
        issue_comments = pr.get_issue_comments()
        if issue_comments:
            for comment in issue_comments:
                if comment.user.login == "github-actions[bot]" or comment.user.login == "codegen-team":
                    comment.delete()
                    removed_count += 1
        
        logger.info(f"Removed {removed_count} bot comments from PR #{pr_number} in {repo_name}")
        
        return {
            "pr_number": pr_number,
            "repo_name": repo_name,
            "removed_comments": removed_count
        }
    except Exception as e:
        logger.error(f"Error removing bot comments: {e}")
        logger.error(traceback.format_exc())
        raise

def review_pr(github_client: Github, repo_name: str, pr_number: int) -> Dict[str, Any]:
    """
    Review a pull request using the standard approach.
    
    Args:
        github_client: GitHub client
        repo_name: Repository name
        pr_number: Pull request number
        
    Returns:
        Result of the review
    """
    logger.info(f"Reviewing PR #{pr_number} in {repo_name}")
    
    try:
        # Get repository and PR
        repo = get_repository(github_client, repo_name)
        pr = get_pull_request(repo, pr_number)
        
        # Create a simple review comment
        comment_body = f"PR #{pr_number} has been reviewed by the PR Review Bot."
        pr.create_issue_comment(comment_body)
        
        # Check if PR can be merged
        if pr.mergeable:
            # Try to merge the PR
            try:
                merge_result = pr.merge(
                    commit_title=f"Merge PR #{pr_number}: {pr.title}",
                    commit_message=f"Automatically merged PR #{pr_number}.",
                    merge_method="merge"
                )
                logger.info(f"PR #{pr_number} automatically merged")
                return {
                    "pr_number": pr_number,
                    "repo_name": repo_name,
                    "merged": True,
                    "message": "PR automatically merged."
                }
            except Exception as merge_error:
                logger.error(f"Error merging PR: {merge_error}")
                logger.error(traceback.format_exc())
                return {
                    "pr_number": pr_number,
                    "repo_name": repo_name,
                    "merged": False,
                    "message": f"Error merging PR: {str(merge_error)}"
                }
        else:
            logger.info(f"PR #{pr_number} is not mergeable")
            return {
                "pr_number": pr_number,
                "repo_name": repo_name,
                "merged": False,
                "message": "PR is not mergeable."
            }
    except Exception as e:
        logger.error(f"Error reviewing PR: {e}")
        logger.error(traceback.format_exc())
        raise

def pr_review_agent(event) -> Dict[str, Any]:
    """
    Run the PR review agent using Codegen's AI capabilities.
    
    Args:
        event: GitHub webhook event
        
    Returns:
        Result of the review
    """
    try:
        # Get repository and PR information
        repo_name = event["repository"]["full_name"]
        pr_number = event["pull_request"]["number"]
        pr_url = event["pull_request"]["html_url"]
        
        logger.info(f"Running PR review agent for PR #{pr_number} in {repo_name}")
        
        # Initialize Codebase
        codebase = Codebase.from_repo(
            repo_name, 
            language="python", 
            secrets=SecretsConfig(github_token=os.environ["GITHUB_TOKEN"])
        )
        
        # Create a temporary comment to indicate the review is in progress
        review_attention_message = "CodegenBot is starting to review the PR, please wait..."
        comment = codebase._op.create_pr_comment(pr_number, review_attention_message)
        
        # Define tools for the agent
        pr_tools = [
            GithubViewPRTool(codebase),
            GithubCreatePRCommentTool(codebase),
            GithubCreatePRReviewCommentTool(codebase),
        ]
        
        # Create agent with the defined tools
        agent = CodeAgent(codebase=codebase, tools=pr_tools)
        
        # Create the prompt for the agent
        prompt = f"""
        Hey CodegenBot!

        Here's a task for you. Please review this pull request!
        {pr_url}
        
        Do not terminate until you have reviewed the pull request and are satisfied with your review.

        Review this Pull request thoroughly:
        1. Be explicit about the changes
        2. Produce a short summary
        3. Point out possible improvements where present
        4. Don't be self-congratulatory, stick to the facts
        5. Use the tools at your disposal to create proper PR reviews
        6. Include code snippets if needed
        7. Suggest improvements if necessary
        8. Check if the PR is valid and can be merged to the main branch
        """
        
        # Run the agent
        agent.run(prompt)
        
        # Delete the temporary comment
        if comment:
            comment.delete()
        
        # Check if PR can be merged
        g = Github(os.environ.get("GITHUB_TOKEN", ""))
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        
        if pr.mergeable:
            # Try to merge the PR
            try:
                merge_result = pr.merge(
                    commit_title=f"Merge PR #{pr_number}: {pr.title}",
                    commit_message=f"Automatically merged PR #{pr_number} after review.",
                    merge_method="merge"
                )
                logger.info(f"PR #{pr_number} automatically merged after review")
                return {
                    "pr_number": pr_number,
                    "repo_name": repo_name,
                    "merged": True,
                    "message": "PR automatically merged after review."
                }
            except Exception as merge_error:
                logger.error(f"Error merging PR: {merge_error}")
                logger.error(traceback.format_exc())
                return {
                    "pr_number": pr_number,
                    "repo_name": repo_name,
                    "merged": False,
                    "message": f"Error merging PR: {str(merge_error)}"
                }
        else:
            logger.info(f"PR #{pr_number} is not mergeable after review")
            return {
                "pr_number": pr_number,
                "repo_name": repo_name,
                "merged": False,
                "message": "PR is not mergeable after review."
            }
    except Exception as e:
        logger.error(f"Error in PR review agent: {e}")
        logger.error(traceback.format_exc())
        raise
