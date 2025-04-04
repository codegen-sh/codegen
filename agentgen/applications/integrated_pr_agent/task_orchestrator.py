"""
Task Orchestrator for coordinating between requirements and PR reviews.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any

from .models import (
    Requirement, 
    RequirementList, 
    RequirementStatus,
    PullRequest, 
    PRList, 
    PRStatus, 
    PRReviewStatus
)
from .services import (
    GitHubService,
    RequirementsService,
    PRReviewService,
    SlackService
)

logger = logging.getLogger("integrated_pr_agent")


class TaskOrchestrator:
    """Orchestrator for coordinating between requirements and PR reviews."""
    
    def __init__(
        self,
        repo_name: str,
        docs_path: str,
        output_dir: str,
        slack_channel_id: Optional[str] = None,
        github_token: Optional[str] = None,
        slack_token: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
    ):
        """Initialize the task orchestrator."""
        self.repo_name = repo_name
        self.docs_path = docs_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize services
        self.github_service = GitHubService(github_token=github_token)
        self.requirements_service = RequirementsService(docs_path=docs_path)
        self.pr_review_service = PRReviewService(
            anthropic_api_key=anthropic_api_key,
            openai_api_key=openai_api_key,
        )
        
        if slack_channel_id and slack_token:
            self.slack_service = SlackService(
                slack_token=slack_token,
                channel_id=slack_channel_id,
            )
        else:
            self.slack_service = None
        
        # Initialize state
        self.requirements_file = self.output_dir / "requirements.json"
        self.prs_file = self.output_dir / "pull_requests.json"
        self.progress_file = self.output_dir / "progress.md"
        self.last_check_file = self.output_dir / "last_check.txt"
    
    def load_state(self) -> Tuple[RequirementList, PRList, Optional[str]]:
        """Load the current state."""
        # Load requirements
        if self.requirements_file.exists():
            requirements = self.requirements_service.load_requirements(str(self.requirements_file))
        else:
            requirements = RequirementList()
        
        # Load PRs
        if self.prs_file.exists():
            with open(self.prs_file, "r", encoding="utf-8") as f:
                prs = PRList.parse_raw(f.read())
        else:
            prs = PRList()
        
        # Load last check timestamp
        last_check = None
        if self.last_check_file.exists():
            with open(self.last_check_file, "r", encoding="utf-8") as f:
                last_check = f.read().strip()
        
        return requirements, prs, last_check
    
    def save_state(self, requirements: RequirementList, prs: PRList, last_check: Optional[str] = None) -> None:
        """Save the current state."""
        # Save requirements
        self.requirements_service.save_requirements(requirements, str(self.requirements_file))
        
        # Save PRs
        with open(self.prs_file, "w", encoding="utf-8") as f:
            f.write(prs.json(indent=2))
        
        # Save progress report
        self.requirements_service.save_progress_report(requirements, str(self.progress_file))
        
        # Save last check timestamp
        if last_check:
            with open(self.last_check_file, "w", encoding="utf-8") as f:
                f.write(last_check)
    
    def update_requirements(self) -> RequirementList:
        """Update requirements from documentation."""
        # Parse requirements from documentation
        requirements = self.requirements_service.parse_all_documents()
        
        # Load existing requirements to preserve status
        existing_requirements, _, _ = self.load_state()
        
        # Update status of new requirements based on existing ones
        for new_req in requirements.requirements:
            for existing_req in existing_requirements.requirements:
                if new_req.description == existing_req.description and new_req.section == existing_req.section:
                    new_req.status = existing_req.status
                    new_req.assigned_pr = existing_req.assigned_pr
                    new_req.implementation_details = existing_req.implementation_details
                    break
        
        return requirements
    
    def update_prs(self, prs: PRList) -> PRList:
        """Update PR status from GitHub."""
        updated_prs = PRList()
        
        # Get all PRs from GitHub
        github_prs = self.github_service.get_pull_requests(self.repo_name, state="all")
        
        # Update existing PRs
        for github_pr in github_prs:
            existing_pr = prs.get_pull_request_by_number(github_pr.number)
            
            if existing_pr:
                # Update status
                existing_pr.status = github_pr.status
                existing_pr.updated_at = github_pr.updated_at
                updated_prs.add_pull_request(existing_pr)
            else:
                # Add new PR
                updated_prs.add_pull_request(github_pr)
        
        return updated_prs
    
    def process_new_prs(self, requirements: RequirementList, prs: PRList) -> None:
        """Process new PRs and update requirements."""
        # Get open PRs
        open_prs = prs.get_open_pull_requests()
        
        for pr in open_prs:
            # Skip PRs that have already been reviewed
            if pr.review_status != PRReviewStatus.PENDING:
                continue
            
            # Get PR diff
            github_pr = self.github_service.get_pull_request(self.repo_name, pr.number)
            pr_diff = github_pr.diff()
            
            # Analyze PR against requirements
            review_result = self.pr_review_service.analyze_pr_against_requirements(pr, requirements, pr_diff)
            
            # Update PR with review result
            if review_result["compliant"]:
                pr.update_review_status(PRReviewStatus.APPROVED)
            else:
                pr.update_review_status(PRReviewStatus.CHANGES_REQUESTED)
            
            # Add suggestions to PR
            for suggestion in review_result.get("suggestions", []):
                if isinstance(suggestion, dict):
                    pr.add_suggestion(suggestion)
            
            # Post review comment on GitHub
            review_comment = self.pr_review_service.format_review_comment(review_result)
            self.github_service.create_pr_comment(self.repo_name, pr.number, review_comment)
            
            # Submit formal review
            review_event = self.pr_review_service.get_review_event(review_result)
            self.github_service.create_pr_review(
                self.repo_name, pr.number, review_comment, review_event
            )
            
            # Send review result to Slack if available
            if self.slack_service:
                self.slack_service.send_pr_review_result(pr.number, review_result)
            
            # Update requirement status if PR is approved and associated with a requirement
            if pr.requirement_id and review_result["compliant"]:
                requirement = requirements.get_requirement_by_id(pr.requirement_id)
                if requirement:
                    requirement.mark_completed()
    
    def send_next_requirement(self, requirements: RequirementList) -> None:
        """Send the next pending requirement to Codegen via Slack."""
        if not self.slack_service:
            logger.warning("Slack service not available, skipping sending requirement")
            return
        
        # Get pending requirements
        pending_reqs = requirements.get_pending_requirements()
        
        if not pending_reqs:
            logger.info("No pending requirements to send")
            return
        
        # Get the first pending requirement
        next_req = pending_reqs[0]
        
        # Send requirement to Codegen
        self.slack_service.send_requirement_request(next_req)
        
        # Mark requirement as in progress
        next_req.mark_in_progress()
        
        logger.info(f"Sent requirement '{next_req.description}' to Codegen")
    
    def check_for_completed_requirements(
        self, requirements: RequirementList, prs: PRList, last_check: Optional[str]
    ) -> str:
        """Check for completed requirements based on Slack messages."""
        if not self.slack_service:
            logger.warning("Slack service not available, skipping check for completed requirements")
            return last_check or datetime.now().isoformat()
        
        # Get messages since last check
        messages = self.slack_service.get_messages(last_check)
        
        # Parse Codegen responses
        responses = self.slack_service.parse_codegen_response(messages)
        
        # Check for PR links in responses
        for response in responses:
            # Look for PR links in the format "PR #123" or "pull request #123"
            import re
            pr_matches = re.findall(r"(?:PR|pull request) #(\d+)", response["text"], re.IGNORECASE)
            
            if pr_matches:
                pr_number = int(pr_matches[0])
                
                # Get the PR
                pr = prs.get_pull_request_by_number(pr_number)
                
                if not pr:
                    # Try to get it from GitHub
                    try:
                        github_pr = self.github_service.get_pull_request_model(self.repo_name, pr_number)
                        prs.add_pull_request(github_pr)
                        pr = github_pr
                    except Exception as e:
                        logger.error(f"Error getting PR #{pr_number}: {e}")
                        continue
                
                # Find in-progress requirements without assigned PRs
                in_progress_reqs = requirements.get_in_progress_requirements()
                
                for req in in_progress_reqs:
                    if not req.assigned_pr:
                        # Assign PR to requirement
                        req.assign_pr(pr_number)
                        
                        # Assign requirement to PR
                        pr.requirement_id = req.id
                        
                        logger.info(f"Assigned PR #{pr_number} to requirement '{req.description}'")
                        break
        
        # Return the timestamp of the latest message as the new last_check
        if responses:
            return responses[0]["timestamp"]
        else:
            return last_check or datetime.now().isoformat()
    
    def run_once(self) -> None:
        """Run the orchestrator once."""
        # Load state
        requirements, prs, last_check = self.load_state()
        
        # Update requirements from documentation
        requirements = self.update_requirements()
        
        # Update PRs from GitHub
        prs = self.update_prs(prs)
        
        # Process new PRs
        self.process_new_prs(requirements, prs)
        
        # Check for completed requirements
        last_check = self.check_for_completed_requirements(requirements, prs, last_check)
        
        # Send next requirement if no in-progress requirements
        if not requirements.get_in_progress_requirements():
            self.send_next_requirement(requirements)
        
        # Save state
        self.save_state(requirements, prs, last_check)
    
    def run_continuously(self, interval: int = 60) -> None:
        """Run the orchestrator continuously."""
        while True:
            try:
                logger.info("Running task orchestrator...")
                self.run_once()
                logger.info(f"Sleeping for {interval} seconds...")
                time.sleep(interval)
            except KeyboardInterrupt:
                logger.info("Interrupted by user. Exiting...")
                break
            except Exception as e:
                logger.error(f"Error in task orchestrator: {e}")
                logger.exception(e)
                time.sleep(10)  # Sleep for a shorter time on error