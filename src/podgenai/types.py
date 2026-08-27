from pathlib import Path
from typing import Literal, Required, TypedDict


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
