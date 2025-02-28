from codegen.agents.code_agent import CodeAgent
from codegen.extensions.events.codegen_app import CodegenApp
from codegen.extensions.linear.types import LinearEvent
from codegen.extensions.slack.types import SlackEvent
from codegen.extensions.events.modal.base import CodebaseEventsApp, EventRouterMixin
from codegen.extensions.github.types.pull_request import PullRequestLabeledEvent
from pr_tasks import lint_for_dev_import_violations, review_with_codegen_agent
from typing import Literal
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from classy_fastapi import Routable, post
import modal
import logging

load_dotenv(".env")


logging.basicConfig(level=logging.INFO, force=True)
logger = logging.getLogger(__name__)

codegen_events_app = modal.App("codegen-events-router")

SNAPSHOT_DICT_ID = "codegen-events-codebase-snapshots"


REPO_URL = "https://github.com/codegen-sh/codegen-sdk.git"
COMMIT_ID = "f398107d31bbd53fc77bc9c5f8763d2dc8fcae5b"

# Create the base image with dependencies
base_image = (
    modal.Image.debian_slim(python_version="3.13")
    .apt_install("git")
    .pip_install(
        # =====[ Codegen ]=====
        # "codegen",
        f"git+{REPO_URL}@{COMMIT_ID}",
        # =====[ Rest ]=====
        "openai>=1.1.0",
        "fastapi[standard]",
        "slack_sdk",
        "classy-fastapi>=0.6.1",
    )
)


event_handlers_app = modal.App("codegen-event-handlers")


@event_handlers_app.cls(image=base_image, secrets=[modal.Secret.from_dotenv(".env")], enable_memory_snapshot=True, container_idle_timeout=300)
class CustomEventHandlersAPI(CodebaseEventsApp):
    commit: str = modal.parameter(default="79114f67ccfe8700416cd541d1c7c43659a95342")
    repo_org: str = modal.parameter(default="codegen-sh")
    repo_name: str = modal.parameter(default="Kevin-s-Adventure-Game")
    snapshot_index_id: str = SNAPSHOT_DICT_ID

    def setup_handlers(self, cg: CodegenApp):
        @cg.slack.event("app_mention")
        async def handle_mention(event: SlackEvent):
            logger.info("[APP_MENTION] Received cg_app_mention event")

            # Codebase
            logger.info("[CODEBASE] Initializing codebase")
            codebase = cg.get_codebase()

            # Code Agent
            logger.info("[CODE_AGENT] Initializing code agent")
            agent = CodeAgent(codebase=codebase)

            logger.info("[CODE_AGENT] Running code agent")
            response = agent.run(event.text)

            cg.slack.client.chat_postMessage(channel=event.channel, text=response, thread_ts=event.ts)

            return {"message": "Mentioned", "received_text": event.text, "response": response}

        @cg.github.event("pull_request:labeled")
        def handle_pr(event: PullRequestLabeledEvent):
            logger.info("PR labeled")
            logger.info(f"PR head sha: {event.pull_request.head.sha}")

            codebase = cg.get_codebase()
            logger.info(f"Codebase: {codebase.name} codebase.repo: {codebase.repo_path}")

            # =====[ Check out commit ]=====
            # Might require fetch?
            logger.info("> Checking out commit")
            codebase.checkout(commit=event.pull_request.head.sha)

            logger.info("> Running PR Lints")
            # LINT CODEMOD
            lint_for_dev_import_violations(codebase, event)

            # REVIEW CODEMOD
            review_with_codegen_agent(codebase, event)

            return {"message": "PR event handled", "num_files": len(codebase.files), "num_functions": len(codebase.functions)}

        @cg.linear.event("Issue")
        def handle_issue(event: LinearEvent):
            logger.info(f"Issue created: {event}")
            codebase = cg.get_codebase()
            return {"message": "Linear Issue event", "num_files": len(codebase.files), "num_functions": len(codebase.functions)}


@codegen_events_app.cls(image=base_image, secrets=[modal.Secret.from_dotenv(".env")])
class WebhookEventRouterAPI(EventRouterMixin, Routable):
    snapshot_index_id: str = SNAPSHOT_DICT_ID

    def get_event_handler_cls(self):
        modal_cls = modal.Cls.from_name(app_name="Events", name="CustomEventHandlersAPI")
        return modal_cls

    @post("/{org}/{repo}/{provider}/events")
    async def handle_event(self, org: str, repo: str, provider: Literal["slack", "github", "linear"], request: Request):
        # Define the route for the webhook url sink, it will need to indicate the repo repo org, and the provider
        return await super().handle_event(org, repo, provider, request)

    @modal.asgi_app()
    def api(self):
        """Run the FastAPI app with the Router."""
        event_api = FastAPI()
        route_view = WebhookEventRouterAPI()
        event_api.include_router(route_view.router)
        return event_api


# Setup a cron job to trigger updates to the codebase snapshots.
@codegen_events_app.function(schedule=modal.Cron("*/10 * * * *"), image=base_image, secrets=[modal.Secret.from_dotenv(".env")])
def refresh_repository_snapshots():
    WebhookEventRouterAPI().refresh_repository_snapshots(snapshot_index_id=SNAPSHOT_DICT_ID)


app = modal.App("Events", secrets=[modal.Secret.from_dotenv(".env")])
app.include(event_handlers_app)
app.include(codegen_events_app)
