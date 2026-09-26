import functools
from typing import Final

from tiktoken import Encoding, encoding_for_model, get_encoding

from podgenai.util.sys import print_warning

_FALLBACK_ENCODING: Final[Encoding] = get_encoding("o200k_base")


@functools.cache
def get_token_count(text: str, *, model: str) -> int:
    """Return the number of tokens in the given text for the specified model."""
    try:
        encoding = encoding_for_model(model)
    except KeyError:
        print_warning(f"Encoding for model {model} not found. Using fallback encoding {_FALLBACK_ENCODING.name}.")
        encoding = _FALLBACK_ENCODING
    token_count = len(encoding.encode(text))
    return token_count
