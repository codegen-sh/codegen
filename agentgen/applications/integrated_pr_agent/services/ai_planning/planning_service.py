"""
AI Planning Service for project planning and visualization.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import anthropic
import openai
from pydantic import BaseModel

logger = logging.getLogger("integrated_pr_agent")


class ProjectPlan(BaseModel):
    """Project plan model."""
    
    title: str
    description: str
    components: List[Dict[str, Any]]
    structure: Dict[str, Any]
    timeline: Optional[Dict[str, Any]] = None
    created_at: str


class AIPlanningService:
    """Service for AI-assisted project planning and visualization."""
    
    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        output_dir: Optional[str] = None,
    ):
        """Initialize the AI planning service."""
        self.anthropic_api_key = anthropic_api_key
        self.openai_api_key = openai_api_key
        self.output_dir = Path(output_dir) if output_dir else None
        
        # Initialize clients
        if self.anthropic_api_key:
            self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_api_key)
        else:
            self.anthropic_client = None
        
        if self.openai_api_key:
            self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
        else:
            self.openai_client = None
    
    def generate_project_plan(
        self,
        repo_url: str,
        requirements: List[Dict[str, Any]],
        context_docs: Optional[List[Dict[str, Any]]] = None,
    ) -> ProjectPlan:
        """
        Generate a project plan based on requirements and context documents.
        
        Args:
            repo_url: GitHub repository URL
            requirements: List of requirement objects
            context_docs: Optional list of context documents
            
        Returns:
            ProjectPlan object
        """
        from datetime import datetime
        
        # Format requirements for the prompt
        formatted_requirements = "\n".join([
            f"- {req['description']}" for req in requirements
        ])
        
        # Format context documents if available
        formatted_context = ""
        if context_docs:
            formatted_context = "\n\n## Context Documents\n\n"
            for doc in context_docs:
                formatted_context += f"### {doc['title']}\n{doc['content']}\n\n"
        
        # Create the prompt
        prompt = f"""
        # Project Planning Task
        
        You are an expert software architect and project planner. Your task is to create a detailed project plan for implementing the following requirements in the GitHub repository: {repo_url}
        
        ## Requirements
        
        {formatted_requirements}
        
        {formatted_context}
        
        ## Instructions
        
        Create a comprehensive project plan that includes:
        
        1. A high-level overview of the project
        2. Key components and their responsibilities
        3. Project structure (directories, files, etc.)
        4. Implementation timeline and milestones
        
        Format your response as a JSON object with the following structure:
        
        ```json
        {{
            "title": "Project title",
            "description": "High-level overview of the project",
            "components": [
                {{
                    "name": "Component name",
                    "description": "Component description",
                    "responsibilities": ["Responsibility 1", "Responsibility 2"]
                }}
            ],
            "structure": {{
                "directories": [
                    {{
                        "path": "path/to/directory",
                        "description": "Purpose of this directory",
                        "files": [
                            {{
                                "name": "filename.ext",
                                "description": "Purpose of this file",
                                "key_functions": ["Function 1", "Function 2"]
                            }}
                        ]
                    }}
                ]
            }},
            "timeline": {{
                "phases": [
                    {{
                        "name": "Phase 1",
                        "description": "Description of phase 1",
                        "tasks": ["Task 1", "Task 2"],
                        "estimated_duration": "X days"
                    }}
                ]
            }}
        }}
        ```
        
        Ensure your plan is realistic, well-structured, and follows best practices for software development.
        """
        
        # Generate the plan using the available LLM
        plan_json = self._generate_with_llm(prompt)
        
        try:
            plan_data = json.loads(plan_json)
            plan_data["created_at"] = datetime.now().isoformat()
            return ProjectPlan(**plan_data)
        except Exception as e:
            logger.error(f"Error parsing project plan: {e}")
            logger.error(f"Raw plan: {plan_json}")
            raise ValueError(f"Failed to generate valid project plan: {e}")
    
    def visualize_project_structure(self, plan: ProjectPlan) -> str:
        """
        Generate a visualization of the project structure.
        
        Args:
            plan: ProjectPlan object
            
        Returns:
            Markdown representation of the project structure
        """
        markdown = f"# {plan.title} - Project Structure\n\n"
        markdown += f"{plan.description}\n\n"
        
        # Add components section
        markdown += "## Components\n\n"
        for component in plan.components:
            markdown += f"### {component['name']}\n\n"
            markdown += f"{component['description']}\n\n"
            markdown += "**Responsibilities:**\n\n"
            for resp in component['responsibilities']:
                markdown += f"- {resp}\n"
            markdown += "\n"
        
        # Add directory structure
        markdown += "## Directory Structure\n\n"
        markdown += "```\n"
        
        # Helper function to recursively build directory tree
        def build_tree(directories, prefix=""):
            result = ""
            for i, directory in enumerate(directories):
                is_last = i == len(directories) - 1
                connector = "└── " if is_last else "├── "
                result += f"{prefix}{connector}{directory['path'].split('/')[-1]}/\n"
                
                if "files" in directory:
                    file_prefix = prefix + ("    " if is_last else "│   ")
                    for j, file in enumerate(directory["files"]):
                        file_is_last = j == len(directory["files"]) - 1
                        file_connector = "└── " if file_is_last else "├── "
                        result += f"{file_prefix}{file_connector}{file['name']}\n"
                
                if "subdirectories" in directory:
                    subdir_prefix = prefix + ("    " if is_last else "│   ")
                    result += build_tree(directory["subdirectories"], subdir_prefix)
            
            return result
        
        # Build the tree
        if "directories" in plan.structure:
            markdown += build_tree(plan.structure["directories"])
        
        markdown += "```\n\n"
        
        # Add timeline if available
        if plan.timeline:
            markdown += "## Implementation Timeline\n\n"
            for phase in plan.timeline["phases"]:
                markdown += f"### {phase['name']}\n\n"
                markdown += f"{phase['description']}\n\n"
                markdown += "**Tasks:**\n\n"
                for task in phase["tasks"]:
                    markdown += f"- {task}\n"
                markdown += f"\n**Estimated Duration:** {phase['estimated_duration']}\n\n"
        
        return markdown
    
    def generate_progress_document(
        self,
        plan: ProjectPlan,
        requirements: List[Dict[str, Any]],
        prs: List[Dict[str, Any]],
    ) -> str:
        """
        Generate a progress tracking document.
        
        Args:
            plan: ProjectPlan object
            requirements: List of requirement objects
            prs: List of pull request objects
            
        Returns:
            Markdown representation of the progress
        """
        from datetime import datetime
        
        # Calculate progress statistics
        total_reqs = len(requirements)
        completed_reqs = sum(1 for req in requirements if req["status"] == "completed")
        in_progress_reqs = sum(1 for req in requirements if req["status"] == "in_progress")
        pending_reqs = sum(1 for req in requirements if req["status"] == "pending")
        
        completion_percentage = (completed_reqs / total_reqs) * 100 if total_reqs > 0 else 0
        
        # Generate the document
        markdown = f"# {plan.title} - Progress Report\n\n"
        markdown += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Add progress summary
        markdown += "## Progress Summary\n\n"
        markdown += f"- **Completion:** {completion_percentage:.1f}%\n"
        markdown += f"- **Total Requirements:** {total_reqs}\n"
        markdown += f"- **Completed:** {completed_reqs}\n"
        markdown += f"- **In Progress:** {in_progress_reqs}\n"
        markdown += f"- **Pending:** {pending_reqs}\n\n"
        
        # Add progress bar
        progress_bar_length = 30
        completed_chars = int((completion_percentage / 100) * progress_bar_length)
        markdown += "```\n["
        markdown += "=" * completed_chars
        markdown += " " * (progress_bar_length - completed_chars)
        markdown += f"] {completion_percentage:.1f}%\n```\n\n"
        
        # Add requirements status
        markdown += "## Requirements Status\n\n"
        markdown += "| Requirement | Status | PR |\n"
        markdown += "|------------|--------|----|\n"
        
        for req in requirements:
            status = req["status"].replace("_", " ").title()
            pr_link = f"[#{req['assigned_pr']}](https://github.com/PR/{req['assigned_pr']})" if req.get("assigned_pr") else "N/A"
            markdown += f"| {req['description']} | {status} | {pr_link} |\n"
        
        # Add recent PRs
        if prs:
            markdown += "\n## Recent Pull Requests\n\n"
            markdown += "| PR | Title | Status | Created |\n"
            markdown += "|-------|-------|--------|--------|\n"
            
            # Sort PRs by created_at (newest first) and take the top 5
            sorted_prs = sorted(prs, key=lambda x: x.get("created_at", ""), reverse=True)[:5]
            
            for pr in sorted_prs:
                pr_link = f"[#{pr['number']}](https://github.com/PR/{pr['number']})"
                status = pr["status"].replace("_", " ").title()
                created_at = pr.get("created_at", "").split("T")[0]  # Just the date part
                markdown += f"| {pr_link} | {pr['title']} | {status} | {created_at} |\n"
        
        return markdown
    
    def save_project_plan(self, plan: ProjectPlan, filename: str) -> str:
        """
        Save the project plan to a file.
        
        Args:
            plan: ProjectPlan object
            filename: Name of the file to save
            
        Returns:
            Path to the saved file
        """
        if not self.output_dir:
            raise ValueError("Output directory not set")
        
        # Create the output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save the plan as JSON
        plan_path = self.output_dir / f"{filename}.json"
        with open(plan_path, "w", encoding="utf-8") as f:
            f.write(plan.json(indent=2))
        
        # Generate and save the visualization
        viz_path = self.output_dir / f"{filename}_structure.md"
        visualization = self.visualize_project_structure(plan)
        with open(viz_path, "w", encoding="utf-8") as f:
            f.write(visualization)
        
        return str(plan_path)
    
    def _generate_with_llm(self, prompt: str) -> str:
        """
        Generate text using the available LLM.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            Generated text
        """
        # Try with Anthropic first
        if self.anthropic_client:
            try:
                response = self.anthropic_client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=4000,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.content[0].text
            except Exception as e:
                logger.error(f"Error generating with Anthropic: {e}")
        
        # Fall back to OpenAI
        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[
                        {"role": "system", "content": "You are an expert software architect and project planner."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=4000
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"Error generating with OpenAI: {e}")
        
        raise ValueError("No LLM client available")