#!/usr/bin/env python3
"""
Requirements Tracker - A CI/CD application that tracks project requirements,
analyzes implementation progress, and coordinates with Codegen to complete tasks.
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

import dotenv
import github
import markdown
import requests
from bs4 import BeautifulSoup
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("requirements_tracker")

# Load environment variables
dotenv.load_dotenv()

# Constants
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
CODEGEN_USER_ID = os.getenv("CODEGEN_USER_ID")


class RequirementsParser:
    """Parse requirements from Markdown documents."""

    def __init__(self, docs_path: str):
        """Initialize the parser with the path to the documents."""
        self.docs_path = Path(docs_path)
        if not self.docs_path.exists():
            raise FileNotFoundError(f"Documents path not found: {docs_path}")

    def parse_markdown_file(self, file_path: Path) -> Dict:
        """Parse a Markdown file and extract requirements."""
        with open(file_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        # Convert Markdown to HTML
        html_content = markdown.markdown(md_content)
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract headings and content
        requirements = {
            "title": soup.find("h1").text if soup.find("h1") else file_path.stem,
            "sections": [],
        }

        current_section = None
        current_content = []

        for element in soup.find_all(["h2", "h3", "p", "ul", "ol"]):
            if element.name == "h2":
                if current_section:
                    requirements["sections"].append(
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
            requirements["sections"].append(
                {"title": current_section, "content": "".join(current_content)}
            )

        return requirements

    def extract_tasks(self, requirements: Dict) -> List[Dict]:
        """Extract tasks from requirements."""
        tasks = []
        for section in requirements["sections"]:
            section_title = section["title"]
            content_soup = BeautifulSoup(section["content"], "html.parser")

            # Extract tasks from lists
            for list_item in content_soup.find_all("li"):
                task_text = list_item.text.strip()
                if task_text:
                    tasks.append(
                        {
                            "section": section_title,
                            "description": task_text,
                            "completed": False,
                        }
                    )

            # Extract tasks from paragraphs that look like requirements
            for paragraph in content_soup.find_all("p"):
                text = paragraph.text.strip()
                if re.search(r"(must|should|shall|will|needs to|required to)", text, re.IGNORECASE):
                    tasks.append(
                        {
                            "section": section_title,
                            "description": text,
                            "completed": False,
                        }
                    )

        return tasks

    def parse_all_documents(self) -> List[Dict]:
        """Parse all Markdown documents in the docs path."""
        all_tasks = []
        for file_path in self.docs_path.glob("*.md"):
            try:
                requirements = self.parse_markdown_file(file_path)
                tasks = self.extract_tasks(requirements)
                for task in tasks:
                    task["source"] = file_path.name
                all_tasks.extend(tasks)
            except Exception as e:
                logger.error(f"Error parsing {file_path}: {e}")

        return all_tasks


class RepositoryAnalyzer:
    """Analyze a GitHub repository to track implementation progress."""

    def __init__(self, repo_name: str):
        """Initialize the analyzer with the repository name."""
        self.repo_name = repo_name
        self.github_client = github.Github(GITHUB_TOKEN)
        self.repo = self.github_client.get_repo(repo_name)

    def get_file_list(self) -> List[str]:
        """Get a list of all files in the repository."""
        contents = self.repo.get_contents("")
        file_list = []

        while contents:
            file_content = contents.pop(0)
            if file_content.type == "dir":
                contents.extend(self.repo.get_contents(file_content.path))
            else:
                file_list.append(file_content.path)

        return file_list

    def search_code(self, query: str) -> List[github.ContentFile.ContentFile]:
        """Search for code in the repository."""
        return list(self.github_client.search_code(f"{query} repo:{self.repo_name}"))

    def check_task_implementation(self, task: Dict) -> bool:
        """Check if a task has been implemented in the repository."""
        # Extract key terms from the task description
        description = task["description"].lower()
        terms = re.findall(r"\b\w{4,}\b", description)
        
        # Filter out common words
        common_words = {"must", "should", "shall", "will", "needs", "required", "have", "that", "this", "with", "from"}
        terms = [term for term in terms if term not in common_words]
        
        # Search for each term in the repository
        for term in terms:
            try:
                results = self.search_code(term)
                if results:
                    return True
            except github.GithubException as e:
                logger.warning(f"Error searching for '{term}': {e}")
        
        return False

    def analyze_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """Analyze tasks to determine if they have been implemented."""
        for task in tasks:
            task["completed"] = self.check_task_implementation(task)
        
        return tasks


class SlackIntegration:
    """Integrate with Slack to communicate with Codegen."""

    def __init__(self, channel_id: str):
        """Initialize the Slack integration with the channel ID."""
        self.channel_id = channel_id
        self.client = WebClient(token=SLACK_BOT_TOKEN)
        self.codegen_user_id = CODEGEN_USER_ID

    def send_message(self, message: str) -> Dict:
        """Send a message to the Slack channel."""
        try:
            response = self.client.chat_postMessage(
                channel=self.channel_id,
                text=message,
            )
            return response
        except SlackApiError as e:
            logger.error(f"Error sending message: {e}")
            return {"ok": False, "error": str(e)}

    def send_task_request(self, task: Dict) -> Dict:
        """Send a task request to Codegen."""
        message = f"<@{self.codegen_user_id}> I need help implementing the following task:\n\n"
        message += f"*Task*: {task['description']}\n"
        message += f"*Section*: {task['section']}\n"
        message += f"*Source*: {task['source']}\n\n"
        message += "Please provide a step-by-step implementation plan for this task."

        return self.send_message(message)

    def get_messages(self, timestamp: Optional[str] = None) -> List[Dict]:
        """Get messages from the Slack channel."""
        try:
            response = self.client.conversations_history(
                channel=self.channel_id,
                oldest=timestamp,
            )
            return response["messages"]
        except SlackApiError as e:
            logger.error(f"Error getting messages: {e}")
            return []

    def parse_codegen_response(self, messages: List[Dict]) -> List[Dict]:
        """Parse Codegen responses from messages."""
        responses = []
        for message in messages:
            if message.get("user") == self.codegen_user_id:
                responses.append(
                    {
                        "text": message.get("text", ""),
                        "timestamp": message.get("ts", ""),
                    }
                )
        return responses


class ProgressTracker:
    """Track progress of tasks and generate reports."""

    def __init__(self, output_dir: str):
        """Initialize the progress tracker with the output directory."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.tasks_file = self.output_dir / "tasks.json"
        self.progress_file = self.output_dir / "progress.md"

    def save_tasks(self, tasks: List[Dict]) -> None:
        """Save tasks to a JSON file."""
        with open(self.tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2)

    def load_tasks(self) -> List[Dict]:
        """Load tasks from a JSON file."""
        if not self.tasks_file.exists():
            return []
        
        with open(self.tasks_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def update_task_status(self, task_index: int, completed: bool) -> None:
        """Update the status of a task."""
        tasks = self.load_tasks()
        if 0 <= task_index < len(tasks):
            tasks[task_index]["completed"] = completed
            self.save_tasks(tasks)

    def generate_progress_report(self, tasks: List[Dict]) -> str:
        """Generate a progress report in Markdown format."""
        report = "# Project Progress Report\n\n"
        report += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Calculate overall progress
        total_tasks = len(tasks)
        completed_tasks = sum(1 for task in tasks if task["completed"])
        progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        report += f"## Overall Progress: {progress_percentage:.1f}%\n\n"
        report += f"- Completed: {completed_tasks}/{total_tasks} tasks\n\n"
        
        # Group tasks by section
        sections = {}
        for task in tasks:
            section = task["section"]
            if section not in sections:
                sections[section] = []
            sections[section].append(task)
        
        # Generate report for each section
        for section, section_tasks in sections.items():
            report += f"## {section}\n\n"
            
            for task in section_tasks:
                status = "[X]" if task["completed"] else "[ ]"
                report += f"- {status} {task['description']} _(Source: {task['source']})_\n"
            
            report += "\n"
        
        return report

    def save_progress_report(self, tasks: List[Dict]) -> None:
        """Save the progress report to a Markdown file."""
        report = self.generate_progress_report(tasks)
        with open(self.progress_file, "w", encoding="utf-8") as f:
            f.write(report)


class RequirementsTracker:
    """Main application class for Requirements Tracker."""

    def __init__(
        self,
        repo_name: str,
        docs_path: str,
        output_dir: str,
        slack_channel: Optional[str] = None,
        interval: int = 60,
    ):
        """Initialize the Requirements Tracker."""
        self.repo_name = repo_name
        self.docs_path = docs_path
        self.output_dir = output_dir
        self.slack_channel = slack_channel
        self.interval = interval
        
        self.parser = RequirementsParser(docs_path)
        self.analyzer = RepositoryAnalyzer(repo_name)
        self.progress_tracker = ProgressTracker(output_dir)
        
        if slack_channel:
            self.slack = SlackIntegration(slack_channel)
        else:
            self.slack = None

    def run_once(self) -> None:
        """Run the tracker once."""
        logger.info("Parsing requirements documents...")
        tasks = self.parser.parse_all_documents()
        
        logger.info("Analyzing repository for implementation status...")
        tasks = self.analyzer.analyze_tasks(tasks)
        
        logger.info("Saving tasks and generating progress report...")
        self.progress_tracker.save_tasks(tasks)
        self.progress_tracker.save_progress_report(tasks)
        
        if self.slack:
            # Find incomplete tasks
            incomplete_tasks = [task for task in tasks if not task["completed"]]
            if incomplete_tasks:
                logger.info(f"Sending request for {len(incomplete_tasks)} incomplete tasks...")
                self.slack.send_task_request(incomplete_tasks[0])

    def run_continuously(self) -> None:
        """Run the tracker continuously."""
        while True:
            try:
                self.run_once()
                logger.info(f"Sleeping for {self.interval} minutes...")
                time.sleep(self.interval * 60)
            except KeyboardInterrupt:
                logger.info("Interrupted by user. Exiting...")
                break
            except Exception as e:
                logger.error(f"Error in tracker loop: {e}")
                time.sleep(60)  # Sleep for a minute before retrying


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="Requirements Tracker")
    parser.add_argument("--repo", required=True, help="GitHub repository (owner/repo)")
    parser.add_argument("--docs", required=True, help="Path to documents directory")
    parser.add_argument("--output", required=True, help="Path to output directory")
    parser.add_argument("--slack-channel", help="Slack channel ID")
    parser.add_argument(
        "--interval", type=int, default=60, help="Interval in minutes for periodic checks"
    )
    parser.add_argument(
        "--once", action="store_true", help="Run once and exit"
    )
    
    args = parser.parse_args()
    
    tracker = RequirementsTracker(
        repo_name=args.repo,
        docs_path=args.docs,
        output_dir=args.output,
        slack_channel=args.slack_channel,
        interval=args.interval,
    )
    
    if args.once:
        tracker.run_once()
    else:
        tracker.run_continuously()


if __name__ == "__main__":
    main()