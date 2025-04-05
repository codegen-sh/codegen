"""
Project planning and management module for PR Code Review agent.
"""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import markdown
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class Step(BaseModel):
    """A step in a project plan."""
    
    id: str
    description: str
    order: int
    status: str = "pending"  # pending, in_progress, completed, failed
    assigned_pr: Optional[int] = None
    implementation_details: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class Requirement(BaseModel):
    """A requirement for a project."""
    
    id: str
    description: str
    section: str
    source: str
    status: str = "pending"  # pending, in_progress, completed, failed
    assigned_pr: Optional[int] = None
    implementation_details: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class ProjectPlan(BaseModel):
    """A project plan with steps and requirements."""
    
    title: str
    description: str
    steps: List[Step] = Field(default_factory=list)
    requirements: List[Requirement] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class PlanManager:
    """Manager for project plans and requirements."""
    
    def __init__(
        self,
        output_dir: str,
        anthropic_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
    ):
        """Initialize the plan manager."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.anthropic_api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY", "")
        
        # Initialize state files
        self.plans_file = self.output_dir / "plans.json"
        self.current_plan_file = self.output_dir / "current_plan.json"
        self.progress_file = self.output_dir / "progress.md"
    
    def create_plan_from_markdown(self, markdown_content: str, title: str, description: str) -> ProjectPlan:
        """Create a project plan from markdown content."""
        # Parse markdown to extract steps and requirements
        steps = self._extract_steps_from_markdown(markdown_content)
        requirements = self._extract_requirements_from_markdown(markdown_content)
        
        # Create the project plan
        plan = ProjectPlan(
            title=title,
            description=description,
            steps=steps,
            requirements=requirements,
        )
        
        # Save the plan
        self._save_plan(plan)
        
        return plan
    
    def _extract_steps_from_markdown(self, markdown_content: str) -> List[Step]:
        """Extract steps from markdown content."""
        # Convert markdown to HTML
        html = markdown.markdown(markdown_content)
        
        # Use BeautifulSoup to parse HTML
        soup = BeautifulSoup(html, "html.parser")
        
        steps = []
        step_id = 1
        
        # Look for ordered lists (ol) and list items (li)
        for ol in soup.find_all("ol"):
            for li in ol.find_all("li"):
                step_text = li.get_text().strip()
                if step_text:
                    steps.append(
                        Step(
                            id=f"step-{step_id}",
                            description=step_text,
                            order=step_id,
                        )
                    )
                    step_id += 1
        
        # Also look for headers followed by paragraphs
        for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            header_text = h.get_text().strip()
            if "step" in header_text.lower():
                # Get the next paragraph
                next_p = h.find_next("p")
                if next_p:
                    step_text = next_p.get_text().strip()
                    steps.append(
                        Step(
                            id=f"step-{step_id}",
                            description=step_text,
                            order=step_id,
                        )
                    )
                    step_id += 1
        
        return steps
    
    def _extract_requirements_from_markdown(self, markdown_content: str) -> List[Requirement]:
        """Extract requirements from markdown content."""
        # Convert markdown to HTML
        html = markdown.markdown(markdown_content)
        
        # Use BeautifulSoup to parse HTML
        soup = BeautifulSoup(html, "html.parser")
        
        requirements = []
        req_id = 1
        
        # Look for sections with "requirement" in the header
        for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            header_text = h.get_text().strip()
            section = header_text
            
            # If this is a requirements section, process it
            if "requirement" in header_text.lower():
                # Get all paragraphs and list items until the next header
                next_elem = h.next_sibling
                while next_elem and not next_elem.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                    if next_elem.name == "p":
                        req_text = next_elem.get_text().strip()
                        if req_text:
                            requirements.append(
                                Requirement(
                                    id=f"req-{req_id}",
                                    description=req_text,
                                    section=section,
                                    source="markdown",
                                )
                            )
                            req_id += 1
                    elif next_elem.name == "ul" or next_elem.name == "ol":
                        for li in next_elem.find_all("li"):
                            req_text = li.get_text().strip()
                            if req_text:
                                requirements.append(
                                    Requirement(
                                        id=f"req-{req_id}",
                                        description=req_text,
                                        section=section,
                                        source="markdown",
                                    )
                                )
                                req_id += 1
                    next_elem = next_elem.next_sibling
        
        # Also look for bullet points with requirement-like text
        for ul in soup.find_all("ul"):
            for li in ul.find_all("li"):
                li_text = li.get_text().strip()
                # Check if this looks like a requirement (contains "must", "should", etc.)
                if any(keyword in li_text.lower() for keyword in ["must", "should", "shall", "will", "required"]):
                    requirements.append(
                        Requirement(
                            id=f"req-{req_id}",
                            description=li_text,
                            section="Requirements",
                            source="markdown",
                        )
                    )
                    req_id += 1
        
        return requirements
    
    def _save_plan(self, plan: ProjectPlan) -> None:
        """Save a project plan to disk."""
        # Save as current plan
        with open(self.current_plan_file, "w", encoding="utf-8") as f:
            f.write(plan.model_dump_json(indent=2))
        
        # Add to plans list if it exists
        if self.plans_file.exists():
            with open(self.plans_file, "r", encoding="utf-8") as f:
                plans = json.load(f)
        else:
            plans = []
        
        # Add the new plan
        plans.append(json.loads(plan.model_dump_json()))
        
        # Save the plans list
        with open(self.plans_file, "w", encoding="utf-8") as f:
            json.dump(plans, f, indent=2)
    
    def load_current_plan(self) -> Optional[ProjectPlan]:
        """Load the current project plan."""
        if not self.current_plan_file.exists():
            return None
        
        with open(self.current_plan_file, "r", encoding="utf-8") as f:
            plan_data = json.load(f)
        
        return ProjectPlan.model_validate(plan_data)
    
    def get_next_step(self) -> Optional[Step]:
        """Get the next pending step in the current plan."""
        plan = self.load_current_plan()
        if not plan:
            return None
        
        # Find the first pending step
        for step in plan.steps:
            if step.status == "pending":
                return step
        
        return None
    
    def update_step_status(self, step_id: str, status: str, pr_number: Optional[int] = None, details: Optional[str] = None) -> None:
        """Update the status of a step in the current plan."""
        plan = self.load_current_plan()
        if not plan:
            return
        
        # Find and update the step
        for step in plan.steps:
            if step.id == step_id:
                step.status = status
                step.updated_at = datetime.now().isoformat()
                if pr_number:
                    step.assigned_pr = pr_number
                if details:
                    step.implementation_details = details
                break
        
        # Save the updated plan
        self._save_plan(plan)
    
    def update_requirement_status(self, req_id: str, status: str, pr_number: Optional[int] = None, details: Optional[str] = None) -> None:
        """Update the status of a requirement in the current plan."""
        plan = self.load_current_plan()
        if not plan:
            return
        
        # Find and update the requirement
        for req in plan.requirements:
            if req.id == req_id:
                req.status = status
                req.updated_at = datetime.now().isoformat()
                if pr_number:
                    req.assigned_pr = pr_number
                if details:
                    req.implementation_details = details
                break
        
        # Save the updated plan
        self._save_plan(plan)
    
    def generate_progress_report(self) -> str:
        """Generate a progress report for the current plan."""
        plan = self.load_current_plan()
        if not plan:
            return "No active plan found."
        
        # Calculate progress statistics
        total_steps = len(plan.steps)
        completed_steps = sum(1 for step in plan.steps if step.status == "completed")
        in_progress_steps = sum(1 for step in plan.steps if step.status == "in_progress")
        pending_steps = sum(1 for step in plan.steps if step.status == "pending")
        failed_steps = sum(1 for step in plan.steps if step.status == "failed")
        
        completion_percentage = (completed_steps / total_steps) * 100 if total_steps > 0 else 0
        
        # Generate the report
        report = f"# {plan.title} - Progress Report\n\n"
        report += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Add progress summary
        report += "## Progress Summary\n\n"
        report += f"- **Completion:** {completion_percentage:.1f}%\n"
        report += f"- **Total Steps:** {total_steps}\n"
        report += f"- **Completed:** {completed_steps}\n"
        report += f"- **In Progress:** {in_progress_steps}\n"
        report += f"- **Pending:** {pending_steps}\n"
        report += f"- **Failed:** {failed_steps}\n\n"
        
        # Add progress bar
        progress_bar_length = 30
        completed_chars = int((completion_percentage / 100) * progress_bar_length)
        report += "```\n["
        report += "=" * completed_chars
        report += " " * (progress_bar_length - completed_chars)
        report += f"] {completion_percentage:.1f}%\n```\n\n"
        
        # Add steps status
        report += "## Steps Status\n\n"
        report += "| Step | Status | PR |\n"
        report += "|------|--------|----|"
        
        for step in sorted(plan.steps, key=lambda s: s.order):
            status = step.status.replace("_", " ").title()
            pr_link = f"[#{step.assigned_pr}](https://github.com/PR/{step.assigned_pr})" if step.assigned_pr else "N/A"
            report += f"\n| {step.description} | {status} | {pr_link} |"
        
        # Add requirements status
        if plan.requirements:
            report += "\n\n## Requirements Status\n\n"
            report += "| Requirement | Status | PR |\n"
            report += "|------------|--------|----|"
            
            for req in plan.requirements:
                status = req.status.replace("_", " ").title()
                pr_link = f"[#{req.assigned_pr}](https://github.com/PR/{req.assigned_pr})" if req.assigned_pr else "N/A"
                report += f"\n| {req.description} | {status} | {pr_link} |"
        
        # Save the report
        with open(self.progress_file, "w", encoding="utf-8") as f:
            f.write(report)
        
        return report
