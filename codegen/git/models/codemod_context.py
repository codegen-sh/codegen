from importlib.metadata import version
from typing import Any

from pydantic import BaseModel
from pydantic.fields import Field

from codegen.git.models.pull_request_context import PullRequestContext
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class CodemodContext(BaseModel):
    CODEGEN_VERSION: str = version("codegen")
    CODEMOD_ID: int | None = None
    CODEMOD_LINK: str | None = None
    CODEMOD_AUTHOR: str | None = None
    TEMPLATE_ARGS: dict[str, Any] = Field(default_factory=dict)

    # TODO: add fields for version
    # CODEMOD_VERSION_ID: int | None = None
    # CODEMOD_VERSION_AUTHOR: str | None = None

    PULL_REQUEST: PullRequestContext | None = None

    @classmethod
    def _render_template(cls, template_schema: dict[str, str], template_values: dict[str, Any]) -> dict[str, Any]:
        template_data: dict[str, Any] = {}
        for var_name, var_value in template_values.items():
            var_type = template_schema.get(var_name)

            if var_type == "list":
                template_data[var_name] = [str(v).strip() for v in var_value.split(",")]
            else:
                template_data[var_name] = str(var_value)
        return template_data
