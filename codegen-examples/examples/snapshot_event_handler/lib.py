import json
import os
from typing import Literal
from fastapi import APIRouter, FastAPI, Request
import modal
import logging
from codegen.extensions.events.codegen_app import CodegenApp
from codegen.git.clients.git_repo_client import GitRepoClient
from codegen.git.schemas.repo_config import RepoConfig
from fastapi_utils.cbv import cbv

logging.basicConfig(level=logging.INFO, force=True)
logger = logging.getLogger(__name__)

# refactor this to be a config
SNAPSHOT_DICT_ID = "codegen-events-codebase-snapshots"


class EventRouterAPI:
    """ 
    This class is intended to be registered as a modal Class
    and will be used to route events to the correct handler.

    Usage:
    @codegen_events_app.cls(image=base_image, secrets=[modal.Secret.from_dotenv()])
    class CustomEventAPI(EventRouterAPI):
        pass
    
    """


    def get_event_handler_cls(self) -> modal.Cls:
        """ lookup the Modal Class where the event handlers are defined"""
        raise NotImplementedError("Subclasses must implement this method")

    async def handle_event(self, org: str, repo: str, provider: Literal["slack", "github", "linear"], request: Request):

        repo_config = RepoConfig(
            name=repo,
            full_name=f"{org}/{repo}",
        )

        repo_snapshotdict = modal.Dict.from_name(SNAPSHOT_DICT_ID, {}, create_if_missing=True)

        last_snapshot_commit = repo_snapshotdict.get(f"{org}/{repo}", None)

        if last_snapshot_commit is None:

            git_client = GitRepoClient(repo_config=repo_config, access_token=os.environ["GITHUB_ACCESS_TOKEN"])
            branch = git_client.get_branch_safe(git_client.default_branch)
            last_snapshot_commit = branch.commit.sha if branch and branch.commit else None
        
        Klass = self.get_event_handler_cls()
        klass = Klass(repo_org=org, repo_name=repo, commit=last_snapshot_commit)

        print(f"Repo info: org: {org} repo: {repo} commit: {last_snapshot_commit}")
        print("DEBUG: ", await request.body())
        request_payload = await request.json()
        request_headers = dict(request.headers)
        request_headers.pop('host', None)  # Remove host header if present
  

        if provider == "slack":
            return klass.proxy_event.remote(f"{org}/{repo}/slack/events", payload=request_payload, headers=request_headers)
        elif provider == "github":
            return klass.proxy_event.remote(f"{org}/{repo}/github/events", payload=request_payload, headers=request_headers)
        elif provider == "linear":
            return klass.proxy_event.remote(f"{org}/{repo}/linear/events", payload=request_payload, headers=request_headers)
        else:
            raise ValueError(f"Invalid provider: {provider}")
    


    def refresh_repository_snapshots(self, snapshot_index_id: str):
        """Refresh the latest snapshot for all repositories in the dictionary."""
        # Get all repositories from the modal.Dict
        repo_dict = modal.Dict.from_name(snapshot_index_id, {}, create_if_missing=True)
        
        for repo_full_name in repo_dict.keys():
            try:
                # Parse the repository full name to get org and repo
                org, repo = repo_full_name.split('/')
                
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
                logging.error(f"Error refreshing snapshot for {repo_full_name}: {str(e)}")




class CodebaseEventsApp:
    """
    This class is intended to be registered as a modal Class
    and will be used to route events to the correct handler. It includes snapshotting behavior
    and should be used with CodebaseEventsAPI.
    
    Usage:
    @app.cls(image=base_image, secrets=[modal.Secret.from_dotenv()], enable_memory_snapshot=True, container_idle_timeout=300)
    class YourCustomerEventsAPP(CodebaseEventsApp):
        pass
    """

    commit: str = modal.parameter(default="79114f67ccfe8700416cd541d1c7c43659a95342") 
    repo_org: str = modal.parameter(default="codegen-sh")
    repo_name: str = modal.parameter(default="Kevin-s-Adventure-Game")


    def get_codegen_app(self) -> CodegenApp:
        full_repo_name = f"{self.repo_org}/{self.repo_name}"
        return CodegenApp(name=f"{full_repo_name}-events", repo=full_repo_name, commit=self.commit)

    @modal.enter(snap=True)
    def load(self):
        logger.info("Preparing codegen fastapi app")

        self.cg = self.get_codegen_app()
        self.cg.parse_repo()
        self.setup_handlers(self.cg)


        # TODO: if multiple snapshots are taken for the same commit, we will need to compare commit timestamps
        snapshot_dict = modal.Dict.from_name(SNAPSHOT_DICT_ID, {}, create_if_missing=True)
        snapshot_dict.put(f"{self.repo_org}/{self.repo_name}", self.commit)
    
    def setup_handlers(self, cg: CodegenApp):
        pass
    
    @modal.method()
    async def proxy_event(self, route: str, payload: dict, headers: dict):
        logger.info(f"Handling event: {route}")
        
        # Create a FastAPI Request object from the payload and headers
        # 1. Create the scope dictionary
        scope = {
            "type": "http",
            "method": "POST",
            "path": f"/{route}",
            "raw_path": f"/{route}".encode(),
            "query_string": b"",
            "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
            "client": ("127.0.0.1", 0),  # Default client address
            "app": self.cg.app,
        }
        
        # 2. Create a receive function that returns the request body
        body_bytes = json.dumps(payload).encode()
        
        async def receive():
            return {
                "type": "http.request",
                "body": body_bytes,
                "more_body": False,
            }
        
        # 3. Create a send function to capture the response
        response_body = []
        response_status = None
        response_headers = None
        
        async def send(message):
            nonlocal response_status, response_headers
            
            if message["type"] == "http.response.start":
                response_status = message["status"]
                response_headers = message["headers"]
            elif message["type"] == "http.response.body":
                response_body.append(message.get("body", b""))
        
        # 4. Create the request object
        request = Request(scope, receive)
        
        # 5. Call the appropriate handler based on the route
        if "slack/events" in route:
            response_data = await self.cg.handle_slack_event(request)
        elif "github/events" in route:
            response_data = await self.cg.handle_github_event(request)
        elif "linear/events" in route:
            response_data = await self.cg.handle_linear_event(request)
        else:
            # Call the ASGI app directly if no specific handler
            await self.cg.app(scope, receive, send)
            # Combine response body chunks
            body = b"".join(response_body)
            if body:
                try:
                    response_data = json.loads(body)
                except json.JSONDecodeError:
                    response_data = {"body": body.decode("utf-8", errors="replace")}
            else:
                response_data = {"status": response_status}
        
        return response_data
    
    @modal.method()
    def ping(self):
        logger.info(f"Pinging function with repo: {self.repo_org}/{self.repo_name} commit: {self.commit}")
        return {"status": "ok"}

    @modal.asgi_app()
    def fastapi_endpoint(self):
        logger.info("Serving FastAPI app from class method")
        return self.cg.app
 