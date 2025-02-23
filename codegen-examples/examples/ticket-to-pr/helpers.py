from codegen import Codebase, ProgrammingLanguage
from typing import List, Dict, Any
from codegen.sdk.codebase.config import CodebaseConfig
from data import LinearLabels, LinearIssueUpdateEvent
import os
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_update_event(event_data: dict[str, Any]):
    print("processing update event")

    action = event_data.get("action")
    actor = event_data.get("actor")
    created_at = event_data.get("createdAt")
    issue_url = event_data.get("url")
    data: Dict[str, Any] = event_data.get("data")
    issue_id = data.get("id")
    title = data.get("title")
    description = data.get("description")
    identifier = data.get("identifier")

    labels: List[LinearLabels] = data.get("labels")
    updated_from: Dict[str, Any] = event_data.get("updatedFrom")

    update_event = LinearIssueUpdateEvent(
        issue_id=issue_id,
        action=action,
        actor=actor,
        created_at=created_at,
        issue_url=issue_url,
        data=data,
        labels=labels,
        updated_from=updated_from,
        title=title,
        description=description,
        identifier=identifier,
    )
    return update_event


def format_linear_message(title: str, description: str | None = "") -> str:
    """Format a Linear update event into a message for the agent"""

    return f"""
    Here is a new issue titled '{title}' and with the description '{description}'. Continue to respond to this query. Use your tools to query the codebase for more context.
    When applicable include references to files and line numbers, code snippets are also encouraged. Don't forget to create a pull request with your changes, use the appropriate tool to do so.
    """


def has_codegen_label(*args, **kwargs):
    body = kwargs.get("data")
    type = body.get("type")
    action = body.get("action")

    if type == "Issue" and action == "update":
        # handle issue update (label updates)
        update_event = process_update_event(body)

    has_codegen_label = any(label.name == "Codegen" for label in update_event.labels)
    codegen_label_id = next((label.id for label in update_event.labels if label.name == "Codegen"), None)
    had_codegen_label = codegen_label_id in update_event.updated_from.get("labels", []) if codegen_label_id else False
    previous_labels = update_event.updated_from.get("labelIds", None)

    if previous_labels is None or not has_codegen_label:
        logger.info("No labels updated, skipping codegen bot response")
        return False

    if has_codegen_label and not had_codegen_label:
        logger.info("Codegen label added, codegen bot will respond")
        return True

    logger.info("Codegen label removed or already existed, codegen bot will not respond")
    return False


def create_codebase(repo_name: str, language: ProgrammingLanguage):
    config = CodebaseConfig()
    config.secrets.github_token = os.environ["GITHUB_TOKEN"]

    return Codebase.from_repo(repo_name, language=language, tmp_dir="/root", config=config)
