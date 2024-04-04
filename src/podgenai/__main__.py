from typing import Optional

import fire
import os
from pathlib import Path

from podgenai.podgenai import generate_media
from podgenai.content.topic import get_topic, is_topic_valid
from podgenai.util.openai import is_openai_key_available
from podgenai.util.sys import print_error


def main(topic: Optional[str] = None, path: Optional[Path] = None, confirm: bool = False) -> None:
    """Generate and write an audiobook podcast mp3 file for the given topic to the given output file path.

    Params:
    * `topic`: Topic. If not given, the user is prompted for it.
    * `path`: Output file or directory path.
        If an intended file path, it must have an ".mp3" suffix. If a directory, it must exist, and the file name is auto-determined.
        If not given, the output file is written to the repo directory with an auto-determined file name.
    * `confirm`: Confirm before full-text generation.
        If true, a confirmation is interactively sought after generating and printing the list of subtopics, before generating the full-text. Its default is false.
    """
    try:
        if not is_openai_key_available():
            exit(1)

        if topic:
            if not is_topic_valid(topic):
                print_error(f"Failed to generate podcast for topic: {topic}")
                exit(2)
        else:
            topic = get_topic()

        if path:
            path = Path(path)
        assert isinstance(confirm, bool), confirm

        if not generate_media(topic, output_path=path, confirm=confirm):
            print_error(f"Failed to generate podcast for topic: {topic}")
            exit(3)
    except KeyboardInterrupt:
        print_error("Interrupted by user.")
        os._exit(-2)  # Plain `exit` is not used because it may not immediately terminate, with background threads potentially still running.


if __name__ == "__main__":
    fire.Fire(main)
