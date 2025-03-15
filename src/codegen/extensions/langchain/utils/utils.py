from langchain_core.language_models import LLM


def get_max_model_input_tokens(llm: LLM) -> int:
    """Get the maximum input tokens for the current model.

    Returns:
        int: Maximum number of input tokens supported by the model
    """
    # For Claude models not explicitly listed, if model name contains "claude", use Claude's limit
    if "claude" in llm.model.lower():
        return 200000
    # For GPT-4 models
    elif "gpt-4" in llm.model.lower():
        return 128000
    # For Grok models
    elif "grok" in llm.model.lower():
        return 1000000

    # default to gpt as it's lower bound
    return 128000
