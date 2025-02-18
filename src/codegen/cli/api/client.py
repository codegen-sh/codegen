import json
from typing import ClassVar, TypeVar

import requests
from pydantic import BaseModel
from rich import print as rprint

from codegen.cli.api.endpoints import (
    CREATE_ENDPOINT,
    DEPLOY_ENDPOINT,
    DOCS_ENDPOINT,
    EXPERT_ENDPOINT,
    IDENTIFY_ENDPOINT,
    IMPROVE_ENDPOINT,
    LOOKUP_ENDPOINT,
    PR_LOOKUP_ENDPOINT,
    RUN_ENDPOINT,
    RUN_ON_PR_ENDPOINT,
)
from codegen.cli.api.schemas import (
    AskExpertInput,
    AskExpertResponse,
    CodemodRunType,
    CreateInput,
    CreateResponse,
    DeployInput,
    DeployResponse,
    DocsInput,
    DocsResponse,
    IdentifyResponse,
    ImproveCodemodInput,
    ImproveCodemodResponse,
    LookupInput,
    LookupOutput,
    PRLookupInput,
    PRLookupResponse,
    RunCodemodInput,
    RunCodemodOutput,
    RunOnPRInput,
    RunOnPRResponse,
)
from codegen.cli.auth.session import CodegenSession
from codegen.cli.codemod.convert import convert_to_ui
from codegen.cli.env.global_env import global_env
from codegen.cli.errors import InvalidTokenError, ServerError
from codegen.cli.utils.codemods import Codemod
from codegen.cli.utils.function_finder import DecoratedFunction
from codegen.shared.enums.programming_language import ProgrammingLanguage

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class RestAPI:
    """Handles auth + validation with the codegen API."""

    _session: ClassVar[requests.Session] = requests.Session()

    auth_token: str

    def __init__(self, auth_token: str):
        self.auth_token = auth_token

    def _get_headers(self) -> dict[str, str]:
        """Get headers with authentication token."""
        return {"Authorization": f"Bearer {self.auth_token}"}

    def _make_request(
        self,
        method: str,
        endpoint: str,
        input_data: InputT | None,
        output_model: type[OutputT],
    ) -> OutputT:
        """Make an API request with input validation and response handling."""
        if global_env.DEBUG:
            rprint(f"[purple]{method}[/purple] {endpoint}")
            if input_data:
                rprint(f"{json.dumps(input_data.model_dump(), indent=4)}")

        try:
            headers = self._get_headers()

            json_data = input_data.model_dump() if input_data else None

            response = self._session.request(
                method,
                endpoint,
                json=json_data,
                headers=headers,
            )

            if response.status_code == 200:
                try:
                    return output_model.model_validate(response.json())
                except ValueError as e:
                    msg = f"Invalid response format: {e}"
                    raise ServerError(msg)
            elif response.status_code == 401:
                msg = "Invalid or expired authentication token"
                raise InvalidTokenError(msg)
            elif response.status_code == 500:
                msg = "The server encountered an error while processing your request"
                raise ServerError(msg)
            else:
                try:
                    error_json = response.json()
                    error_msg = error_json.get("detail", error_json)
                except Exception:
                    error_msg = response.text
                msg = f"Error ({response.status_code}): {error_msg}"
                raise ServerError(msg)

        except requests.RequestException as e:
            msg = f"Network error: {e!s}"
            raise ServerError(msg)

    def run(
        self,
        function: DecoratedFunction | Codemod,
        include_source: bool = True,
        run_type: CodemodRunType = CodemodRunType.DIFF,
        template_context: dict[str, str] | None = None,
    ) -> RunCodemodOutput:
        """Run a codemod transformation.

        Args:
            function: The function or codemod to run
            include_source: Whether to include the source code in the request.
                          If False, uses the deployed version.
            run_type: Type of run (diff or pr)
            template_context: Context variables to pass to the codemod

        """
        session = CodegenSession.from_active_session()
        base_input = {
            "codemod_name": function.name,
            "repo_full_name": session.config.repository.full_name,
            "codemod_run_type": run_type,
        }

        # Only include source if requested
        if include_source:
            source = function.get_current_source() if isinstance(function, Codemod) else function.source
            base_input["codemod_source"] = convert_to_ui(source)

        # Add template context if provided
        if template_context:
            base_input["template_context"] = template_context

        input_data = RunCodemodInput(input=RunCodemodInput.BaseRunCodemodInput(**base_input))
        return self._make_request(
            "POST",
            RUN_ENDPOINT,
            input_data,
            RunCodemodOutput,
        )

    def get_docs(self) -> DocsResponse:
        """Search documentation."""
        session = CodegenSession.from_active_session()
        return self._make_request(
            "GET",
            DOCS_ENDPOINT,
            DocsInput(docs_input=DocsInput.BaseDocsInput(repo_full_name=session.config.repository.full_name)),
            DocsResponse,
        )

    def ask_expert(self, query: str) -> AskExpertResponse:
        """Ask the expert system a question."""
        return self._make_request(
            "GET",
            EXPERT_ENDPOINT,
            AskExpertInput(input=AskExpertInput.BaseAskExpertInput(query=query)),
            AskExpertResponse,
        )

    def create(self, name: str, query: str) -> CreateResponse:
        """Get AI-generated starter code for a codemod."""
        session = CodegenSession.from_active_session()
        language = ProgrammingLanguage(session.config.repository.language)
        return self._make_request(
            "GET",
            CREATE_ENDPOINT,
            CreateInput(input=CreateInput.BaseCreateInput(name=name, query=query, language=language)),
            CreateResponse,
        )

    def identify(self) -> IdentifyResponse | None:
        """Identify the user's codemod."""
        return self._make_request(
            "POST",
            IDENTIFY_ENDPOINT,
            None,
            IdentifyResponse,
        )

    def deploy(
        self,
        codemod_name: str,
        codemod_source: str,
        lint_mode: bool = False,
        lint_user_whitelist: list[str] | None = None,
        message: str | None = None,
        arguments_schema: dict | None = None,
    ) -> DeployResponse:
        """Deploy a codemod to the Modal backend."""
        session = CodegenSession.from_active_session()
        return self._make_request(
            "POST",
            DEPLOY_ENDPOINT,
            DeployInput(
                input=DeployInput.BaseDeployInput(
                    codemod_name=codemod_name,
                    codemod_source=codemod_source,
                    repo_full_name=session.config.repository.full_name,
                    lint_mode=lint_mode,
                    lint_user_whitelist=lint_user_whitelist or [],
                    message=message,
                    arguments_schema=arguments_schema,
                )
            ),
            DeployResponse,
        )

    def lookup(self, codemod_name: str) -> LookupOutput:
        """Look up a codemod by name."""
        session = CodegenSession.from_active_session()
        return self._make_request(
            "GET",
            LOOKUP_ENDPOINT,
            LookupInput(input=LookupInput.BaseLookupInput(codemod_name=codemod_name, repo_full_name=session.config.repository.full_name)),
            LookupOutput,
        )

    def run_on_pr(self, codemod_name: str, repo_full_name: str, github_pr_number: int, language: str | None = None) -> RunOnPRResponse:
        """Test a webhook against a specific PR."""
        return self._make_request(
            "POST",
            RUN_ON_PR_ENDPOINT,
            RunOnPRInput(
                input=RunOnPRInput.BaseRunOnPRInput(
                    codemod_name=codemod_name,
                    repo_full_name=repo_full_name,
                    github_pr_number=github_pr_number,
                    language=language,
                )
            ),
            RunOnPRResponse,
        )

    def lookup_pr(self, repo_full_name: str, github_pr_number: int) -> PRLookupResponse:
        """Look up a PR by repository and PR number."""
        return self._make_request(
            "GET",
            PR_LOOKUP_ENDPOINT,
            PRLookupInput(input=PRLookupInput.BasePRLookupInput(repo_full_name=repo_full_name, github_pr_number=github_pr_number)),
            PRLookupResponse,
        )

    def improve_codemod(self, codemod: str, task: str, concerns: list[str], context: dict[str, str], language: ProgrammingLanguage) -> ImproveCodemodResponse:
        """Improve a codemod."""
        return self._make_request(
            "GET",
            IMPROVE_ENDPOINT,
            ImproveCodemodInput(input=ImproveCodemodInput.BaseImproveCodemodInput(codemod=codemod, task=task, concerns=concerns, context=context, language=language)),
            ImproveCodemodResponse,
        )
