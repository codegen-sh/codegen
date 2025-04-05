"""
Enhanced PR Review Agent with planning and research capabilities.
"""

import os
import sys
import logging
import traceback
from logging import getLogger
from typing import Dict, List, Any, Optional, Tuple
from github import Github
from github.Repository import Repository
from github.PullRequest import PullRequest
from github.ContentFile import ContentFile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = getLogger("pr_review_agent")

from agentgen.agents.code_agent import CodeAgent
from agentgen.agents.utils import AgentConfig
from agentgen.extensions.planning.manager import PlanManager, ProjectPlan, Step, Requirement
from agentgen.extensions.research.researcher import Researcher, CodeInsight, ResearchResult
from agentgen.extensions.reflection.reflector import Reflector, ReflectionResult
from agentgen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class PRReviewAgent(CodeAgent):
    """Enhanced agent for reviewing pull requests with planning, research, and reflection capabilities."""
    
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
        
        self.reflector = Reflector(
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
            
            # Apply reflection to improve the review
            improved_review_result = self._apply_reflection(review_result, analysis_result)
            
            # Post review comment on GitHub
            self._post_review_comment(repo, pr, improved_review_result)
            
            # Submit formal review on GitHub
            self._submit_review(repo, pr, improved_review_result)
            
            # Update plan based on PR review
            self._update_plan_from_pr(pr, improved_review_result)
            
            # Send notification to Slack
            self._send_slack_notification(repo_name, pr_number, improved_review_result)
            
            # Auto-merge if PR is compliant
            if improved_review_result.get("compliant", False) and improved_review_result.get("approval_recommendation") == "approve":
                self._auto_merge_pr(repo, pr, improved_review_result)
            
            return improved_review_result
        
        except Exception as e:
            logger.error(f"Error reviewing PR: {e}")
            logger.error(traceback.format_exc())
            
            return {
                "compliant": False,
                "issues": [f"Error reviewing PR: {e}"],
                "suggestions": [],
                "approval_recommendation": "request_changes",
                "review_comment": f"Error reviewing PR: {e}",
            }
    
    def _apply_reflection(self, review_result: Dict[str, Any], analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Apply reflection to improve the PR review."""
        try:
            # Extract requirements and patterns from analysis result
            requirements = []
            if analysis_result.get("requirements_analysis", {}).get("has_plan", False):
                for req in analysis_result.get("requirements_analysis", {}).get("matched_requirements", []):
                    requirements.append({
                        "id": req.id,
                        "description": req.description,
                        "status": req.status,
                    })
                
                for req in analysis_result.get("requirements_analysis", {}).get("unmatched_requirements", []):
                    requirements.append({
                        "id": req.id,
                        "description": req.description,
                        "status": req.status,
                    })
            
            codebase_patterns = []
            if analysis_result.get("patterns_analysis", {}).get("has_patterns", False):
                for pattern in analysis_result.get("patterns_analysis", {}).get("matched_patterns", []):
                    codebase_patterns.append({
                        "file_path": pattern.file_path,
                        "line_number": pattern.line_number,
                        "category": pattern.category,
                        "description": pattern.description,
                        "code_snippet": pattern.code_snippet,
                    })
                
                for pattern in analysis_result.get("patterns_analysis", {}).get("unmatched_patterns", []):
                    codebase_patterns.append({
                        "file_path": pattern.file_path,
                        "line_number": pattern.line_number,
                        "category": pattern.category,
                        "description": pattern.description,
                        "code_snippet": pattern.code_snippet,
                    })
            
            # Evaluate the review
            reflection_result = self.reflector.evaluate_pr_review(
                pr_review=review_result,
                requirements=requirements,
                codebase_patterns=codebase_patterns,
            )
            
            logger.info(f"Reflection score: {reflection_result.score}")
            
            # If the review is not valid or has a low score, improve it
            if not reflection_result.is_valid or reflection_result.score < 0.8:
                logger.info(f"Improving PR review based on reflection feedback: {reflection_result.feedback}")
                
                improved_review = self.reflector.improve_pr_review(
                    pr_review=review_result,
                    reflection_result=reflection_result,
                    requirements=requirements,
                    codebase_patterns=codebase_patterns,
                )
                
                return improved_review
            
            return review_result
        
        except Exception as e:
            logger.error(f"Error applying reflection: {e}")
            logger.error(traceback.format_exc())
            
            return review_result
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        # Simple keyword extraction
        words = re.findall(r'\b\w+\b', text.lower())
        stopwords = {'a', 'an', 'the', 'and', 'or', 'but', 'if', 'then', 'else', 'when', 'at', 'from', 'by', 'for', 'with', 'about', 'to', 'in', 'on', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'shall', 'should', 'may', 'might', 'must', 'can', 'could'}
        keywords = [word for word in words if word not in stopwords and len(word) > 2]
        return keywords
    
    def _prepare_pr_analysis_prompt(self, repo_name: str, pr: PullRequest, pr_files: List[Any], analysis_result: Dict[str, Any]) -> str:
        """Prepare a prompt for LLM analysis of the PR."""
        prompt = f"""You are a PR review bot that checks if pull requests comply with project requirements and codebase patterns.

Repository: {repo_name}
PR #{pr.number}: {pr.title}
PR Description: {pr.body or "No description provided"}

Files changed:
"""
        
        for file in pr_files:
            prompt += f"- {file.filename} (+{file.additions}, -{file.deletions})\n"
        
        prompt += "\nRequirements Analysis:\n"
        
        requirements_analysis = analysis_result.get("requirements_analysis", {})
        if requirements_analysis.get("has_plan", False):
            prompt += f"Compliance Score: {requirements_analysis.get('compliance_score', 0.0):.2f}\n\n"
            
            matched_requirements = requirements_analysis.get("matched_requirements", [])
            if matched_requirements:
                prompt += "Matched Requirements:\n"
                for req in matched_requirements:
                    prompt += f"- {req.id}: {req.description}\n"
                prompt += "\n"
            
            unmatched_requirements = requirements_analysis.get("unmatched_requirements", [])
            if unmatched_requirements:
                prompt += "Unmatched Requirements:\n"
                for req in unmatched_requirements:
                    prompt += f"- {req.id}: {req.description}\n"
                prompt += "\n"
        else:
            prompt += "No project plan found.\n\n"
        
        prompt += "Codebase Patterns Analysis:\n"
        
        patterns_analysis = analysis_result.get("patterns_analysis", {})
        if patterns_analysis.get("has_patterns", False):
            prompt += f"Pattern Compliance Score: {patterns_analysis.get('pattern_compliance_score', 0.0):.2f}\n\n"
            
            matched_patterns = patterns_analysis.get("matched_patterns", [])
            if matched_patterns:
                prompt += "Matched Patterns:\n"
                for pattern in matched_patterns:
                    prompt += f"""- {pattern.file_path}
                  {f"Line: {pattern.line_number}" if pattern.line_number else ""}
                  Category: {pattern.category}
                  
                  ```
                  {pattern.code_snippet if pattern.code_snippet else "No code snippet available"}
                  ```
                """
            
            unmatched_patterns = patterns_analysis.get("unmatched_patterns", [])
            if unmatched_patterns:
                prompt += "Unmatched Patterns:\n"
                for pattern in unmatched_patterns:
                    prompt += f"""- {pattern.file_path}
                  {f"Line: {pattern.line_number}" if pattern.line_number else ""}
                  Category: {pattern.category}
                  
                  ```
                  {pattern.code_snippet if pattern.code_snippet else "No code snippet available"}
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
    
    def _auto_merge_pr(self, repo: Repository, pr: PullRequest, review_result: Dict[str, Any]) -> None:
        """Automatically merge a PR if it meets all requirements."""
        try:
            # Check if PR is mergeable
            if not pr.mergeable:
                logger.warning(f"PR #{pr.number} is not mergeable")
                return
            
            # Check if PR has been approved
            if review_result.get("approval_recommendation") != "approve":
                logger.warning(f"PR #{pr.number} has not been approved")
                return
            
            # Merge the PR
            merge_message = f"Auto-merged PR #{pr.number}: {pr.title}\n\nThis PR was automatically merged because it met all requirements."
            pr.merge(
                commit_title=f"Auto-merge PR #{pr.number}: {pr.title}",
                commit_message=merge_message,
                merge_method="merge"
            )
            
            logger.info(f"Auto-merged PR #{pr.number}")
            
            # Send notification to Slack
            if self.slack_token and self.slack_channel_id:
                from slack_sdk import WebClient
                
                try:
                    slack_client = WebClient(token=self.slack_token)
                    
                    message = f":rocket: *Auto-merged PR #{pr.number} in {repo.full_name}*\n\n"
                    message += f"*Title:* {pr.title}\n"
                    message += f"*Description:* {pr.body or 'No description provided'}\n\n"
                    message += "This PR was automatically merged because it met all requirements."
                    
                    slack_client.chat_postMessage(
                        channel=self.slack_channel_id,
                        text=message
                    )
                    
                    logger.info(f"Sent auto-merge notification to Slack channel {self.slack_channel_id}")
                
                except Exception as e:
                    logger.error(f"Error sending auto-merge notification: {e}")
        
        except Exception as e:
            logger.error(f"Error auto-merging PR: {e}")
            logger.error(traceback.format_exc())
