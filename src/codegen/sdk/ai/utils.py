import tiktoken

ENCODERS = {
    "gpt-4o": tiktoken.encoding_for_model("gpt-4o"),
}


def count_tokens(s: str, model_name: str = "gpt-4o") -> int:
    """Uses tiktoken"""
    if s is None:
        return 0
    enc = ENCODERS.get(model_name, None)
    if not enc:
        ENCODERS[model_name] = tiktoken.encoding_for_model(model_name)
        enc = ENCODERS[model_name]
    tokens = enc.encode(s)
    return len(tokens)
