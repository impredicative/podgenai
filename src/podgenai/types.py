from pathlib import Path
from typing import Required, TypedDict


class SpeechTask(TypedDict):
    path: Required[Path]
    text: Required[str]
    portion_num: Required[int]
    num_portions: Required[int]
