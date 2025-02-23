from codegen import Codebase, CodeAgent
from codegen.extensions.clients.linear import LinearClient
from codegen.extensions.events.app import CodegenApp
from codegen.extensions.tools.github.create_pr import create_pr
from codegen.shared.enums.programming_language import ProgrammingLanguage
from helpers import create_codebase, format_linear_message, has_codegen_label, process_update_event

from fastapi import Request

import os
import modal
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

image = modal.Image.debian_slim(python_version="3.13").apt_install("git").pip_install("fastapi[standard]", "codegen>=v0.26.3")

app = CodegenApp("linear-bot", image=image, modal_api_key="")


@app.cls(secrets=[modal.Secret.from_dotenv()], keep_warm=1)
class LinearApp:
    codebase: Codebase

    @modal.enter()
    def run_this_on_container_startup(self):
        self.codebase = create_codebase("codegen-sh/codegen-sdk", ProgrammingLanguage.PYTHON)

        # Subscribe web endpoints as linear webhook callbacks
        app.linear.subscribe_all_handlers()

    @modal.exit()
    def run_this_on_container_exit(self):
        app.linear.unsubscribe_all_handlers()

    @modal.web_endpoint(method="POST")
    @app.linear.event("Issue", should_handle=has_codegen_label)
    def handle_webhook(self, data: dict, request: Request):
        """"Handle incoming webhook events from Linear""" ""
        linear_client = LinearClient(access_token=os.environ["LINEAR_ACCESS_TOKEN"])

        event = process_update_event(data)
        linear_client.comment_on_issue(event.issue_id, "I'm on it 👍")

        query = format_linear_message(event.title, event.description)
        agent = CodeAgent(self.codebase)

        agent.run(query)

        pr_title = f"[{event.identifier}] " + event.title
        pr_body = "Codegen generated PR for issue: " + event.issue_url
        create_pr_result = create_pr(self.codebase, pr_title, pr_body)

        logger.info(f"PR created: {create_pr_result.model_dump_json()}")

        linear_client.comment_on_issue(event.issue_id, f"I've finished running, please review the PR: {create_pr_result.url}")
        self.codebase.reset()

        return {"status": "success"}
