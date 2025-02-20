from typing import Optional
from uuid import uuid4

from codegen.extensions.langchain.agent import create_codebase_agent
from codegen.sdk.core.codebase import Codebase


class CodeAgent:
    """Agent for interacting with a codebase."""

    def __init__(self, codebase: Codebase):
        self.codebase = codebase
        self.agent = create_codebase_agent(self.codebase)

    def run(self, prompt: str, session_id: Optional[str] = None) -> str:
        if session_id is None:
            session_id = str(uuid4())
        return self.agent.invoke(
            {"input": prompt},
            config={"configurable": {"session_id": session_id}},
        )
