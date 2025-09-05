import os

from codegen.cli.api.endpoints import API_ENDPOINT

# Prefer explicit override; fall back to the CLI's unified API endpoint
CODEGEN_BASE_API_URL = os.environ.get("CODEGEN_API_BASE_URL", API_ENDPOINT.rstrip("/"))
