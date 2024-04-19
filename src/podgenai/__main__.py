from typing import Optional

import fire
import os
from pathlib import Path

import podgenai.exceptions
from podgenai.podgenai import generate_media
from podgenai.content.topic import get_topic, ensure_topic_is_valid
from podgenai.util.openai import ensure_openai_key
from podgenai.util.sys import print_error


def main(topic: Optional[str] = None, path: Optional[Path] = None, confirm: bool = False) -> None:
    """Generate and write an audiobook podcast mp3 file for the given topic to the given output file path.

    Params:
    * `topic` (-t): Topic. If not given, the user is prompted for it.
    * `path (-p)`: Output file or directory path.
        If an intended file path, it must have an ".mp3" suffix. If a directory, it must exist, and the file name is auto-determined.
        If not given, the output file is written to the repo directory with an auto-determined file name.
    * `confirm`: Confirm before full-text and speech generation.
        If true, a confirmation is interactively sought after generating and printing the list of subtopics, before generating the full-text, and also before generating the speech. Its default is false.

    A nonzero exitcode exists if there is an error.
    """
    try:
        ensure_openai_key()

        if not topic:
            topic = get_topic()
        ensure_topic_is_valid(topic)

        if path:
            path = Path(path)

        if not isinstance(confirm, bool):
            raise podgenai.exceptions.InputError("`confirm` (-c) argument has an invalid value. No value is to explicitly be specified for it since it is a boolean.")

        generate_media(topic, output_path=path, confirm=confirm)
    except podgenai.exceptions.Error as exc:
        print_error(str(exc))
        print_error(f"Failed to generate for topic: {topic}")
        exit(1)
    except KeyboardInterrupt:
        print()  # This separates "^C" from the subsequent error.
        print_error("Interrupted by user.")
        os._exit(-2)  # Plain `exit` is not used because it may not immediately terminate, with background threads potentially still running.


if __name__ == "__main__":
    fire.Fire(main)
