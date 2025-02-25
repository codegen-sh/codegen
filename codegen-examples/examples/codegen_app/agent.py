   

from codegen.agents.code_agent import CodeAgent
from codegen.extensions.github.types.events.pull_request import PullRequestLabeledEvent
from codegen.extensions.langchain.tools import GithubCreatePRCommentTool, GithubCreatePRReviewCommentTool, GithubViewPRTool
from codegen.sdk.core.codebase import Codebase


def pr_review_agent(codebase: Codebase, event: PullRequestLabeledEvent) -> None:
    review_atention_message = f"CodegenBot is starting to review the PR please wait..."
    comment =codebase._op.create_pr_comment(event.number, review_atention_message)
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
    result = agent.run(prompt)
    comment.delete()