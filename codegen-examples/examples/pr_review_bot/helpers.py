from github import Github
from codegen.extensions.github.types.events.pull_request import PullRequestUnlabeledEvent
from logging import getLogger

import os

from codegen import Codebase

from codegen.extensions.github.types.events.pull_request import PullRequestLabeledEvent
from codegen.configs.models.secrets import SecretsConfig
from codegen import CodeAgent

from codegen.extensions.langchain.tools import (
    # Github
    GithubViewPRTool,
    GithubCreatePRCommentTool,
    GithubCreatePRReviewCommentTool,
)

from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = getLogger(__name__)


def remove_bot_comments(event: PullRequestUnlabeledEvent):
    g = Github(os.getenv("GITHUB_API_KEY"))
    logger.info(f"{event.organization.login}/{event.repository.name}")
    repo = g.get_repo(f"{event.organization.login}/{event.repository.name}")

    pr = repo.get_pull(int(event.number))
    comments = pr.get_comments()
    if comments:
        for comment in comments:
            logger.info("removing comment")
            logger.info(comment.user.login)
            if comment.user.login == "codegen-team":
                comment.delete()
    reviews = pr.get_reviews()

    if reviews:
        for review in reviews:
            logger.info("removing review")
            logger.info(review.user.login)
            if review.user.login == "codegen-team":
                review.delete()

    issue_comments = pr.get_issue_comments()
    if issue_comments:
        for comment in issue_comments:
            logger.info("removing comment")
            logger.info(comment.user.login)
            if comment.user.login == "codegen-team":
                comment.delete()


def pr_review_agent(event: PullRequestLabeledEvent) -> None:
    # Pull a subset of SWE bench
    repo_str = f"{event.organization.login}/{event.repository.name}"
    codebase = Codebase.from_repo(repo_str, language="python", secrets=SecretsConfig(github_token=os.environ["GITHUB_TOKEN"]))
    review_atention_message = "CodegenBot is starting to review the PR please wait..."
    comment = codebase._op.create_pr_comment(event.number, review_atention_message)
    # Define tools first
    pr_tools = [
        GithubViewPRTool(codebase),
        GithubCreatePRCommentTool(codebase),
        GithubCreatePRReviewCommentTool(codebase),
    ]

    # Create agent with the defined tools
    agent = CodeAgent(codebase=codebase, tools=pr_tools)

    # Using a prompt from SWE Bench
    prompt = f"""
Hey CodegenBot!

Here's a SWE task for you. Please Review this pull request!
{event.pull_request.url}
Do not terminate until have reviewed the pull request and are satisfied with your review.

Review this Pull request like the señor ingenier you are
be explicit about the changes, produce a short summary, and point out possible improvements where pressent dont be self congratulatory stick to the facts
use the tools at your disposal to create propper pr reviews include code snippets if needed, and suggest improvements if feel its necesary
"""
    # Run the agent
    agent.run(prompt)
    comment.delete()
