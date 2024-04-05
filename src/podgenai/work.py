from pathlib import Path

import pathvalidate

from podgenai.config import WORK_PATH
from podgenai.content.topic import is_topic_valid


def get_topic_work_path(topic: str) -> Path:
    """Return the working directory for the given topic.

    The directory is created if it does not already exist.
    """
    assert is_topic_valid(topic)
    work_path = WORK_PATH / pathvalidate.sanitize_filepath(topic, platform="auto")
    pathvalidate.validate_filepath(work_path, platform="auto")
    work_path.mkdir(parents=True, exist_ok=True)
    return work_path
