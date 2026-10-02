"""Tests of the callback splitter's public behavior and hard size limits."""

from unittest.mock import patch

import pytest
import tiktoken

from podgenai.util.semantic_text_splitter import semantic_split_by_length_and_tokens_using_callback

MODEL: str = "gpt-4o-mini-tts-2025-12-15"


@pytest.fixture(scope="module", params=[MODEL, "gpt-4"], ids=["o200k_base", "cl100k_base"])
def model(request: pytest.FixtureRequest) -> str:
    model_name = request.param
    assert isinstance(model_name, str)
    return model_name


@pytest.fixture(scope="module")
def encoding(model: str) -> tiktoken.Encoding:
    return tiktoken.encoding_for_model(model)


def assert_valid_chunks(text: str, chunks: list[str], *, encoding: tiktoken.Encoding, length_limit: int, token_limit: int) -> None:
    """Check both limits and preserve source order, allowing boundary trimming."""
    assert chunks, "Non-whitespace input must produce at least one chunk"
    remaining = text.lstrip()

    for chunk in chunks:
        assert chunk, "Chunks must not be empty"
        assert chunk == chunk.strip(), "Chunks must trim surrounding whitespace"
        assert len(chunk) <= length_limit, repr(chunk)
        assert len(encoding.encode(chunk)) <= token_limit, repr(chunk)
        assert remaining.startswith(chunk), "Chunks must preserve source text and order"
        remaining = remaining[len(chunk) :].lstrip()

    assert not remaining, "Chunks must preserve all non-whitespace input"


@pytest.mark.parametrize("text", ["", "Hello, world."], ids=["empty", "nonempty"])
@pytest.mark.parametrize(
    ("length_limit", "token_limit", "message"),
    [
        pytest.param(0, 2000, "length_limit must be greater than 0", id="zero-length"),
        pytest.param(-1, 2000, "length_limit must be greater than 0", id="negative-length"),
        pytest.param(4096, 0, "token_limit must be greater than 0", id="zero-tokens"),
        pytest.param(4096, -1, "token_limit must be greater than 0", id="negative-tokens"),
    ],
)
def test_rejects_nonpositive_limits(text: str, length_limit: int, token_limit: int, message: str) -> None:
    # An unknown model also ensures limit validation happens before model lookup.
    with pytest.raises(ValueError, match=message):
        semantic_split_by_length_and_tokens_using_callback(text, model="unknown-model", length_limit=length_limit, token_limit=token_limit)


def test_empty_text_does_not_require_a_known_model() -> None:
    assert semantic_split_by_length_and_tokens_using_callback("", model="unknown-model", length_limit=4096, token_limit=2000) == []


@pytest.mark.parametrize("text", [" ", "\t\r\n", "\u2003\n\t"])
def test_whitespace_only_text_returns_no_chunks(text: str, model: str) -> None:
    assert semantic_split_by_length_and_tokens_using_callback(text, model=model, length_limit=4096, token_limit=2000) == []


@pytest.mark.parametrize("text", ["Hello, world.", "Café  déjà vu.", "你好，世界！🙂", "establishment"])
def test_text_at_both_limits_remains_a_single_chunk(text: str, model: str, encoding: tiktoken.Encoding) -> None:
    chunks = semantic_split_by_length_and_tokens_using_callback(text, model=model, length_limit=len(text), token_limit=len(encoding.encode(text)))

    assert chunks == [text]


def test_trims_surrounding_whitespace_and_preserves_internal_whitespace(model: str) -> None:
    chunks = semantic_split_by_length_and_tokens_using_callback(" \t\nHello,  world.\r\n ", model=model, length_limit=4096, token_limit=2000)

    assert chunks == ["Hello,  world."]


def test_prefers_paragraph_boundaries_when_paragraphs_fit(model: str) -> None:
    paragraphs = ["The fox sleeps.", "The owl watches."]
    text = "\n\n".join(paragraphs)

    chunks = semantic_split_by_length_and_tokens_using_callback(text, model=model, length_limit=max(map(len, paragraphs)), token_limit=2000)

    assert chunks == paragraphs


@pytest.mark.parametrize(
    ("text", "length_limit", "token_limit"),
    [
        pytest.param("The fox walks through the quiet forest. " * 20, 73, 2000, id="character-limit"),
        pytest.param("The fox walks through the quiet forest. " * 20, 4096, 17, id="token-limit"),
        pytest.param("The fox walks through the quiet forest. " * 20, 73, 17, id="both-limits"),
        pytest.param("The fox walks through the quiet forest. " * 20, 32, 32, id="equal-limits"),
        pytest.param("The fox walks through the quiet forest. " * 20, 17, 73, id="more-tokens-than-characters"),
        pytest.param("a" * 120 + "\n\n" + "𝄞 " * 30, 73, 17, id="mixed-token-density"),
        pytest.param("Café déjà vu. 你好，世界！ 👩🏽‍💻 launches a rocket 🚀.\n\n" * 8, 31, 23, id="multilingual-paragraphs"),
        pytest.param("abc123-" * 80, 41, 29, id="no-whitespace"),
        pytest.param("The fox walks through the quiet forest. " * 700, 4096, 2000, id="tts-limits"),
    ],
)
def test_split_chunks_respect_both_limits_and_preserve_text(text: str, length_limit: int, token_limit: int, model: str, encoding: tiktoken.Encoding) -> None:
    assert len(text.strip()) > length_limit or len(encoding.encode(text.strip())) > token_limit

    chunks = semantic_split_by_length_and_tokens_using_callback(text, model=model, length_limit=length_limit, token_limit=token_limit)

    assert len(chunks) > 1
    assert_valid_chunks(text, chunks, encoding=encoding, length_limit=length_limit, token_limit=token_limit)


def test_regression_for_byte_length_shortcut(model: str, encoding: tiktoken.Encoding) -> None:
    # The naive multiplied capacity is 8: the library's shortcut can then
    # accept all eight bytes even though the character limit is only four.
    text = "foxy bar"
    chunks = semantic_split_by_length_and_tokens_using_callback(text, model=model, length_limit=4, token_limit=2)

    assert len(chunks) > 1
    assert_valid_chunks(text, chunks, encoding=encoding, length_limit=4, token_limit=2)


def test_character_limit_is_enforced_when_normalization_requires_rounding_up(model: str, encoding: tiktoken.Encoding) -> None:
    text = "establishment"
    length_limit = len(text) - 1
    token_limit = len(encoding.encode(text))
    assert 0 < token_limit < length_limit

    chunks = semantic_split_by_length_and_tokens_using_callback(text, model=model, length_limit=length_limit, token_limit=token_limit)

    assert len(chunks) > 1
    assert_valid_chunks(text, chunks, encoding=encoding, length_limit=length_limit, token_limit=token_limit)


def test_token_limit_is_enforced_when_normalization_requires_rounding_up(model: str, encoding: tiktoken.Encoding) -> None:
    # Musical clefs use multiple tokens per character. The full text exceeds
    # the token limit by one, while each individual character still fits.
    text = "𝄞𝄞"
    length_limit = len(text)
    token_limit = len(encoding.encode(text)) - 1
    assert token_limit > length_limit
    assert len(encoding.encode(text[:1])) <= token_limit

    chunks = semantic_split_by_length_and_tokens_using_callback(text, model=model, length_limit=length_limit, token_limit=token_limit)

    assert len(chunks) > 1
    assert_valid_chunks(text, chunks, encoding=encoding, length_limit=length_limit, token_limit=token_limit)


def test_rejects_unknown_model_for_nonempty_text() -> None:
    with pytest.raises(KeyError):
        semantic_split_by_length_and_tokens_using_callback("Hello, world.", model="unknown-model", length_limit=4096, token_limit=2000)


def test_checks_character_limit_of_each_returned_chunk(model: str) -> None:
    with patch("podgenai.util.semantic_text_splitter.TextSplitter") as splitter_type:
        splitter = splitter_type.from_callback.return_value
        splitter.chunks.return_value = ["Hello", "too long"]

        with pytest.raises(RuntimeError, match="length 8, exceeding length_limit=5"):
            semantic_split_by_length_and_tokens_using_callback("Hello too long", model=model, length_limit=5, token_limit=2000)


def test_checks_token_limit_of_each_returned_chunk(model: str, encoding: tiktoken.Encoding) -> None:
    oversized_chunk = "red green blue yellow"
    token_count = len(encoding.encode(oversized_chunk))
    token_limit = token_count - 1
    assert len(encoding.encode("red")) <= token_limit

    with patch("podgenai.util.semantic_text_splitter.TextSplitter") as splitter_type:
        splitter = splitter_type.from_callback.return_value
        splitter.chunks.return_value = ["red", oversized_chunk]

        with pytest.raises(RuntimeError, match=f"containing {token_count} tokens, exceeding token_limit={token_limit}"):
            semantic_split_by_length_and_tokens_using_callback(f"red {oversized_chunk}", model=model, length_limit=4096, token_limit=token_limit)


def test_passes_full_text_to_splitter_once(model: str) -> None:
    text = "Hello world.\n\nGoodbye world."
    expected_chunks = ["Hello world.", "Goodbye world."]

    with patch("podgenai.util.semantic_text_splitter.TextSplitter") as splitter_type:
        splitter = splitter_type.from_callback.return_value
        splitter.chunks.return_value = expected_chunks

        chunks = semantic_split_by_length_and_tokens_using_callback(text, model=model, length_limit=4096, token_limit=2000)

        assert chunks == expected_chunks
        splitter_type.from_callback.assert_called_once()
        splitter.chunks.assert_called_once_with(text)
