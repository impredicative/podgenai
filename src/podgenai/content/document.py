import io

import podgenai.exceptions
from podgenai.util.openai import MODELS
from podgenai.util.tiktoken import get_token_count


def ensure_document_is_valid(document: str) -> None:
    """Raise `InputError` if the document is too large for the knowledge model or text model's input capacity."""
    assert isinstance(document, str), (document, type(document))
    exception = podgenai.exceptions.InputError

    if document != document.strip():
        raise exception("Document contains leading or trailing whitespace.")

    if len(document) == 0:
        raise exception("Document is empty.")

    models = (MODELS["knowledge"], MODELS["text"])
    for model in models:
        document_token_count = get_token_count(document, model=model["name"])
        text_model_input_token_capacity = model["context_window"] - model["max_output"]
        if document_token_count > text_model_input_token_capacity:
            excess_tokens = document_token_count - text_model_input_token_capacity
            reduction_ratio = excess_tokens / document_token_count
            raise exception(f"Document uses {document_token_count:,} tokens, but the {model['name']} model's input capacity is {text_model_input_token_capacity:,} tokens. Reduce the document size by at least {excess_tokens:,} tokens ({reduction_ratio:.0%}).")

    for line_num, line in enumerate(io.StringIO(document), start=1):
        line = line.strip()
        for tag in ("<document>", "</document>"):
            if line == tag:
                raise exception(f"Document contains a line with the '{tag}' tag on line {line_num}. It must not contain the tag.")
