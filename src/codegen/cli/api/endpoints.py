import os

from codegen.cli.api.modal import MODAL_PREFIX

RUN_ENDPOINT = f"https://{MODAL_PREFIX}--cli-run.modal.run"
DOCS_ENDPOINT = f"https://{MODAL_PREFIX}--cli-docs.modal.run"
EXPERT_ENDPOINT = f"https://{MODAL_PREFIX}--cli-ask-expert.modal.run"
IDENTIFY_ENDPOINT = f"https://{MODAL_PREFIX}--cli-identify.modal.run"
CREATE_ENDPOINT = f"https://{MODAL_PREFIX}--cli-create.modal.run"
DEPLOY_ENDPOINT = f"https://{MODAL_PREFIX}--cli-deploy.modal.run"
LOOKUP_ENDPOINT = f"https://{MODAL_PREFIX}--cli-lookup.modal.run"
RUN_ON_PR_ENDPOINT = f"https://{MODAL_PREFIX}--cli-run-on-pull-request.modal.run"
PR_LOOKUP_ENDPOINT = f"https://{MODAL_PREFIX}--cli-pr-lookup.modal.run"
CODEGEN_SYSTEM_PROMPT_URL = "https://raw.githubusercontent.com/codegen-sh/codegen-sdk/develop/src/codegen/sdk/system-prompt.txt"
IMPROVE_ENDPOINT = f"https://{MODAL_PREFIX}--cli-improve.modal.run"
MCP_SERVER_ENDPOINT = f"https://{MODAL_PREFIX}--codegen-mcp-server.modal.run/mcp"

# API ENDPOINT
# Prefer explicit override via CODEGEN_API_BASE_URL; fallback to Modal-derived URL for current ENV
API_ENDPOINT = os.environ.get("CODEGEN_API_BASE_URL", f"https://{MODAL_PREFIX}--rest-api.modal.run/")
