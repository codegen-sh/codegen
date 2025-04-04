"""Langchain tools for workspace operations."""

from collections.abc import Callable
from typing import Annotated, ClassVar, Literal, Optional

from langchain_core.messages import ToolMessage
from langchain_core.stores import InMemoryBaseStore
from langchain_core.tools import InjectedToolCallId
from langchain_core.tools.base import BaseTool
from langgraph.prebuilt import InjectedStore
from pydantic import BaseModel, Field

from codegen.extensions.linear.linear_client import LinearClient
from codegen.extensions.tools.bash import run_bash_command
from codegen.extensions.tools.github.checkout_pr import checkout_pr
from codegen.extensions.tools.github.view_pr_checks import view_pr_checks
from codegen.extensions.tools.global_replacement_edit import replacement_edit_global
from codegen.extensions.tools.linear.linear import (
    linear_comment_on_issue_tool,
    linear_create_issue_tool,
    linear_get_issue_comments_tool,
    linear_get_issue_tool,
    linear_get_teams_tool,
    linear_search_issues_tool,
)
from codegen.extensions.tools.link_annotation import add_links_to_message
from codegen.extensions.tools.reflection import perform_reflection
from codegen.extensions.tools.relace_edit import relace_edit
from codegen.extensions.tools.replacement_edit import replacement_edit
from codegen.extensions.tools.reveal_symbol import reveal_symbol
from codegen.extensions.tools.search import search
from codegen.extensions.tools.search_files_by_name import search_files_by_name
from codegen.extensions.tools.semantic_edit import semantic_edit
from codegen.extensions.tools.semantic_search import semantic_search
from codegen.sdk.core.codebase import Codebase

from ..tools import (
    commit,
    create_file,
    create_pr,
    create_pr_comment,
    create_pr_review_comment,
    delete_file,
    edit_file,
    list_directory,
    move_symbol,
    rename_file,
    view_file,
    view_pr,
)
from ..tools.relace_edit_prompts import RELACE_EDIT_PROMPT
from ..tools.semantic_edit_prompts import FILE_EDIT_PROMPT
