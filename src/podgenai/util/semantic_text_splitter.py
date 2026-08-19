from semantic_text_splitter import TextSplitter


def semantic_split_by_length(text: str, limit: int) -> list[str]:
    """Return a list of chunks from the given text, splitting it at semantically sensible boundaries while applying the specified character length limit for each chunk."""
    # Ref: https://stackoverflow.com/a/78288960/
    splitter = TextSplitter(limit)
    chunks = splitter.chunks(text)
    return chunks

def semantic_split_by_tokens(text: str, *, model: str, limit: int) -> list[str]:
    """Return a list of chunks from the given text, splitting it at semantically sensible boundaries while applying the specified model's token length limit for each chunk."""
    splitter = TextSplitter.from_tiktoken_model(model, limit)
    chunks = splitter.chunks(text)
    return chunks