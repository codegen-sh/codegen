import logging
from codegen.agents.code_agent import CodeAgent
from codegen.extensions.github.types.pull_request import PullRequestLabeledEvent

from codegen.extensions.langchain.tools import GithubCreatePRCommentTool, GithubCreatePRReviewCommentTool, GithubViewPRTool
from codegen.sdk.core.codebase import Codebase

logging.basicConfig(level=logging.INFO, force=True)
logger = logging.getLogger(__name__)


def lint_for_dev_import_violations(codebase: Codebase, event: PullRequestLabeledEvent):
    patch, commit_shas, modified_symbols = codebase.get_modified_symbols_in_pr(event.pull_request.number)
    modified_files = set(commit_shas.keys())

    DIR_NAME = "packages/next/src/client/components/react-dev-overlay"
    directory = codebase.get_directory(DIR_NAME)

    # Initialize a list to store all violations
    violations = []

    print("modified_files", modified_files)

    # Check if directory exists before proceeding
    if directory is not None and hasattr(directory, "files"):
        for file in directory.files:
            print("checking file", file.filepath)
            for imp in file.inbound_imports:
                print("file", imp.file.filepath)
                print("checking import", imp.import_statement)
                # Check if the import is from outside the directory and is in the modified files
                if imp.file not in directory and imp.file.filepath in modified_files:
                    # Skip require statements
                    if "require" in imp.import_statement:
                        continue
                    violation = f"- Violation in `{file.filepath}`: Importing from `{imp.file.filepath}` ([link]({imp.github_url}))"
                    violations.append(violation)
                    logger.info(f"Found violation: {violation}")

        # Only create a PR comment if violations are found
        if violations:
            review_attention_message = "## Dev Import Violations Found\n\n"
            review_attention_message += "The following files have imports that violate development overlay rules:\n\n"
            review_attention_message += "\n".join(violations)
            review_attention_message += "\n\nPlease ensure that development imports are not imported in production code."

            # Create PR comment with the formatted message
            codebase._op.create_pr_comment(event.pull_request.number, review_attention_message)


def review_with_codegen_agent(codebase: Codebase, event: PullRequestLabeledEvent):
    review_initial_message = "CodegenBot is starting to review the PR please wait..."
    comment = codebase._op.create_pr_comment(event.number, review_initial_message)
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
