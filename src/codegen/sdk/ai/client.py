from openai import OpenAI


def get_openai_client(key: str) -> OpenAI:
    return OpenAI(api_key=key)
