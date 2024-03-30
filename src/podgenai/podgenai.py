import datetime
from pathlib import Path
from typing import Optional

from podgenai.config import REPO_PATH


def generate_podcast(topic: str, *, output_path: Optional[Path] = None) -> Path:
    """Return the output path after generating and writing a podcast to file for the given topic."""
    if output_path is None:
        now = datetime.datetime.now().isoformat(timespec='seconds')
        output_path = REPO_PATH / f'{now} {topic}.mp3'
    return output_path
