"""LLM implementation supporting both OpenAI and Anthropic models."""

import os
import re
from collections.abc import Sequence
from typing import Any, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.base import LanguageModelInput
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.outputs import ChatResult
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain_xai import ChatXAI
from pydantic import Field


class LLM(BaseChatModel):
    """A unified chat model that supports both OpenAI and Anthropic."""

    model_provider: str = Field(default="anthropic", description="The model provider to use.")

    model_name: str = Field(default="claude-3-5-sonnet-latest", description="Name of the model to use.")

    temperature: float = Field(default=0, description="Temperature parameter for the model.", ge=0, le=1)

    top_p: Optional[float] = Field(default=None, description="Top-p sampling parameter.", ge=0, le=1)

    top_k: Optional[int] = Field(default=None, description="Top-k sampling parameter.", ge=1)

    max_tokens: Optional[int] = Field(default=None, description="Maximum number of tokens to generate.", ge=1)

    def __init__(self, model_provider: str = "anthropic", model_name: str = "claude-3-5-sonnet-latest", **kwargs: Any) -> None:
        """Initialize the LLM.

        Args:
            model_provider: "anthropic" or "openai"
            model_name: Name of the model to use
            **kwargs: Additional configuration options. Supported options:
                - temperature: Temperature parameter (0-1)
                - top_p: Top-p sampling parameter (0-1)
                - top_k: Top-k sampling parameter (>= 1)
                - max_tokens: Maximum number of tokens to generate
        """
        # Set model provider and name before calling super().__init__
        kwargs["model_provider"] = model_provider
        kwargs["model_name"] = model_name

        # Filter out unsupported kwargs
        supported_kwargs = {"model_provider", "model_name", "temperature", "top_p", "top_k", "max_tokens", "callbacks", "tags", "metadata"}
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
        }

        if self.top_p is not None:
            base_kwargs["top_p"] = self.top_p

        if self.top_k is not None:
            base_kwargs["top_k"] = self.top_k

        if self.max_tokens is not None:
            base_kwargs["max_tokens"] = self.max_tokens

        if self.model_provider == "anthropic":
            return {**base_kwargs, "model": self.model_name}
        elif self.model_provider == "xai":
            xai_api_base = os.getenv("XAI_API_BASE", "https://api.x.ai/v1/")
            return {**base_kwargs, "model": self.model_name, "xai_api_base": xai_api_base}
        else:  # openai
            return {**base_kwargs, "model": self.model_name}

    def _get_model(self) -> BaseChatModel:
        """Get the appropriate model instance based on configuration."""
        if self.model_provider == "anthropic":
            if not os.getenv("ANTHROPIC_API_KEY"):
                msg = "ANTHROPIC_API_KEY not found in environment. Please set it in your .env file or environment variables."
                raise ValueError(msg)
            max_tokens = 8192
            return ChatAnthropic(**self._get_model_kwargs(), max_tokens=max_tokens, max_retries=10, timeout=1000)

        elif self.model_provider == "openai":
            if not os.getenv("OPENAI_API_KEY"):
                msg = "OPENAI_API_KEY not found in environment. Please set it in your .env file or environment variables."
                raise ValueError(msg)
            return ChatOpenAI(**self._get_model_kwargs(), max_tokens=4096, max_retries=10, timeout=1000)

        elif self.model_provider == "xai":
            if not os.getenv("XAI_API_KEY"):
                msg = "XAI_API_KEY not found in environment. Please set it in your .env file or environment variables."
                raise ValueError(msg)
            return ChatXAI(**self._get_model_kwargs(), max_tokens=12000)

        msg = f"Unknown model provider: {self.model_provider}. Must be one of: anthropic, openai, xai"
        raise ValueError(msg)

    def _process_messages_for_multimodal(self, messages: list[BaseMessage]) -> list[BaseMessage]:
        """Process messages to handle multimodal content (images).

        This function looks for image URLs in the format [Image: filename](URL) in message content
        and converts them to the appropriate format for multimodal models.

        Args:
            messages: List of messages to process

        Returns:
            Processed messages with multimodal content
        """
        processed_messages = []

        for message in messages:
            if not isinstance(message, HumanMessage):
                # Only process human messages for now
                processed_messages.append(message)
                continue

            content = message.content
            if isinstance(content, str):
                # Check for image URLs in the format [Image: filename](URL)
                image_pattern = r"\[Image(?:\s+\d+)?:\s+([^\]]+)\]\(([^)]+)\)"
                matches = re.findall(image_pattern, content)

                if not matches:
                    # No images found, keep the message as is
                    processed_messages.append(message)
                    continue

                # Convert to multimodal format
                multimodal_content = []
                last_end = 0

                for match in re.finditer(image_pattern, content):
                    # Add text before the image
                    if match.start() > last_end:
                        multimodal_content.append({"type": "text", "text": content[last_end : match.start()]})

                    # Add the image
                    image_url = match.group(2)
                    multimodal_content.append({"type": "image_url", "image_url": {"url": image_url}})

                    last_end = match.end()

                # Add any remaining text after the last image
                if last_end < len(content):
                    multimodal_content.append({"type": "text", "text": content[last_end:]})

                # Create a new message with multimodal content
                new_message = HumanMessage(content=multimodal_content)
                processed_messages.append(new_message)
            else:
                # Content is already in a different format, keep as is
                processed_messages.append(message)

        return processed_messages

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
        # Process messages for multimodal content if using a multimodal model
        if self.model_provider == "anthropic" and "claude-3" in self.model_name:
            processed_messages = self._process_messages_for_multimodal(messages)
            return self._model._generate(processed_messages, stop=stop, run_manager=run_manager, **kwargs)

        return self._model._generate(messages, stop=stop, run_manager=run_manager, **kwargs)

    def bind_tools(
        self,
        tools: Sequence[BaseTool],
        **kwargs: Any,
    ) -> Runnable[LanguageModelInput, BaseMessage]:
        """Bind tools to the underlying model.

        Args:
            tools: List of tools to bind
            **kwargs: Additional arguments to pass to the model

        Returns:
            Runnable that can be used to invoke the model with tools
        """
        return self._model.bind_tools(tools, **kwargs)
