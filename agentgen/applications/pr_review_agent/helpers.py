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

# Import langchain components
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

# Import local modules
from codebase import Codebase

def get_github_client(token: str) -> Github:
    """Get a GitHub client instance."""
    return Github(token)

def get_repository(github_client: Github, repo_name: str) -> Repository:
    """Get a GitHub repository instance."""
    return github_client.get_repo(repo_name)

def get_pull_request(repo: Repository, pr_number: int) -> PullRequest:
    """Get a GitHub pull request instance."""
    return repo.get_pull(pr_number)

def get_root_markdown_files(repo: Repository) -> List[ContentFile]:
    """Get all markdown files in the root directory of the repository."""
    contents = repo.get_contents("")
    markdown_files = []

    for content in contents:
        if content.type == "file" and content.name.lower().endswith(".md"):
            markdown_files.append(content)

    return markdown_files

def extract_text_from_markdown(markdown_content: str) -> str:
    """Extract text from markdown content."""
    # Convert markdown to HTML
    html = markdown.markdown(markdown_content)

    # Use BeautifulSoup to extract text from HTML
    soup = BeautifulSoup(html, "html.parser")

    # Get text and normalize whitespace
    text = soup.get_text()
    text = re.sub(r'\s+', ' ', text).strip()

    return text

def analyze_pr_against_docs(pr: PullRequest, markdown_files: List[ContentFile]) -> Dict[str, Any]:
    """Analyze a pull request against documentation."""
    # Get PR details
    pr_title = pr.title
    pr_body = pr.body or ""
    pr_files = list(pr.get_files())

    # Extract documentation content
    docs_content = ""
    for md_file in markdown_files:
        docs_content += f"\n\n--- {md_file.name} ---\n"
        docs_content += extract_text_from_markdown(md_file.decoded_content.decode("utf-8"))

    # Use LLM to analyze PR against documentation
    analysis_result = analyze_with_llm(pr, docs_content)

    return analysis_result

def analyze_with_llm(pr: PullRequest, docs_content: str) -> Dict[str, Any]:
    """Analyze a pull request using a language model."""
    # Get repository information
    repo = pr.base.repo
    repo_name = repo.full_name

    try:
        # Initialize Codebase
        logger.info(f"Initializing Codebase for {repo_name}")
        codebase = Codebase(repo_name, github_token=os.environ["GITHUB_TOKEN"])

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

        Format your final response as a JSON object with the following structure:
        {{
            "compliant": true/false,
            "issues": ["issue1", "issue2", ...],
            "suggestions": ["suggestion1", "suggestion2", ...],
            "approval_recommendation": "approve" or "request_changes",
            "review_comment": "Your detailed review comment here"
        }}
        """

        # Run the LLM and get the response
        logger.info("Running LLM for analysis")
        
        # Try to use Anthropic if available, otherwise use OpenAI
        try:
            if os.environ.get("ANTHROPIC_API_KEY"):
                llm = ChatAnthropic(model="claude-3-opus-20240229", temperature=0)
            elif os.environ.get("OPENAI_API_KEY"):
                llm = ChatOpenAI(model="gpt-4-turbo", temperature=0)
            else:
                raise ValueError("No API key found for Anthropic or OpenAI")
                
            # Create a simple chain
            chain = ChatPromptTemplate.from_template(prompt) | llm | StrOutputParser()
            response = chain.invoke({})
            
        except Exception as llm_error:
            logger.error(f"Error using LLM: {llm_error}")
            return {
                "compliant": False,
                "issues": [f"Error during automated review: {str(llm_error)}"],
                "suggestions": ["Please review manually"],
                "approval_recommendation": "request_changes",
                "review_comment": f"An error occurred during the automated review: {str(llm_error)}\n\nPlease review this PR manually."
            }

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
                    logger.error("Could not extract JSON from LLM response")
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
            logger.error(f"Error parsing LLM response: {e}")
            return {
                "compliant": False,
                "issues": ["Failed to analyze PR properly"],
                "suggestions": ["Please review manually"],
                "approval_recommendation": "request_changes",
                "review_comment": "Failed to analyze PR properly. Please review manually."
            }
    except Exception as e:
        logger.error(f"Error in LLM analysis: {e}")
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

def merge_pr(pr: PullRequest, review_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge a pull request if it complies with requirements or if user confirms.

    Args:
        pr: GitHub PullRequest object
        review_result: Analysis results

    Returns:
        Result of the merge operation
    """
    if review_result["compliant"]:
        # Automatically merge if compliant
        try:
            merge_result = pr.merge(
                commit_title=f"Merge PR #{pr.number}: {pr.title}",
                commit_message=f"Automatically merged PR #{pr.number} as it complies with all requirements.",
                merge_method="merge"
            )
            logger.info(f"PR #{pr.number} automatically merged")
            print(f"\n✅ PR #{pr.number} automatically merged")
            return {
                "merged": True,
                "message": "PR automatically merged as it complies with all requirements."
            }
        except Exception as merge_error:
            logger.error(f"Error merging PR: {merge_error}")
            logger.error(traceback.format_exc())
            return {
                "merged": False,
                "message": f"Error merging PR: {str(merge_error)}"
            }
    else:
        # Ask for confirmation if not compliant
        print(f"\n❌ PR #{pr.number} does not comply with requirements")
        print("Issues found:")
        for issue in review_result["issues"]:
            print(f"- {issue}")
        
        user_input = input("\nDo you still want to merge this PR? (y/n): ")
        
        if user_input.lower() == "y":
            try:
                merge_result = pr.merge(
                    commit_title=f"Merge PR #{pr.number}: {pr.title}",
                    commit_message=f"Merged PR #{pr.number} with manual approval despite issues.",
                    merge_method="merge"
                )
                logger.info(f"PR #{pr.number} manually approved and merged")
                print(f"\n✅ PR #{pr.number} manually approved and merged")
                return {
                    "merged": True,
                    "message": "PR manually approved and merged."
                }
            except Exception as merge_error:
                logger.error(f"Error merging PR: {merge_error}")
                logger.error(traceback.format_exc())
                return {
                    "merged": False,
                    "message": f"Error merging PR: {str(merge_error)}"
                }
        else:
            logger.info(f"PR #{pr.number} not merged due to user decision")
            print(f"\n❌ PR #{pr.number} not merged")
            return {
                "merged": False,
                "message": "PR not merged due to user decision."
            }

def review_pr(github_client: Github, repo_name: str, pr_number: int) -> Dict[str, Any]:
    """Review a pull request."""
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

        # Try to merge the PR
        merge_result = merge_pr(pr, review_result)

        return {
            "pr_number": pr_number,
            "repo_name": repo_name,
            "compliant": review_result["compliant"],
            "approval_recommendation": review_result["approval_recommendation"],
            "merge_result": merge_result
        }

    except Exception as e:
        logger.error(f"Error reviewing PR: {e}")
        logger.error(traceback.format_exc())
        raise

def remove_bot_comments(event) -> Dict[str, Any]:
    """
    Remove bot comments from a pull request.

    Args:
        event: GitHub webhook event

    Returns:
        Result of the operation
    """
    try:
        # Get repository and PR
        repo_name = event.repository.full_name
        pr_number = event.number
        
        github_client = get_github_client(os.environ.get("GITHUB_TOKEN", ""))
        repo = get_repository(github_client, repo_name)
        pr = get_pull_request(repo, pr_number)
        
        # Get all comments
        comments = pr.get_issue_comments()
        
        # Remove bot comments
        removed_count = 0
        for comment in comments:
            if comment.user.login == "github-actions[bot]" or "PR Review Bot Analysis" in comment.body:
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

def pr_review_agent(event) -> Dict[str, Any]:
    """
    Run the PR review agent.

    Args:
        event: GitHub webhook event

    Returns:
        Result of the review
    """
    try:
        # Get repository and PR information
        repo_name = event.repository.full_name
        pr_number = event.number
        
        # Process the PR
        github_client = get_github_client(os.environ.get("GITHUB_TOKEN", ""))
        result = review_pr(github_client, repo_name, pr_number)
        
        # Print results to terminal
        if result["compliant"]:
            print(f"\n✅ PR #{pr_number} in {repo_name} complies with requirements")
            print(f"Recommendation: {result['approval_recommendation']}")
            if result.get("merge_result", {}).get("merged", False):
                print(f"Merge status: Merged")
            else:
                print(f"Merge status: Not merged - {result.get('merge_result', {}).get('message', 'Unknown reason')}")
        else:
            print(f"\n❌ PR #{pr_number} in {repo_name} does not comply with requirements")
            print(f"Recommendation: {result['approval_recommendation']}")
            print(f"Merge status: {result.get('merge_result', {}).get('message', 'Not merged')}")
            print("See PR comments for details")
        
        return result
    except Exception as e:
        logger.error(f"Error in PR review agent: {e}")
        logger.error(traceback.format_exc())
        print(f"\n❌ Error reviewing PR: {str(e)}")
        raise
