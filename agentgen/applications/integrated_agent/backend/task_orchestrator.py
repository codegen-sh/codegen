"""
Task orchestrator for the integrated agent application.

This module coordinates the workflow between requirements and PR reviews.
"""

import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Union, Any

from .database import JSONDatabase
from .models import Requirement, RequirementStatus, PRReview, SlackMessage
from .slack_integration import SlackIntegration

logger = logging.getLogger(__name__)

class TaskOrchestrator:
    """Task orchestrator for the integrated agent application."""

    def __init__(
        self, 
        db: JSONDatabase, 
        slack_integration: Optional[SlackIntegration] = None,
        channel_id: Optional[str] = None
    ):
        """Initialize the task orchestrator.
        
        Args:
            db: Database instance
            slack_integration: Slack integration instance
            channel_id: Default Slack channel ID
        """
        self.db = db
        self.slack_integration = slack_integration
        self.channel_id = channel_id or os.environ.get("SLACK_CHANNEL")
        self.running = False
    
    def start(self):
        """Start the task orchestrator."""
        self.running = True
        logger.info("Task orchestrator started")
    
    def stop(self):
        """Stop the task orchestrator."""
        self.running = False
        logger.info("Task orchestrator stopped")
    
    def is_running(self) -> bool:
        """Check if the task orchestrator is running."""
        return self.running
    
    def send_next_requirement(self) -> Optional[Requirement]:
        """Send the next requirement to Slack.
        
        Returns:
            Requirement: The requirement that was sent, or None if no requirement was sent
        """
        if not self.running:
            logger.warning("Task orchestrator is not running")
            return None
        
        if not self.slack_integration:
            logger.error("Slack integration not available")
            return None
        
        # Get the next requirement to send
        requirements = self.db.list_requirements()
        not_started_requirements = [r for r in requirements if r.status == RequirementStatus.NOT_STARTED]
        
        if not not_started_requirements:
            logger.info("No requirements to send")
            return None
        
        # Sort by creation date (oldest first)
        not_started_requirements.sort(key=lambda r: r.created_at)
        
        # Get the next requirement
        requirement = not_started_requirements[0]
        
        # Update the requirement status
        requirement.status = RequirementStatus.IN_PROGRESS
        requirement.updated_at = datetime.now()
        self.db.update_requirement(requirement)
        
        # Send the requirement to Slack
        try:
            message = self.slack_integration.send_requirement(requirement, channel=self.channel_id)
            
            # Store the message in the database
            self.db.create_slack_message(message)
            
            logger.info(f"Requirement {requirement.id} sent to Slack")
            return requirement
        
        except Exception as e:
            logger.error(f"Error sending requirement {requirement.id} to Slack: {e}")
            
            # Revert the requirement status
            requirement.status = RequirementStatus.NOT_STARTED
            requirement.updated_at = datetime.now()
            self.db.update_requirement(requirement)
            
            return None
    
    def process_pr_review(self, pr_review: PRReview) -> bool:
        """Process a PR review.
        
        Args:
            pr_review: PR review to process
            
        Returns:
            bool: True if the PR review was processed successfully, False otherwise
        """
        if not self.running:
            logger.warning("Task orchestrator is not running")
            return False
        
        if not self.slack_integration:
            logger.error("Slack integration not available")
            return False
        
        # Get the requirements met by this PR
        requirements_met = []
        for requirement_id in pr_review.requirements_met:
            requirement = self.db.get_requirement(requirement_id)
            if requirement:
                requirements_met.append(requirement)
        
        # Update the requirements
        for requirement in requirements_met:
            requirement.status = RequirementStatus.COMPLETED
            requirement.assigned_pr = pr_review.pr_number
            requirement.updated_at = datetime.now()
            self.db.update_requirement(requirement)
        
        # Send the PR review notification to Slack
        try:
            message = self.slack_integration.send_pr_review_notification(pr_review, channel=self.channel_id)
            
            # Store the message in the database
            self.db.create_slack_message(message)
            
            logger.info(f"PR review for PR #{pr_review.pr_number} sent to Slack")
            
            # If the PR meets all requirements, send the next requirement
            if pr_review.requirements_not_met:
                logger.info(f"PR #{pr_review.pr_number} does not meet all requirements")
                return True
            
            # Wait a bit before sending the next requirement
            time.sleep(5)
            
            # Send the next requirement
            next_requirement = self.send_next_requirement()
            if next_requirement:
                logger.info(f"Next requirement {next_requirement.id} sent to Slack")
            else:
                logger.info("No more requirements to send")
            
            return True
        
        except Exception as e:
            logger.error(f"Error sending PR review for PR #{pr_review.pr_number} to Slack: {e}")
            return False
    
    def run_once(self) -> bool:
        """Run the task orchestrator once.
        
        Returns:
            bool: True if the task orchestrator is running, False otherwise
        """
        if not self.running:
            logger.warning("Task orchestrator is not running")
            return False
        
        # Check if there are any requirements in progress
        requirements = self.db.list_requirements()
        in_progress_requirements = [r for r in requirements if r.status == RequirementStatus.IN_PROGRESS]
        
        if not in_progress_requirements:
            # Send the next requirement
            next_requirement = self.send_next_requirement()
            if next_requirement:
                logger.info(f"Next requirement {next_requirement.id} sent to Slack")
            else:
                logger.info("No more requirements to send")
        
        return True
