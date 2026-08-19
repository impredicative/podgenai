from tiktoken import encoding_for_model

def get_token_count(text: str, *, model: str) -> int:
    """Return the number of tokens in the given text for the specified model."""
    encoding = encoding_for_model(model)
    token_count = len(encoding.encode(text))
    return token_count