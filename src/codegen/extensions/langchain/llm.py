"""LLM implementation supporting both OpenAI and Anthropic models."""

import os
from typing import Any, Literal, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult
from langchain_openai import ChatOpenAI
from pydantic import Field


class LLM(BaseChatModel):
    """A unified chat model that supports both OpenAI and Anthropic."""

    model_provider: Literal["anthropic", "openai"] = Field(default="anthropic", description="The model provider to use.")

    model_name: str = Field(default="claude-3-5-sonnet-latest", description="Name of the model to use.")

    temperature: float = Field(default=0, description="Temperature parameter for the model.", ge=0, le=1)

    top_p: float = Field(default=1, description="Top-p sampling parameter.", ge=0, le=1)

    top_k: int = Field(default=1, description="Top-k sampling parameter.", ge=1)

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the LLM.

        Args:
            **kwargs: Configuration options. Supported options:
                - model_provider: "anthropic" or "openai"
                - model_name: Name of the model to use
                - temperature: Temperature parameter (0-1)
                - top_p: Top-p sampling parameter (0-1)
                - top_k: Top-k sampling parameter (>= 1)
        """
        # Filter out unsupported kwargs
        supported_kwargs = {"model_provider", "model_name", "temperature", "top_p", "top_k", "callbacks", "tags", "metadata"}
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in supported_kwargs}

        super().__init__(**filtered_kwargs)
        self._model = self._get_model()

    @property
    def _llm_type(self) -> str:
        """Return identifier for this LLM class."""
        return "unified_chat_model"

    def _get_model_kwargs(self) -> dict[str, Any]:
        """Get kwargs for the specific model provider."""
        base_kwargs = {
            "temperature": self.temperature,
            "top_p": self.top_p,
        }

        if self.model_provider == "anthropic":
            return {**base_kwargs, "model": self.model_name, "top_k": self.top_k}
        else:  # openai
            return {**base_kwargs, "model": self.model_name}

    def _get_model(self) -> BaseChatModel:
        """Get the appropriate model instance based on configuration."""
        if self.model_provider == "anthropic":
            if not os.getenv("ANTHROPIC_API_KEY"):
                msg = "ANTHROPIC_API_KEY not found in environment. Please set it in your .env file or environment variables."
                raise ValueError(msg)
            return ChatAnthropic(**self._get_model_kwargs())

        elif self.model_provider == "openai":
            if not os.getenv("OPENAI_API_KEY"):
                msg = "OPENAI_API_KEY not found in environment. Please set it in your .env file or environment variables."
                raise ValueError(msg)
            return ChatOpenAI(**self._get_model_kwargs())

        msg = f"Unknown model provider: {self.model_provider}. Must be one of: anthropic, openai"
        raise ValueError(msg)

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate chat completion using the underlying model.

        Args:
            messages: The messages to generate from
            stop: Optional list of stop sequences
            run_manager: Optional callback manager for tracking the run
            **kwargs: Additional arguments to pass to the model

        Returns:
            ChatResult containing the generated completion
        """
        return self._model._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
