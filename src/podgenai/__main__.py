from typing import Optional

import fire
import os
from pathlib import Path

from podgenai.podgenai import generate_podcast
from podgenai.content.topic import get_topic, is_topic_valid
from podgenai.util.openai import is_openai_key_available
from podgenai.util.sys import print_error


def main(topic: Optional[str] = None, path: Optional[Path] = None) -> None:
    """Generate and write an audiobook podcast mp3 file for the given topic to the given output file path.

    Params:
    * `topic`: Topic. If not given, the user is prompted for it.
    * `path`: Output file path. It must have an ".mp3" suffix. If not given, the output file is written to the repo directory.
    """
    try:
        if not is_openai_key_available():
            exit(1)

        if topic:
            if not is_topic_valid(topic):
                print_error(f'Failed to generate podcast for topic: {topic}')
                exit(2)
        else:
            topic = get_topic()

        if path:
            path = Path(path)

        if not generate_podcast(topic, output_path=path):
            print_error(f'Failed to generate podcast for topic: {topic}')
            exit(3)
    except KeyboardInterrupt:
        print_error('Interrupted by user.')
        os._exit(-2)  # Plain `exit` is not used because it may not immediately terminate, with background threads potentially still running.


if __name__ == "__main__":
    fire.Fire(main)
