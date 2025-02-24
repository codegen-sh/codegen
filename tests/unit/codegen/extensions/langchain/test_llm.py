"""Tests for the unified LLM class."""

import os
from unittest.mock import AsyncMock, patch

import pytest
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from codegen.extensions.langchain.llm import LLM


@pytest.fixture
def mock_env():
    """Mock environment with API keys."""
    original_env = dict(os.environ)
    os.environ.update(
        {
            "ANTHROPIC_API_KEY": "test-anthropic-key",
            "OPENAI_API_KEY": "test-openai-key",
        }
    )
    yield
    os.environ.clear()
    os.environ.update(original_env)


def test_init_default_anthropic(mock_env):
    """Test default initialization with Anthropic."""
    llm = LLM()
    assert isinstance(llm._model, ChatAnthropic)
    assert llm.model_provider == "anthropic"
    assert llm.model_name == "claude-3-5-sonnet-latest"
    assert llm.temperature == 0


def test_init_openai(mock_env):
    """Test initialization with OpenAI."""
    llm = LLM(
        model_provider="openai",
        model_name="gpt-4",
        temperature=0.7,
        top_p=0.9,
    )
    assert isinstance(llm._model, ChatOpenAI)
    assert llm.model_provider == "openai"
    assert llm.model_name == "gpt-4"
    assert llm.temperature == 0.7
    assert llm.top_p == 0.9


def test_anthropic_missing_api_key():
    """Test error when Anthropic API key is missing."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError) as exc_info:
            LLM()
        assert "ANTHROPIC_API_KEY not found" in str(exc_info.value)


def test_openai_missing_api_key():
    """Test error when OpenAI API key is missing."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError) as exc_info:
            LLM(model_provider="openai")
        assert "OPENAI_API_KEY not found" in str(exc_info.value)


def test_invalid_model_provider():
    """Test error with invalid model provider."""
    with pytest.raises(ValueError) as exc_info:
        LLM(model_provider="invalid")
    assert "Must be one of: anthropic, openai" in str(exc_info.value)


def test_invalid_temperature():
    """Test error with invalid temperature."""
    with pytest.raises(ValueError) as exc_info:
        LLM(temperature=2.0)
    assert "temperature" in str(exc_info.value)


def test_invalid_top_p():
    """Test error with invalid top_p."""
    with pytest.raises(ValueError) as exc_info:
        LLM(top_p=2.0)
    assert "top_p" in str(exc_info.value)


def test_invalid_top_k():
    """Test error with invalid top_k."""
    with pytest.raises(ValueError) as exc_info:
        LLM(top_k=0)
    assert "top_k" in str(exc_info.value)


@pytest.mark.asyncio
async def test_generate_anthropic(mock_env):
    """Test generate with Anthropic model."""
    llm = LLM()
    messages = [HumanMessage(content="Hello!")]

    # Mock the underlying model's _generate method
    mock_generate = AsyncMock()
    with patch.object(ChatAnthropic, "_generate", mock_generate):
        await llm._generate(messages)
        mock_generate.assert_called_once_with(
            messages,
            stop=None,
            run_manager=None,
        )


@pytest.mark.asyncio
async def test_generate_openai(mock_env):
    """Test generate with OpenAI model."""
    llm = LLM(model_provider="openai")
    messages = [HumanMessage(content="Hello!")]

    # Mock the underlying model's _generate method
    mock_generate = AsyncMock()
    with patch.object(ChatOpenAI, "_generate", mock_generate):
        await llm._generate(messages)
        mock_generate.assert_called_once_with(
            messages,
            stop=None,
            run_manager=None,
        )


def test_unsupported_kwargs(mock_env):
    """Test that unsupported kwargs are filtered out."""
    llm = LLM(
        unsupported_kwarg="value",
        temperature=0.5,
    )
    assert not hasattr(llm, "unsupported_kwarg")
    assert llm.temperature == 0.5


@pytest.mark.asyncio
async def test_stop_sequence(mock_env):
    """Test that stop sequences are passed through."""
    llm = LLM()
    messages = [HumanMessage(content="Hello!")]
    stop = ["STOP"]

    mock_generate = AsyncMock()
    with patch.object(ChatAnthropic, "_generate", mock_generate):
        await llm._generate(messages, stop=stop)
        mock_generate.assert_called_once_with(
            messages,
            stop=stop,
            run_manager=None,
        )
