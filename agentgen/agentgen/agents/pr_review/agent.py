"""
Enhanced PR Review Agent with planning and research capabilities.
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

from codegen.agents.code_agent import CodeAgent
from codegen.agents.utils import AgentConfig
from codegen.extensions.planning.manager import PlanManager, ProjectPlan, Step, Requirement
from codegen.extensions.research.researcher import Researcher, CodeInsight, ResearchResult
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class PRReviewAgent(CodeAgent):
    """Enhanced agent for reviewing pull requests with planning and research capabilities."""
    
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
        
        self.researcher = Researcher(
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
    
    def research_codebase(self, query: str, file_patterns: Optional[List[str]] = None) -> ResearchResult:
        """Research a codebase for patterns and insights based on a query."""
        return self.researcher.research_codebase(self.codebase, query, file_patterns)
    
    def generate_research_report(self, query: Optional[str] = None) -> str:
        """Generate a research report."""
        return self.researcher.generate_research_report(query)
    
    def analyze_pr_requirements(self, pr_title: str, pr_body: str, pr_files: List[Any]) -> Dict[str, Any]:
        """Analyze PR requirements against the project plan and codebase patterns."""
        plan = self.plan_manager.load_current_plan()
        
        # Extract keywords from PR title and body
        keywords = self._extract_keywords(pr_title + " " + pr_body)
        
        # Research the codebase for patterns related to the PR
        research_results = None
        try:
            if keywords:
                research_results = self.research_codebase(" ".join(keywords))
        except Exception as e:
            logger.error(f"Error researching codebase: {e}")
            logger.error(traceback.format_exc())
        
        # Analyze the PR against the plan requirements
        requirements_analysis = self._analyze_requirements(pr_title, pr_body, plan)
        
        # Analyze the PR against codebase patterns
        patterns_analysis = self._analyze_patterns(pr_files, research_results)
        
        return {
            "requirements_analysis": requirements_analysis,
            "patterns_analysis": patterns_analysis,
            "research_results": research_results,
        }
    
    def _analyze_requirements(self, pr_title: str, pr_body: str, plan: Optional[ProjectPlan]) -> Dict[str, Any]:
        """Analyze PR against plan requirements."""
        if not plan:
            return {
                "has_plan": False,
                "matched_requirements": [],
                "unmatched_requirements": [],
                "compliance_score": 0.0,
            }
        
        matched_requirements = []
        unmatched_requirements = []
        
        # Check for requirement IDs in PR title and body
        for req in plan.requirements:
            if req.id.lower() in pr_title.lower() or req.id.lower() in pr_body.lower():
                matched_requirements.append(req)
            else:
                # Check if requirement description keywords are in PR title or body
                req_keywords = self._extract_keywords(req.description)
                pr_keywords = self._extract_keywords(pr_title + " " + pr_body)
                
                if any(keyword in pr_keywords for keyword in req_keywords):
                    matched_requirements.append(req)
                else:
                    unmatched_requirements.append(req)
        
        # Calculate compliance score
        total_requirements = len(plan.requirements)
        if total_requirements > 0:
            compliance_score = len(matched_requirements) / total_requirements
        else:
            compliance_score = 1.0
        
        return {
            "has_plan": True,
            "matched_requirements": matched_requirements,
            "unmatched_requirements": unmatched_requirements,
            "compliance_score": compliance_score,
        }
    
    def _analyze_patterns(self, pr_files: List[Any], research_results: Optional[ResearchResult]) -> Dict[str, Any]:
        """Analyze PR against codebase patterns."""
        if not research_results:
            return {
                "has_patterns": False,
                "matched_patterns": [],
                "unmatched_patterns": [],
                "pattern_compliance_score": 0.0,
            }
        
        matched_patterns = []
        unmatched_patterns = []
        
        # Check if PR files match patterns found in research
        for insight in research_results.insights:
            pattern_matched = False
            
            for pr_file in pr_files:
                if pr_file.filename == insight.file_path:
                    pattern_matched = True
                    break
            
            if pattern_matched:
                matched_patterns.append(insight)
            else:
                unmatched_patterns.append(insight)
        
        # Calculate pattern compliance score
        total_patterns = len(research_results.insights)
        if total_patterns > 0:
            pattern_compliance_score = len(matched_patterns) / total_patterns
        else:
            pattern_compliance_score = 1.0
        
        return {
            "has_patterns": True,
            "matched_patterns": matched_patterns,
            "unmatched_patterns": unmatched_patterns,
            "pattern_compliance_score": pattern_compliance_score,
        }
    
    def review_pr(self, repo_name: str, pr_number: int) -> Dict[str, Any]:
        """Review a pull request and provide feedback."""
        logger.info(f"Reviewing PR #{pr_number} in {repo_name}")
        
        try:
            repo = self.github_client.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            pr_title = pr.title
            pr_body = pr.body or ""
            pr_files = list(pr.get_files())
            
            # Analyze PR requirements and patterns
            analysis_result = self.analyze_pr_requirements(pr_title, pr_body, pr_files)
            
            # Prepare prompt for LLM analysis
            prompt = self._prepare_pr_analysis_prompt(repo_name, pr, pr_files, analysis_result)
            
            # Run LLM analysis
            llm_analysis_result = self.run(prompt)
            
            # Parse LLM analysis result
            review_result = self._parse_analysis_result(llm_analysis_result)
            
            # Post review comment on GitHub
            self._post_review_comment(repo, pr, review_result)
            
            # Submit formal review on GitHub
            self._submit_review(repo, pr, review_result)
            
            # Update plan based on PR review
            self._update_plan_from_pr(pr, review_result)
            
            # Send Slack notification if configured
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
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "by", "about", "as"}
        
        words = re.findall(r'\b\w+\b', text.lower())
        
        keywords = [word for word in words if word not in common_words and len(word) > 3]
        
        return list(set(keywords))
    
    def _prepare_pr_analysis_prompt(self, repo_name: str, pr: PullRequest, pr_files: List[Any], analysis_result: Dict[str, Any]) -> str:
        """Prepare prompt for PR analysis."""
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
        {pr_diff[:10000]}
        ```
        """
        
        # Add requirements analysis
        requirements_analysis = analysis_result.get("requirements_analysis", {})
        if requirements_analysis.get("has_plan", False):
            prompt += f"""
            Requirements Analysis:
            - Compliance Score: {requirements_analysis.get("compliance_score", 0.0) * 100:.1f}%
            
            Matched Requirements:
            """
            
            for req in requirements_analysis.get("matched_requirements", []):
                prompt += f"- {req.id}: {req.description}\n"
            
            prompt += "\nUnmatched Requirements:\n"
            
            for req in requirements_analysis.get("unmatched_requirements", []):
                prompt += f"- {req.id}: {req.description}\n"
        
        # Add patterns analysis
        patterns_analysis = analysis_result.get("patterns_analysis", {})
        if patterns_analysis.get("has_patterns", False):
            prompt += f"""
            Codebase Patterns Analysis:
            - Pattern Compliance Score: {patterns_analysis.get("pattern_compliance_score", 0.0) * 100:.1f}%
            
            Matched Patterns:
            """
            
            for pattern in patterns_analysis.get("matched_patterns", []):
                prompt += f"""
                - {pattern.description}
                  File: {pattern.file_path}
                  {"Line: " + str(pattern.line_number) if pattern.line_number else ""}
                  Category: {pattern.category}
                """
            
            prompt += "\nUnmatched Patterns:\n"
            
            for pattern in patterns_analysis.get("unmatched_patterns", []):
                prompt += f"""
                - {pattern.description}
                  File: {pattern.file_path}
                  {"Line: " + str(pattern.line_number) if pattern.line_number else ""}
                  Category: {pattern.category}
                """
        
        # Add research results
        research_results = analysis_result.get("research_results")
        if research_results:
            prompt += f"""
            Codebase Research Insights:
            
            {research_results.summary}
            
            Relevant code patterns:
            """
            
            for insight in research_results.insights[:5]: 
                prompt += f"""
                - {insight.description}
                  File: {insight.file_path}
                  {"Line: " + str(insight.line_number) if insight.line_number else ""}
                  Category: {insight.category}
                  
                  ```
                  {insight.code_snippet if insight.code_snippet else "No code snippet available"}
                  ```
                """
        
        prompt += """
        Your task:
        1. Analyze if the PR complies with the requirements and follows good coding practices
        2. Check if the PR follows the codebase patterns and architecture
        3. Identify any issues or non-compliance
        4. Provide specific suggestions for improvement if needed
        5. Determine if the PR should be approved or needs changes

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
        """Parse the analysis result from LLM."""
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
        """Post a review comment on the PR."""
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
        """Submit a formal review on the PR."""
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
        """Update the project plan based on PR review."""
        plan = self.plan_manager.load_current_plan()
        if not plan:
            return
        
        pr_number = pr.number
        pr_title = pr.title
        pr_body = pr.body or ""
        
        is_compliant = review_result.get("compliant", False)
        
        # Check for step ID in PR title or body
        step_id_match = re.search(r'step-([\w-]+)', pr_title + " " + pr_body, re.IGNORECASE)
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
        
        # Check for requirement ID in PR title or body
        req_id_match = re.search(r'req-([\w-]+)', pr_title + " " + pr_body, re.IGNORECASE)
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
