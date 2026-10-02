import tiktoken
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


def semantic_split_by_length_and_tokens_using_callback(text: str, *, model: str, length_limit: int, token_limit: int) -> list[str]:
    """Split text at semantic boundaries while enforcing both size limits.

    Each returned chunk satisfies both of these constraints:

        len(chunk) <= length_limit
        len(encoding.encode(chunk)) <= token_limit

    The naive combined sizing callback uses:

        size = max(character_count * token_limit, token_count * length_limit)
        capacity = length_limit * token_limit

    Although `size <= capacity` exactly represents both constraints, this
    scheme is unreliable with `semantic_text_splitter` 0.33.0. During
    semantic-level selection, the library skips the sizing callback when
    a section's UTF-8 byte length is at most `capacity`, assuming it fits.
    The multiplied size can exceed that byte length, so this shortcut can
    select an oversized section. If the section is later measured and
    found to exceed capacity, the fallback can still emit it to make progress.

    This function normalizes the callback's units using integer ceiling:

        scale = max(length_limit, token_limit)
        capacity = min(length_limit, token_limit)
        multiplied_size = max(
            character_count * token_limit,
            token_count * length_limit,
        )
        size = (multiplied_size + scale - 1) // scale

    For positive limits, `scale * capacity == length_limit * token_limit`,
    so rounding up preserves the original constraints exactly. Character
    count and tiktoken token count are each bounded by UTF-8 byte length.
    Because both multipliers are at most `scale`, the normalized size is
    also bounded by byte length, making the library's shortcut safe.

    For example, with `length_limit=4` and `token_limit=2`, the naive
    capacity is 8. The text `"foxy bar"` has 8 bytes but a multiplied size
    of at least 16, so the shortcut can incorrectly accept it. Normalization
    yields a capacity of 2 and a size of at least 4, correctly rejecting it.

    The full text is passed to the splitter once, and all returned chunks
    are explicitly checked against both original limits. Chunks use the
    splitter's default behavior of trimming surrounding whitespace.

    Raises:
        ValueError:
            If either limit is not positive.
        RuntimeError:
            If the splitter returns a chunk exceeding either limit.
    """
    if length_limit <= 0:
        raise ValueError("length_limit must be greater than 0")

    if token_limit <= 0:
        raise ValueError("token_limit must be greater than 0")

    if not text:
        return []

    encoding = tiktoken.encoding_for_model(model)
    scale = max(length_limit, token_limit)
    capacity = min(length_limit, token_limit)

    def size(chunk: str) -> int:
        tokens = len(encoding.encode(chunk))
        multiplied_size = max(len(chunk) * token_limit, tokens * length_limit)
        return (multiplied_size + scale - 1) // scale

    splitter = TextSplitter.from_callback(size, capacity)
    chunks = splitter.chunks(text)

    for chunk in chunks:
        if len(chunk) > length_limit:
            raise RuntimeError(f"Produced chunk of length {len(chunk)}, exceeding length_limit={length_limit}")

        chunk_token_length = len(encoding.encode(chunk))
        if chunk_token_length > token_limit:
            raise RuntimeError(f"Produced chunk containing {chunk_token_length} tokens, exceeding token_limit={token_limit}")

    return chunks


def semantic_split_by_length_and_tokens_using_search(
    text: str,
    *,
    model: str,
    length_limit: int,
    token_limit: int,
) -> list[str]:
    """Split text at semantically sensible boundaries while enforcing both
    a character-length limit and a model-specific token limit.

    Each returned chunk satisfies both of these constraints:

        len(chunk) <= length_limit
        len(encoding.encode(chunk)) <= token_limit

    Token count is not monotonic with character length: shortening a string
    can actually increase its token count.

    For example, with the tiktoken encoding used by
    `gpt-4o-mini-tts-2025-12-15`:

        "establishment" -> [376, 160388]       # 2 tokens
        "establis"      -> [376, 18122, 276]   # 3 tokens

    Consequently, this function does not assume that a shorter prefix is
    necessarily safer. Instead, for each prospective chunk it:

    1. Checks whether the entire prospective chunk already satisfies both
       limits. If so, it is accepted without further splitting.
    2. Obtains the first semantic chunk independently from a character-based
       splitter and a token-based splitter.
    3. Tests both resulting candidates against both limits.
    4. If either candidate satisfies both limits, accepts the longest such
       candidate.
    5. If neither does, narrows the prospective chunk to the shorter
       candidate and repeats the process.

    The accepted chunk is then removed from the beginning of the remaining
    text and the process repeats until no non-whitespace text remains.

    Args:
        text:
            Text to split.
        model:
            Model name understood by both `tiktoken.encoding_for_model()`
            and `TextSplitter.from_tiktoken_model()`.
        length_limit:
            Maximum number of characters permitted in each returned chunk.
        token_limit:
            Maximum number of model tokens permitted in each returned chunk.

    Returns:
        A list of non-empty, semantically split chunks satisfying both limits.

    Raises:
        ValueError:
            If either limit is not positive.
        RuntimeError:
            If the underlying splitters fail to make progress while trying
            to reduce a chunk that violates one of the limits.
    """
    if length_limit <= 0:
        raise ValueError("length_limit must be greater than 0")

    if token_limit <= 0:
        raise ValueError("token_limit must be greater than 0")

    if not text:
        return []

    encoding = tiktoken.encoding_for_model(model)

    length_splitter = TextSplitter(length_limit)
    token_splitter = TextSplitter.from_tiktoken_model(model, token_limit)

    def token_length(value: str) -> int:
        return len(encoding.encode(value))

    def satisfies_both(value: str) -> bool:
        return len(value) <= length_limit and token_length(value) <= token_limit

    def first_chunk(splitter: TextSplitter, value: str) -> str:
        chunks = splitter.chunks(value)
        # Note: There is no efficient way to get only the first chunk,
        # so we must generate all chunks and take the first one.

        if not chunks:
            raise RuntimeError("TextSplitter returned no chunks for non-empty text")

        return chunks[0]

    def find_next_chunk(value: str) -> str:
        """Find the longest available first semantic chunk known to satisfy
        both limits, recursively narrowing the search space when necessary.
        """
        # TextSplitter trims chunks by default, so perform the same
        # normalization before reasoning about this prospective chunk.
        candidate = value.strip()

        if not candidate:
            return ""

        while True:
            # This check is essential. Token count is not monotonic with
            # character length, so a longer candidate can satisfy the token
            # limit even when one of its shorter prefixes does not.
            if satisfies_both(candidate):
                return candidate

            length_candidate = first_chunk(length_splitter, candidate)
            token_candidate = first_chunk(token_splitter, candidate)

            candidates = (length_candidate, token_candidate)

            # Do not merely select the shorter candidate. Either splitter may
            # happen to produce a candidate that also satisfies the *other*
            # constraint. When that happens, retain the longest known-valid
            # semantic chunk.
            valid_candidates = [value for value in candidates if satisfies_both(value)]

            if valid_candidates:
                return max(valid_candidates, key=len)

            # Neither candidate satisfies both constraints. Narrow the search
            # space to the shorter one and run the meta-splitting process
            # again. A shorter prefix is not assumed to be valid; it will be
            # explicitly checked at the top of the next iteration.
            next_candidate = min(candidates, key=len)

            if len(next_candidate) >= len(candidate):
                raise RuntimeError("Unable to make progress while splitting text: neither splitter produced a smaller candidate satisfying both constraints")

            candidate = next_candidate

    chunks: list[str] = []
    remaining = text

    while remaining:
        # TextSplitter's default behavior discards surrounding whitespace.
        # Removing leading whitespace here makes our position in `remaining`
        # correspond to the beginning of the next returned chunk.
        remaining = remaining.lstrip()

        if not remaining:
            break

        chunk = find_next_chunk(remaining)

        if not chunk:
            raise RuntimeError("Unable to obtain a non-empty chunk from non-empty text")

        # `find_next_chunk()` operates on a prefix of `remaining`, modulo the
        # same trimming behavior used by TextSplitter. Since leading
        # whitespace was removed above, the returned chunk must begin at
        # position zero.
        if not remaining.startswith(chunk):
            raise RuntimeError("TextSplitter returned a chunk that is not a prefix of the remaining text")

        # Defensive verification: these are hard requirements of this
        # function, irrespective of the behavior of the underlying library.
        if len(chunk) > length_limit:
            raise RuntimeError(f"Produced chunk of length {len(chunk)}, exceeding length_limit={length_limit}")

        chunk_token_length = token_length(chunk)
        if chunk_token_length > token_limit:
            raise RuntimeError(f"Produced chunk containing {chunk_token_length} tokens, exceeding token_limit={token_limit}")

        chunks.append(chunk)
        remaining = remaining[len(chunk) :]

    return chunks
