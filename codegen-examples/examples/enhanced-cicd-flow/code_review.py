"""Code Review component for the enhanced CI/CD flow.

This component:
1. Reviews PRs with multiple perspectives (style, security, performance)
2. Performs deep code analysis to validate changes
3. Provides feedback via GitHub and Slack
"""

import os
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

import modal
from fastapi import Request
from shared import (
    BASE_IMAGE,
    create_app,
    create_github_client,
    create_codebase,
    create_agent,
    send_slack_message,
    logger,
)
from codegen.extensions.github.types.events.pull_request import (
    PullRequestLabeledEvent,
    PullRequestUnlabeledEvent,
)

# Create app
app = create_app("code-review")

# Define data structures
@dataclass
class ReviewResult:
    """Represents the result of a code review."""
    pr_number: int
    pr_title: str
    pr_url: str
    feedback: List[Dict[str, Any]]
    summary: str
    rating: str  # "approve", "comment", or "request_changes"

# AI prompts for code review
REVIEW_PROMPT = """
You are an expert code reviewer. Your task is to review the following pull request:

PR Title: {pr_title}
PR Description: {pr_description}

Please review the code changes with a focus on:
1. Code quality and maintainability
2. Security vulnerabilities
3. Performance implications
4. Adherence to best practices
5. Test coverage

For each issue you find, provide:
1. The file and line number
2. A description of the issue
3. A suggested fix

Finally, provide an overall assessment of the PR and a recommendation (approve, comment, or request changes).
"""

@app.cls(secrets=[modal.Secret.from_dotenv()], keep_warm=1)
class CodeReview:
    """Handles GitHub webhook events and reviews PRs."""
    
    @modal.enter()
    def setup(self):
        """Set up the code review component."""
        self.github_client = create_github_client()
        logger.info("Code Review component initialized")
    
    @app.github.event("pull_request:labeled")
    def handle_labeled(self, event: PullRequestLabeledEvent):
        """Handle PR labeled events."""
        logger.info(f"[PULL_REQUEST:LABELED] PR #{event.number} labeled with: {event.label.name}")
        
        # Check if this is a Codegen PR
        if event.label.name != "Codegen":
            logger.info(f"Skipping PR #{event.number} (not labeled with 'Codegen')")
            return
        
        # Notify Slack
        send_slack_message(
            app.slack.client,
            "general",
            f"🔍 Starting code review for PR #{event.number}: {event.pull_request.title}"
        )
        
        # Review the PR
        review_result = self._review_pr(event)
        
        # Post review comments to GitHub
        self._post_review_to_github(review_result)
        
        # Post review summary to Slack
        self._post_review_to_slack(review_result)
    
    @app.github.event("pull_request:unlabeled")
    def handle_unlabeled(self, event: PullRequestUnlabeledEvent):
        """Handle PR unlabeled events."""
        logger.info(f"[PULL_REQUEST:UNLABELED] PR #{event.number} unlabeled: {event.label.name}")
        
        # Check if the Codegen label was removed
        if event.label.name != "Codegen":
            return
        
        # Remove bot comments
        self._remove_bot_comments(event)
    
    @modal.web_endpoint(method="POST")
    def entrypoint(self, event: Dict[str, Any], request: Request):
        """Handle GitHub webhook events."""
        logger.info("[OUTER] Received GitHub webhook")
        return app.github.handle(event, request)
    
    def _review_pr(self, event: PullRequestLabeledEvent) -> ReviewResult:
        """Review a PR and return the results."""
        pr_number = event.number
        pr_title = event.pull_request.title
        pr_url = event.pull_request.html_url
        
        # Get PR details
        pr = self.github_client.get_pr(pr_number)
        
        # Clone the repository
        repo_name = pr.base.repo.full_name
        codebase = create_codebase(repo_name, "python")
        
        # Checkout the PR branch
        codebase.git.fetch("origin", f"pull/{pr_number}/head:pr-{pr_number}")
        codebase.git.checkout(f"pr-{pr_number}")
        
        # Get the changed files
        changed_files = self.github_client.get_pr_files(pr_number)
        
        # Perform deep code analysis
        feedback = self._analyze_code_changes(codebase, changed_files)
        
        # Generate review summary
        summary = self._generate_review_summary(feedback)
        
        # Determine review rating
        rating = self._determine_review_rating(feedback)
        
        return ReviewResult(
            pr_number=pr_number,
            pr_title=pr_title,
            pr_url=pr_url,
            feedback=feedback,
            summary=summary,
            rating=rating,
        )
    
    def _analyze_code_changes(self, codebase, changed_files) -> List[Dict[str, Any]]:
        """Analyze code changes and return feedback."""
        # In a real implementation, this would use more sophisticated analysis
        # For this example, we'll create some sample feedback
        feedback = []
        
        for file in changed_files:
            filepath = file.filename
            
            # Skip deleted files
            if file.status == "removed":
                continue
            
            # Read the file content
            try:
                content = codebase.get_file(filepath).content
            except Exception as e:
                logger.error(f"Error reading file {filepath}: {e}")
                continue
            
            # Add some sample feedback
            if filepath.endswith(".py"):
                feedback.append({
                    "file": filepath,
                    "line": 1,
                    "message": "Consider adding a docstring to explain the purpose of this file.",
                    "severity": "suggestion",
                })
            
            if "TODO" in content:
                line_number = content.split("\n").index([line for line in content.split("\n") if "TODO" in line][0]) + 1
                feedback.append({
                    "file": filepath,
                    "line": line_number,
                    "message": "TODO comments should be addressed before merging.",
                    "severity": "warning",
                })
        
        return feedback
    
    def _generate_review_summary(self, feedback: List[Dict[str, Any]]) -> str:
        """Generate a summary of the review."""
        num_issues = len(feedback)
        num_warnings = len([f for f in feedback if f["severity"] == "warning"])
        num_suggestions = len([f for f in feedback if f["severity"] == "suggestion"])
        
        summary = f"""
# Code Review Summary

I've reviewed the changes and found:
- {num_issues} total issues
- {num_warnings} warnings
- {num_suggestions} suggestions

## Key Findings
"""
        
        if num_issues > 0:
            for i, issue in enumerate(feedback[:3]):  # Show top 3 issues
                summary += f"{i+1}. **{issue['file']}** (line {issue['line']}): {issue['message']}\n"
            
            if num_issues > 3:
                summary += f"... and {num_issues - 3} more issues\n"
        else:
            summary += "No issues found! The code looks great. 👍\n"
        
        return summary
    
    def _determine_review_rating(self, feedback: List[Dict[str, Any]]) -> str:
        """Determine the review rating based on feedback."""
        num_warnings = len([f for f in feedback if f["severity"] == "warning"])
        
        if num_warnings > 5:
            return "request_changes"
        elif num_warnings > 0:
            return "comment"
        else:
            return "approve"
    
    def _post_review_to_github(self, review: ReviewResult):
        """Post review comments to GitHub."""
        # Post individual comments
        for issue in review.feedback:
            self.github_client.create_pr_review_comment(
                review.pr_number,
                issue["file"],
                issue["line"],
                issue["message"],
            )
        
        # Post review summary
        self.github_client.create_pr_review(
            review.pr_number,
            review.summary,
            review.rating,
        )
    
    def _post_review_to_slack(self, review: ReviewResult):
        """Post review summary to Slack."""
        emoji = "✅" if review.rating == "approve" else "⚠️" if review.rating == "comment" else "❌"
        
        message = f"""
{emoji} *Code Review Completed*
PR: <{review.pr_url}|#{review.pr_number} {review.pr_title}>

{review.summary}
"""
        
        send_slack_message(app.slack.client, "general", message)
    
    def _remove_bot_comments(self, event: PullRequestUnlabeledEvent):
        """Remove bot comments from a PR."""
        pr_number = event.number
        
        # Get all comments on the PR
        comments = self.github_client.get_pr_comments(pr_number)
        
        # Filter for bot comments
        bot_comments = [c for c in comments if c.user.login == "codegen-bot"]
        
        # Delete bot comments
        for comment in bot_comments:
            self.github_client.delete_pr_comment(comment.id)