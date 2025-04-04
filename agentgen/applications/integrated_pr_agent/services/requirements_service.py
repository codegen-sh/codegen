"""
Requirements service for parsing and tracking requirements.
"""

import logging
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any

import markdown
from bs4 import BeautifulSoup

from ..models import Requirement, RequirementList, RequirementStatus

logger = logging.getLogger("integrated_pr_agent")


class RequirementsService:
    """Service for parsing and tracking requirements."""
    
    def __init__(self, docs_path: str):
        """Initialize the requirements service."""
        self.docs_path = Path(docs_path)
        if not self.docs_path.exists():
            raise FileNotFoundError(f"Documents path not found: {docs_path}")
    
    def parse_markdown_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse a Markdown file and extract requirements."""
        with open(file_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        # Convert Markdown to HTML
        html_content = markdown.markdown(md_content)
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract headings and content
        requirements_data = {
            "title": soup.find("h1").text if soup.find("h1") else file_path.stem,
            "sections": [],
        }

        current_section = None
        current_content = []

        for element in soup.find_all(["h2", "h3", "p", "ul", "ol"]):
            if element.name == "h2":
                if current_section:
                    requirements_data["sections"].append(
                        {"title": current_section, "content": "".join(current_content)}
                    )
                current_section = element.text
                current_content = []
            elif element.name == "h3":
                if current_section:
                    current_content.append(f"<h3>{element.text}</h3>")
            else:
                current_content.append(str(element))

        if current_section:
            requirements_data["sections"].append(
                {"title": current_section, "content": "".join(current_content)}
            )

        return requirements_data
    
    def extract_requirements(self, requirements_data: Dict[str, Any], source: str) -> List[Requirement]:
        """Extract requirements from parsed data."""
        requirements = []
        
        for section in requirements_data["sections"]:
            section_title = section["title"]
            content_soup = BeautifulSoup(section["content"], "html.parser")

            # Extract requirements from lists
            for list_item in content_soup.find_all("li"):
                task_text = list_item.text.strip()
                if task_text:
                    requirements.append(
                        Requirement(
                            id=str(uuid.uuid4()),
                            description=task_text,
                            section=section_title,
                            source=source,
                        )
                    )

            # Extract requirements from paragraphs that look like requirements
            for paragraph in content_soup.find_all("p"):
                text = paragraph.text.strip()
                if re.search(r"(must|should|shall|will|needs to|required to)", text, re.IGNORECASE):
                    requirements.append(
                        Requirement(
                            id=str(uuid.uuid4()),
                            description=text,
                            section=section_title,
                            source=source,
                        )
                    )
        
        return requirements
    
    def parse_all_documents(self) -> RequirementList:
        """Parse all Markdown documents in the docs path."""
        requirement_list = RequirementList()
        
        for file_path in self.docs_path.glob("*.md"):
            try:
                requirements_data = self.parse_markdown_file(file_path)
                requirements = self.extract_requirements(requirements_data, file_path.name)
                
                for requirement in requirements:
                    requirement_list.add_requirement(requirement)
            except Exception as e:
                logger.error(f"Error parsing {file_path}: {e}")
        
        return requirement_list
    
    def save_requirements(self, requirements: RequirementList, output_path: str) -> None:
        """Save requirements to a JSON file."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(requirements.json(indent=2))
    
    def load_requirements(self, input_path: str) -> RequirementList:
        """Load requirements from a JSON file."""
        input_file = Path(input_path)
        
        if not input_file.exists():
            return RequirementList()
        
        with open(input_file, "r", encoding="utf-8") as f:
            return RequirementList.parse_raw(f.read())
    
    def generate_progress_report(self, requirements: RequirementList) -> str:
        """Generate a progress report in Markdown format."""
        report = "# Project Requirements Progress Report\n\n"
        report += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Calculate overall progress
        total_reqs = len(requirements.requirements)
        completed_reqs = len(requirements.get_completed_requirements())
        in_progress_reqs = len(requirements.get_in_progress_requirements())
        pending_reqs = len(requirements.get_pending_requirements())
        failed_reqs = len(requirements.get_failed_requirements())
        
        progress_percentage = (completed_reqs / total_reqs * 100) if total_reqs > 0 else 0
        
        report += f"## Overall Progress: {progress_percentage:.1f}%\n\n"
        report += f"- Total: {total_reqs} requirements\n"
        report += f"- Completed: {completed_reqs} requirements\n"
        report += f"- In Progress: {in_progress_reqs} requirements\n"
        report += f"- Pending: {pending_reqs} requirements\n"
        report += f"- Failed: {failed_reqs} requirements\n\n"
        
        # Group requirements by section
        sections = {}
        for req in requirements.requirements:
            section = req.section
            if section not in sections:
                sections[section] = []
            sections[section].append(req)
        
        # Generate report for each section
        for section, section_reqs in sections.items():
            report += f"## {section}\n\n"
            
            for req in section_reqs:
                status_marker = {
                    RequirementStatus.COMPLETED: "[✓]",
                    RequirementStatus.IN_PROGRESS: "[🔄]",
                    RequirementStatus.PENDING: "[ ]",
                    RequirementStatus.FAILED: "[✗]",
                }[req.status]
                
                pr_info = f" (PR #{req.assigned_pr})" if req.assigned_pr else ""
                
                report += f"- {status_marker} {req.description} _(Source: {req.source}){pr_info}_\n"
            
            report += "\n"
        
        return report
    
    def save_progress_report(self, requirements: RequirementList, output_path: str) -> None:
        """Save the progress report to a Markdown file."""
        report = self.generate_progress_report(requirements)
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report)