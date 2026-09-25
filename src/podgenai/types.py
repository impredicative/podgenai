from pathlib import Path
from typing import Literal, NotRequired, Required, TypedDict


class KeyValueOverride(TypedDict):
    key: Required[str]
    value: Required[str]
    override: Required[str]


class TextModel(TypedDict):
    name: Required[str]
    context_window: Required[int]  # In tokens.
    max_output: Required[int]  # In tokens.
    extra_kwargs: Required[dict[str, object]]  # Extra keyword arguments to pass to the client when using this model.
    unsupported_kwargs: NotRequired[set[str]]  # Keyword arguments that are unsupported by this model.
    overridden_kwargs: NotRequired[list[KeyValueOverride]]  # Key value overrides for this model.


class Models(TypedDict):
    knowledge: Required[TextModel]
    text: Required[TextModel]
    tts: Required[str]


class TokenMetric(TypedDict):
    """Token usage for one model request.

    Missing token counts are represented by None.
    """

    prompt_cache_key: Required[str | None]
    input_tokens: Required[int | None]
    cache_read_tokens: Required[int | None]
    cache_write_tokens: Required[int | None]
    output_tokens: Required[int | None]


class SpeechLine(TypedDict):
    speaker: Required[Literal["male", "female"]]
    speech: Required[str]
    tone: Required[str | None]


class SpeechTask(TypedDict):
    path: Required[Path]
    text: Required[str]
    part_num: Required[int]
    num_parts: Required[int]
    voice: Required[str]
    tone: Required[str | None]  # Tone instructions.
    pause_after: Required[float | None]  # In seconds.


class SubtopicDuologue(TypedDict):
    subtopic: Required[str]
    duologue: Required[list[SpeechLine]]


class SubtopicText(TypedDict):
    name: Required[str]
    text: Required[str]


class DeduplicatedSubtopicText(SubtopicText):
    is_deduplicated: Required[bool]
