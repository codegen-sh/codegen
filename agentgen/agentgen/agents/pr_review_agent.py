"""
PR Review Agent for analyzing pull requests against requirements and codebase patterns.
"""

import os
import re
import json
import logging
import traceback
from typing import Dict, List, Optional, Any, Tuple, Union
from uuid import uuid4

from github import Github
from github.PullRequest import PullRequest
from github.Repository import Repository
from langchain.tools import BaseTool
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables.config import RunnableConfig

from agentgen.agents.code_agent import CodeAgent
from agentgen.agents.utils import AgentConfig
from agentgen.extensions.planning.manager import PlanManager, ProjectPlan, Step, Requirement
from agentgen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class PRReviewAgent(CodeAgent):
    """Agent for reviewing pull requests against requirements and codebase patterns."""
    
    def __init__(
        self,
        codebase,
        github_token: Optional[str] = None,
        slack_token: Optional[str] = None,
        slack_channel_id: Optional[str] = None,
        output_dir: Optional[str] = None,
        model_provider: str = "anthropic",
        model_name: str = "claude-3-7-sonnet-latest",
        memory: bool = True,
        tools: Optional[list[BaseTool]] = None,
        tags: Optional[list[str]] = [],
        metadata: Optional[dict] = {},
        agent_config: Optional[AgentConfig] = None,
        thread_id: Optional[str] = None,
        logger: Optional[Any] = None,
        **kwargs,
    ):
        """Initialize a PRReviewAgent.

        Args:
            codebase: The codebase to operate on
            github_token: GitHub token for API access
            slack_token: Slack token for API access
            slack_channel_id: Slack channel ID for notifications
            output_dir: Directory for output files
            model_provider: The model provider to use ("anthropic" or "openai")
            model_name: Name of the model to use
            memory: Whether to let LLM keep track of the conversation history
            tools: Additional tools to use
            tags: Tags to add to the agent trace
            metadata: Metadata to use for the agent
            agent_config: Configuration for the agent
            thread_id: Thread ID for message history
            logger: Logger instance
            **kwargs: Additional LLM configuration options
        """
        super().__init__(
            codebase=codebase,
            model_provider=model_provider,
            model_name=model_name,
            memory=memory,
            tools=tools,
            tags=tags,
            metadata=metadata,
            agent_config=agent_config,
            thread_id=thread_id,
            logger=logger,
            **kwargs,
        )
        
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN", "")
        if not self.github_token:
            raise ValueError("GitHub token is required")
        
        self.github_client = Github(self.github_token)
        
        self.slack_token = slack_token or os.environ.get("SLACK_BOT_TOKEN", "")
        self.slack_channel_id = slack_channel_id or os.environ.get("SLACK_CHANNEL_ID", "")
        
        self.output_dir = output_dir or os.environ.get("OUTPUT_DIR", "output")
        
        self.plan_manager = PlanManager(
            output_dir=self.output_dir,
            anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
            openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
        )
    
    def create_plan_from_markdown(self, markdown_content: str, title: str, description: str) -> ProjectPlan:
        """Create a project plan from markdown content."""
        return self.plan_manager.create_plan_from_markdown(markdown_content, title, description)
    
    def get_next_step(self) -> Optional[Step]:
        """Get the next pending step in the current plan."""
        return self.plan_manager.get_next_step()
    
    def update_step_status(self, step_id: str, status: str, pr_number: Optional[int] = None, details: Optional[str] = None) -> None:
        """Update the status of a step in the current plan."""
        self.plan_manager.update_step_status(step_id, status, pr_number, details)
    
    def generate_progress_report(self) -> str:
        """Generate a progress report for the current plan."""
        return self.plan_manager.generate_progress_report()
    
    def review_pr(self, repo_name: str, pr_number: int) -> Dict[str, Any]:
        """Review a pull request against requirements and codebase patterns.
        
        Args:
            repo_name: Name of the repository (e.g., "owner/repo")
            pr_number: Number of the pull request
            
        Returns:
            Dictionary with review results
        """
        logger.info(f"Reviewing PR #{pr_number} in {repo_name}")
        
        try:
            repo = self.github_client.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            pr_title = pr.title
            pr_body = pr.body or ""
            pr_files = list(pr.get_files())
            
            plan = self.plan_manager.load_current_plan()
            
            prompt = self._prepare_pr_analysis_prompt(repo_name, pr, pr_files, plan)
            
            analysis_result = self.run(prompt)
            
            review_result = self._parse_analysis_result(analysis_result)
            
            self._post_review_comment(repo, pr, review_result)
            
            self._submit_review(repo, pr, review_result)
            
            self._update_plan_from_pr(pr, review_result)
            
            if self.slack_token and self.slack_channel_id:
                self._send_slack_notification(repo_name, pr_number, review_result)
            
            return {
                "pr_number": pr_number,
                "repo_name": repo_name,
                "compliant": review_result.get("compliant", False),
                "approval_recommendation": review_result.get("approval_recommendation", "request_changes"),
                "issues": review_result.get("issues", []),
                "suggestions": review_result.get("suggestions", []),
            }
        
        except Exception as e:
            logger.error(f"Error reviewing PR: {e}")
            logger.error(traceback.format_exc())
            
            return {
                "pr_number": pr_number,
                "repo_name": repo_name,
                "compliant": False,
                "approval_recommendation": "request_changes",
                "issues": [f"Error during review: {str(e)}"],
                "suggestions": ["Please review manually"],
                "error": str(e),
            }
    
    def _prepare_pr_analysis_prompt(self, repo_name: str, pr: PullRequest, pr_files: List[Any], plan: Optional[ProjectPlan] = None) -> str:
        """Prepare the prompt for PR analysis."""
        pr_diff = pr.get_patch()
        
        pr_title = pr.title
        pr_body = pr.body or "No description provided"
        
        file_paths = [f.filename for f in pr_files]
        
        prompt = f"""
        You are a PR review bot that checks if pull requests comply with project requirements and codebase patterns.

        Please analyze this pull request:
        PR #{pr.number}: {pr_title}

        PR Description:
        {pr_body}

        Files changed:
        {', '.join(file_paths)}

        PR Diff:
        ```diff
        {pr_diff}
        ```
        """
        
        if plan:
            prompt += f"""
            This PR should comply with the project plan:
            
            Project: {plan.title}
            Description: {plan.description}
            
            Requirements:
            """
            
            for req in plan.requirements:
                prompt += f"- {req.description} (Status: {req.status})\n"
            
            prompt += "\nSteps:\n"
            
            for step in plan.steps:
                prompt += f"- {step.description} (Status: {step.status})\n"
        
        prompt += """
        Your task:
        1. Analyze if the PR complies with the requirements and follows good coding practices
        2. Identify any issues or non-compliance
        3. Provide specific suggestions for improvement if needed
        4. Determine if the PR should be approved or needs changes

        Format your final response as a JSON object with the following structure:
        {
            "compliant": true/false,
            "issues": ["issue1", "issue2", ...],
            "suggestions": [
                {
                    "description": "suggestion1",
                    "file_path": "path/to/file.py",
                    "line_number": 42
                },
                ...
            ],
            "approval_recommendation": "approve" or "request_changes",
            "review_comment": "Your detailed review comment here"
        }
        """
        
        return prompt
    
    def _parse_analysis_result(self, analysis_result: str) -> Dict[str, Any]:
        """Parse the analysis result to extract the JSON."""
        try:
            json_match = re.search(r'```json\s*(.*?)\s*```', analysis_result, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_match = re.search(r'({.*})', analysis_result, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    logger.error("Could not extract JSON from analysis result")
                    return {
                        "compliant": False,
                        "issues": ["Failed to analyze PR properly"],
                        "suggestions": [],
                        "approval_recommendation": "request_changes",
                        "review_comment": "Failed to analyze PR properly. Please review manually.",
                    }

            result = json.loads(json_str)
            return result
        except Exception as e:
            logger.error(f"Error parsing analysis result: {e}")
            logger.error(traceback.format_exc())
            
            return {
                "compliant": False,
                "issues": ["Failed to analyze PR properly"],
                "suggestions": [],
                "approval_recommendation": "request_changes",
                "review_comment": "Failed to analyze PR properly. Please review manually.",
            }
    
    def _post_review_comment(self, repo: Repository, pr: PullRequest, review_result: Dict[str, Any]) -> None:
        """Post a review comment on the pull request."""
        comment = f"# PR Review Bot Analysis\n\n"

        if review_result.get("compliant", False):
            comment += ":white_check_mark: **This PR complies with project requirements.**\n\n"
        else:
            comment += ":x: **This PR does not fully comply with project requirements.**\n\n"

        issues = review_result.get("issues", [])
        if issues and len(issues) > 0:
            comment += "## Issues\n\n"
            for issue in issues:
                comment += f"- {issue}\n"
            comment += "\n"

        suggestions = review_result.get("suggestions", [])
        if suggestions and len(suggestions) > 0:
            comment += "## Suggestions\n\n"
            for suggestion in suggestions:
                if isinstance(suggestion, dict):
                    desc = suggestion.get("description", "")
                    file_path = suggestion.get("file_path")
                    line_number = suggestion.get("line_number")
                    
                    if file_path and line_number:
                        comment += f"- {desc} (in `{file_path}` at line {line_number})\n"
                    elif file_path:
                        comment += f"- {desc} (in `{file_path}`)\n"
                    else:
                        comment += f"- {desc}\n"
                else:
                    comment += f"- {suggestion}\n"
            comment += "\n"

        comment += "## Detailed Review\n\n"
        comment += review_result.get("review_comment", "No detailed review provided.")

        try:
            pr.create_issue_comment(comment)
        except Exception as e:
            logger.error(f"Error posting review comment: {e}")
    
    def _submit_review(self, repo: Repository, pr: PullRequest, review_result: Dict[str, Any]) -> None:
        """Submit a formal review on the pull request."""
        if review_result.get("approval_recommendation") == "approve":
            review_state = "APPROVE"
        else:
            review_state = "REQUEST_CHANGES"

        try:
            pr.create_review(
                body=review_result.get("review_comment", ""),
                event=review_state
            )
        except Exception as e:
            logger.error(f"Error submitting formal review: {e}")
    
    def _update_plan_from_pr(self, pr: PullRequest, review_result: Dict[str, Any]) -> None:
        """Update the plan based on PR review results."""
        plan = self.plan_manager.load_current_plan()
        if not plan:
            return
        
        pr_number = pr.number
        pr_title = pr.title
        pr_body = pr.body or ""
        
        is_compliant = review_result.get("compliant", False)
        
        step_id_match = re.search(r'step-(\d+)', pr_title + " " + pr_body, re.IGNORECASE)
        if step_id_match:
            step_id = f"step-{step_id_match.group(1)}"
            
            if is_compliant:
                self.plan_manager.update_step_status(
                    step_id=step_id,
                    status="completed",
                    pr_number=pr_number,
                    details=f"Implemented in PR #{pr_number}: {pr_title}"
                )
            else:
                self.plan_manager.update_step_status(
                    step_id=step_id,
                    status="in_progress",
                    pr_number=pr_number,
                    details=f"In progress in PR #{pr_number}: {pr_title}"
                )
        
        req_id_match = re.search(r'req-(\d+)', pr_title + " " + pr_body, re.IGNORECASE)
        if req_id_match:
            req_id = f"req-{req_id_match.group(1)}"
            
            if is_compliant:
                self.plan_manager.update_requirement_status(
                    req_id=req_id,
                    status="completed",
                    pr_number=pr_number,
                    details=f"Implemented in PR #{pr_number}: {pr_title}"
                )
            else:
                self.plan_manager.update_requirement_status(
                    req_id=req_id,
                    status="in_progress",
                    pr_number=pr_number,
                    details=f"In progress in PR #{pr_number}: {pr_title}"
                )
    
    def _send_slack_notification(self, repo_name: str, pr_number: int, review_result: Dict[str, Any]) -> None:
        """Send a notification to Slack about the PR review."""
        from slack_sdk import WebClient
        
        try:
            slack_client = WebClient(token=self.slack_token)
            
            message = f"*PR Review Result for {repo_name}#{pr_number}*\n\n"
            
            if review_result.get("compliant", False):
                message += ":white_check_mark: *This PR complies with project requirements.*\n\n"
            else:
                message += ":x: *This PR does not fully comply with project requirements.*\n\n"
            
            issues = review_result.get("issues", [])
            if issues and len(issues) > 0:
                message += "*Issues:*\n"
                for issue in issues:
                    message += f"- {issue}\n"
                message += "\n"
            
            suggestions = review_result.get("suggestions", [])
            if suggestions and len(suggestions) > 0:
                message += "*Suggestions:*\n"
                for suggestion in suggestions:
                    if isinstance(suggestion, dict):
                        desc = suggestion.get("description", "")
                        file_path = suggestion.get("file_path")
                        line_number = suggestion.get("line_number")
                        
                        if file_path and line_number:
                            message += f"- {desc} (in `{file_path}` at line {line_number})\n"
                        elif file_path:
                            message += f"- {desc} (in `{file_path}`)\n"
                        else:
                            message += f"- {desc}\n"
                    else:
                        message += f"- {suggestion}\n"
                message += "\n"
            
            if review_result.get("approval_recommendation") == "approve":
                message += ":thumbsup: *Recommendation: Approve*\n"
            else:
                message += ":thumbsdown: *Recommendation: Request Changes*\n"
            
            message += f"\n<https://github.com/{repo_name}/pull/{pr_number}|View PR on GitHub>"
            
            slack_client.chat_postMessage(
                channel=self.slack_channel_id,
                text=message
            )
            
            logger.info(f"Sent PR review notification to Slack channel {self.slack_channel_id}")
        
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
            logger.error(traceback.format_exc())
