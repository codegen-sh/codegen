import logging
import os
from typing import Literal

import modal
from fastapi import Request

from codegen.extensions.events.codegen_app import CodegenApp
from codegen.extensions.events.modal.request_util import fastapi_request_adapter
from codegen.git.clients.git_repo_client import GitRepoClient
from codegen.git.schemas.repo_config import RepoConfig

logging.basicConfig(level=logging.INFO, force=True)
logger = logging.getLogger(__name__)

# refactor this to be a config
DEFAULT_SNAPSHOT_DICT_ID = "codegen-events-codebase-snapshots"


class EventRouterMixin:
    """This class is intended to be registered as a modal Class
    and will be used to route events to the correct handler.

    Usage:
    @codegen_events_app.cls(image=base_image, secrets=[modal.Secret.from_dotenv()])
    class CustomEventAPI(EventRouterMixin):
        pass

    """

    snapshot_index_id: str = DEFAULT_SNAPSHOT_DICT_ID

    def get_event_handler_cls(self) -> modal.Cls:
        """Lookup the Modal Class where the event handlers are defined"""
        msg = "Subclasses must implement this method"
        raise NotImplementedError(msg)

    async def handle_event(self, org: str, repo: str, provider: Literal["slack", "github", "linear"], request: Request):
        repo_config = RepoConfig(
            name=repo,
            full_name=f"{org}/{repo}",
        )

        repo_snapshotdict = modal.Dict.from_name(self.snapshot_index_id, {}, create_if_missing=True)

        last_snapshot_commit = repo_snapshotdict.get(f"{org}/{repo}", None)

        if last_snapshot_commit is None:
            git_client = GitRepoClient(repo_config=repo_config, access_token=os.environ["GITHUB_ACCESS_TOKEN"])
            branch = git_client.get_branch_safe(git_client.default_branch)
            last_snapshot_commit = branch.commit.sha if branch and branch.commit else None

        Klass = self.get_event_handler_cls()
        klass = Klass(repo_org=org, repo_name=repo, commit=last_snapshot_commit)

        request_payload = await request.json()
        request_headers = dict(request.headers)
        request_headers.pop("host", None)  # Remove host header if present

        if provider == "slack":
            return klass.proxy_event.remote(f"{org}/{repo}/slack/events", payload=request_payload, headers=request_headers)
        elif provider == "github":
            return klass.proxy_event.remote(f"{org}/{repo}/github/events", payload=request_payload, headers=request_headers)
        elif provider == "linear":
            return klass.proxy_event.remote(f"{org}/{repo}/linear/events", payload=request_payload, headers=request_headers)
        else:
            msg = f"Invalid provider: {provider}"
            raise ValueError(msg)

    def refresh_repository_snapshots(self, snapshot_index_id: str):
        """Refresh the latest snapshot for all repositories in the dictionary."""
        # Get all repositories from the modal.Dict
        repo_dict = modal.Dict.from_name(snapshot_index_id, {}, create_if_missing=True)

        for repo_full_name in repo_dict.keys():
            try:
                # Parse the repository full name to get org and repo
                org, repo = repo_full_name.split("/")

                # Create a RepoConfig for the repository
                repo_config = RepoConfig(
                    name=repo,
                    full_name=repo_full_name,
                )

                # Initialize the GitRepoClient to fetch the latest commit
                git_client = GitRepoClient(repo_config=repo_config, access_token=os.environ["GITHUB_ACCESS_TOKEN"])

                # Get the default branch and its latest commit
                branch = git_client.get_branch_safe(git_client.default_branch)
                commit = branch.commit.sha if branch and branch.commit else None

                if commit:
                    # Get the CodegenEventsApi class
                    Klass = self.get_event_handler_cls()
                    # Create an instance with the latest commit
                    klass = Klass(repo_org=org, repo_name=repo, commit=commit)

                    # Ping the function to refresh the snapshot
                    result = klass.ping.remote()

                    logging.info(f"Refreshed snapshot for {repo_full_name} with commit {commit}: {result}")
                else:
                    logging.warning(f"Could not fetch latest commit for {repo_full_name}")

            except Exception as e:
                logging.exception(f"Error refreshing snapshot for {repo_full_name}: {e!s}")


class CodebaseEventsApp:
    """This class is intended to be registered as a modal Class
    and will be used to register event handlers for webhook events. It includes snapshotting behavior
    and should be used with CodebaseEventsAPI.

    Usage:
    @app.cls(image=base_image, secrets=[modal.Secret.from_dotenv()], enable_memory_snapshot=True, container_idle_timeout=300)
    class YourCustomerEventsAPP(CodebaseEventsApp):
        pass
    """

    commit: str = modal.parameter(default="")
    repo_org: str = modal.parameter(default="")
    repo_name: str = modal.parameter(default="")
    snapshot_index_id: str = DEFAULT_SNAPSHOT_DICT_ID

    def get_codegen_app(self) -> CodegenApp:
        full_repo_name = f"{self.repo_org}/{self.repo_name}"
        return CodegenApp(name=f"{full_repo_name}-events", repo=full_repo_name, commit=self.commit)

    @modal.enter(snap=True)
    def load(self):
        self.cg = self.get_codegen_app()
        self.cg.parse_repo()
        self.setup_handlers(self.cg)

        # TODO: if multiple snapshots are taken for the same commit, we will need to compare commit timestamps
        snapshot_dict = modal.Dict.from_name(self.snapshot_index_id, {}, create_if_missing=True)
        snapshot_dict.put(f"{self.repo_org}/{self.repo_name}", self.commit)

    def setup_handlers(self, cg: CodegenApp):
        msg = "Subclasses must implement this method"
        raise NotImplementedError(msg)

    @modal.method()
    async def proxy_event(self, route: str, payload: dict, headers: dict):
        logger.info(f"Handling event: {route}")
        request = await fastapi_request_adapter(payload=payload, headers=headers, route=route)

        if "slack/events" in route:
            response_data = await self.cg.handle_slack_event(request)
        elif "github/events" in route:
            response_data = await self.cg.handle_github_event(request)
        elif "linear/events" in route:
            response_data = await self.cg.handle_linear_event(request)
        else:
            msg = f"Invalid route: {route}"
            raise ValueError(msg)

        return response_data

    @modal.method()
    def ping(self):
        logger.info(f"Pinging function with repo: {self.repo_org}/{self.repo_name} commit: {self.commit}")
        return {"status": "ok"}

    @modal.asgi_app()
    def fastapi_endpoint(self):
        logger.info("Serving FastAPI app from class method")
        return self.cg.app
