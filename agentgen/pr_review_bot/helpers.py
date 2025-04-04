import logging
import os
import re
import traceback
from logging import getLogger
from typing import Dict, List, Any, Tuple, Optional
from github import Github
from github.Repository import Repository
from github.PullRequest import PullRequest
from github.ContentFile import ContentFile
import markdown
from bs4 import BeautifulSoup
from agentgen.agents.chat_agent import ChatAgent
from agentgen.extensions.langchain.tools import (
    GithubViewPRTool,
    GithubCreatePRCommentTool,
    GithubCreatePRReviewCommentTool,
    ViewFileTool,
    ListDirectoryTool,
    RipGrepTool,
    SearchFilesByNameTool,
    ReflectionTool,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = getLogger(__name__)

def get_github_client(token: str) -> Github:
    return Github(token)

def get_repository(github_client: Github, repo_name: str) -> Repository:
    return github_client.get_repo(repo_name)

def get_pull_request(repo: Repository, pr_number: int) -> PullRequest:
    return repo.get_pull(pr_number)

def get_root_markdown_files(repo: Repository) -> List[ContentFile]:
    contents = repo.get_contents("")
    markdown_files = []

    for content in contents:
        if content.type == "file" and content.name.lower().endswith(".md"):
            markdown_files.append(content)

    return markdown_files

def extract_text_from_markdown(markdown_content: str) -> str:
    # Convert markdown to HTML
    html = markdown.markdown(markdown_content)

    # Use BeautifulSoup to extract text from HTML
    soup = BeautifulSoup(html, "html.parser")

    # Get text and normalize whitespace
    text = soup.get_text()
    text = re.sub(r'\s+', ' ', text).strip()

    return text

class Codebase:
    """Simple codebase class for PR review bot."""
    
    def __init__(self, repo_name: str, github_token: str):
        self.repo_name = repo_name
        self.github_token = github_token
        self.g = Github(github_token)
        self.repo = self.g.get_repo(repo_name)
        
    def create_pr_comment(self, pr_number: int, body: str):
        """Create a comment on a PR."""
        pr = self.repo.get_pull(pr_number)
        return pr.create_issue_comment(body)

def analyze_pr_against_docs(pr: PullRequest, markdown_files: List[ContentFile]) -> Dict[str, Any]:
    # Get PR details
    pr_title = pr.title
    pr_body = pr.body or ""
    pr_files = list(pr.get_files())

    # Extract documentation content
    docs_content = ""
    for md_file in markdown_files:
        docs_content += f"\n\n--- {md_file.name} ---\n"
        docs_content += extract_text_from_markdown(md_file.decoded_content.decode("utf-8"))

    # Use Codegen to analyze PR against documentation
    analysis_result = analyze_with_codegen(pr, docs_content)

    return analysis_result

def analyze_with_codegen(pr: PullRequest, docs_content: str) -> Dict[str, Any]:
    # Get repository information
    repo = pr.base.repo
    repo_name = repo.full_name

    try:
        # Initialize Codebase
        logger.info(f"Initializing Codebase for {repo_name}")
        codebase = Codebase(
            repo_name,
            github_token=os.environ["GITHUB_TOKEN"]
        )

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

        # Create agent with tools
        logger.info("Creating ChatAgent with PR review tools")
        agent = ChatAgent(tools=pr_tools)

        # Prepare prompt for analysis
        prompt = f"""
        You are a PR review bot that checks if pull requests comply with project documentation.

        Please analyze this pull request:
        PR #{pr.number}: {pr.title}

        PR Description:
        {pr.body or "No description provided"}

        The PR should comply with the following documentation:
        {docs_content}

        Your task:
        1. Analyze if the PR complies with the documentation requirements
        2. Identify any issues or non-compliance
        3. Provide specific suggestions for improvement if needed
        4. Determine if the PR should be approved or needs changes

        Use the tools available to you to:
        1. View the PR details and changes
        2. Leave comments on specific lines of code if needed
        3. Provide a comprehensive review

        Format your final response as a JSON object with the following structure:
        {{
            "compliant": true/false,
            "issues": ["issue1", "issue2", ...],
            "suggestions": ["suggestion1", "suggestion2", ...],
            "approval_recommendation": "approve" or "request_changes",
            "review_comment": "Your detailed review comment here"
        }}
        """

        # Run the agent and get the response
        logger.info("Running ChatAgent for analysis")
        response = agent.run(prompt)

        # Parse the response to extract the JSON
        try:
            # Find JSON in the response
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON without code blocks
                json_match = re.search(r'({.*})', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    logger.error("Could not extract JSON from Codegen response")
                    return {
                        "compliant": False,
                        "issues": ["Failed to analyze PR properly"],
                        "suggestions": ["Please review manually"],
                        "approval_recommendation": "request_changes",
                        "review_comment": "Failed to analyze PR properly. Please review manually."
                    }

            import json
            result = json.loads(json_str)
            return result
        except Exception as e:
            logger.error(f"Error parsing Codegen response: {e}")
            return {
                "compliant": False,
                "issues": ["Failed to analyze PR properly"],
                "suggestions": ["Please review manually"],
                "approval_recommendation": "request_changes",
                "review_comment": "Failed to analyze PR properly. Please review manually."
            }
    except Exception as e:
        logger.error(f"Error in Codegen analysis: {e}")
        logger.error(traceback.format_exc())
        return {
            "compliant": False,
            "issues": [f"Error during automated review: {str(e)}"],
            "suggestions": ["Please review manually"],
            "approval_recommendation": "request_changes",
            "review_comment": f"An error occurred during the automated review: {str(e)}\n\nPlease review this PR manually."
        }

def post_review_comment(pr: PullRequest, review_result: Dict[str, Any]) -> None:
    """
    Post a review comment on the pull request.

    Args:
        pr: GitHub PullRequest object
        review_result: Analysis results
    """
    # Format the review comment
    comment = f"# PR Review Bot Analysis\n\n"

    if review_result["compliant"]:
        comment += ":white_check_mark: **This PR complies with project documentation requirements.**\n\n"
    else:
        comment += ":x: **This PR does not fully comply with project documentation requirements.**\n\n"

    # Add issues if any
    if review_result["issues"] and len(review_result["issues"]) > 0:
        comment += "## Issues\n\n"
        for issue in review_result["issues"]:
            comment += f"- {issue}\n"
        comment += "\n"

    # Add suggestions if any
    if review_result["suggestions"] and len(review_result["suggestions"]) > 0:
        comment += "## Suggestions\n\n"
        for suggestion in review_result["suggestions"]:
            comment += f"- {suggestion}\n"
        comment += "\n"

    # Add detailed review
    comment += "## Detailed Review\n\n"
    comment += review_result["review_comment"]

    # Post the comment
    try:
        pr.create_issue_comment(comment)
    except Exception as comment_error:
        logger.error(f"Error posting review comment: {comment_error}")
        logger.error(traceback.format_exc())

def submit_review(pr: PullRequest, review_result: Dict[str, Any]) -> None:
    """
    Submit a formal review on the pull request.

    Args:
        pr: GitHub PullRequest object
        review_result: Analysis results
    """
    # Determine review state
    if review_result["approval_recommendation"] == "approve":
        review_state = "APPROVE"
    else:
        review_state = "REQUEST_CHANGES"

    # Submit the review
    try:
        pr.create_review(
            body=review_result["review_comment"],
            event=review_state
        )
    except Exception as review_error:
        logger.error(f"Error submitting formal review: {review_error}")
        logger.error(traceback.format_exc())

def review_pr(github_client: Github, repo_name: str, pr_number: int) -> Dict[str, Any]:
    logger.info(f"Reviewing PR #{pr_number} in {repo_name}")

    try:
        # Get repository and PR
        repo = get_repository(github_client, repo_name)
        pr = get_pull_request(repo, pr_number)

        # Get markdown files from root directory
        markdown_files = get_root_markdown_files(repo)

        if not markdown_files:
            logger.warning(f"No markdown files found in the root directory of {repo_name}")
            review_result = {
                "compliant": False,
                "issues": ["No documentation files found in repository root"],
                "suggestions": ["Add documentation in markdown format to the repository root"],
                "approval_recommendation": "request_changes",
                "review_comment": "Could not review PR as no documentation files were found in the repository root."
            }
        else:
            # Analyze PR against documentation
            review_result = analyze_pr_against_docs(pr, markdown_files)

        # Post review comment
        try:
            post_review_comment(pr, review_result)
        except Exception as comment_error:
            logger.error(f"Error posting review comment: {comment_error}")
            logger.error(traceback.format_exc())

        # Submit formal review
        try:
            submit_review(pr, review_result)
        except Exception as review_error:
            logger.error(f"Error submitting formal review: {review_error}")
            logger.error(traceback.format_exc())

        return {
            "pr_number": pr_number,
            "repo_name": repo_name,
            "compliant": review_result["compliant"],
            "approval_recommendation": review_result["approval_recommendation"]
        }

    except Exception as e:
        logger.error(f"Error reviewing PR: {e}")
        logger.error(traceback.format_exc())
        raise

def remove_bot_comments(event) -> Dict[str, Any]:
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
        logger.error(f"Error removing bot comments: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

def pr_review_agent(event) -> Dict[str, Any]:
    """Review a pull request and provide feedback.
    
    Args:
        event: The PR labeled event
        
    Returns:
        A dictionary with review results
    """
    try:
        # Get repository information
        repo_name = f"{event.organization.login}/{event.repository.name}"
        pr_number = event.number
        pr_title = event.pull_request.title
        pr_url = event.pull_request.url
        
        logger.info(f"Reviewing PR #{pr_number} in {repo_name}: {pr_title}")
        
        # Initialize GitHub client
        github_client = get_github_client(os.environ["GITHUB_TOKEN"])
        
        # Review the PR
        result = review_pr(github_client, repo_name, pr_number)
        
        return {
            "status": "success",
            "message": f"Successfully reviewed PR #{pr_number}",
            "result": result
        }
    except Exception as e:
        logger.error(f"Error reviewing PR: {e}")
        logger.error(traceback.format_exc())
        return {
            "status": "error",
            "error": str(e)
        }
