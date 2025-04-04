"""Graph-based agent implementation."""

import logging
from typing import Any, Dict, List, Optional, Sequence, Union

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph_prebuilt.memory import MessagesState

from agentgen.backend.agents.utils import AgentConfig
from agentgen.backend.extensions.langchain.llm import LLM
from agentgen.backend.extensions.langchain.prompts import SUMMARIZE_CONVERSATION_PROMPT
from agentgen.backend.extensions.langchain.utils.custom_tool_node import CustomToolNode
from agentgen.backend.extensions.langchain.utils.utils import get_max_model_input_tokens

# ... keep the rest of the file unchanged ...
