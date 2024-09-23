import os
from pathlib import Path
from typing import Optional

import click

import podgenai.exceptions
from podgenai.config import NUM_SECTIONS_MIN, NUM_SECTIONS_MAX
from podgenai.podgenai import generate_media
from podgenai.content.topic import get_topic, ensure_topic_is_valid
from podgenai.util.openai import ensure_openai_key
from podgenai.util.sys import print_error


@click.command(context_settings={"help_option_names": ["-h", "--help"], "max_content_width": 120})
@click.option("--topic", "-t", type=str, default=None, help="Topic. If not given, the user is prompted for it.")
@click.option(
    "--path",
    "-p",
    type=Path,
    default=None,
    help='Output file or directory path. If an intended file path, it must have an ".mp3" suffix. If a directory, it must exist, and the file name is auto-determined. If not given, the output file is written to the current working directory with an auto-determined file name.',
)
@click.option("--max-sections", "-s", default=None, type=click.IntRange(NUM_SECTIONS_MIN, NUM_SECTIONS_MAX), help=f"Maximum number of sections, between {NUM_SECTIONS_MIN} and {NUM_SECTIONS_MAX}. If not given, it is unrestricted.")
@click.option(
    "--markers/--no-markers",
    "-m/-nm",
    type=bool,
    default=True,
    help="Include markers at the start or end of sections in the generated audio. If `--markers`, markers are included, and this is the default. If `--no-markers`, markers are excluded, as can be appropriate for foreign-language generation.",
)
@click.option(
    "--confirm/--no-confirm",
    "-c/-nc",
    type=bool,
    default=True,
    help="Confirm before full-text and speech generation. If `--confirm`, a confirmation is interactively sought as each step of the workflow progresses, and this is the default. If `--no-confirm`, the full-text and speech are generated without confirmations.",
)
def main(topic: Optional[str], path: Optional[Path], max_sections: Optional[int], markers: bool, confirm: bool) -> None:
    """Generate and write an audiobook podcast mp3 file for the given topic to the given output file path."""
    try:
        ensure_openai_key()

        if not topic:
            topic = get_topic()
        ensure_topic_is_valid(topic)

        if path:
            assert isinstance(path, Path), (path, type(path))
        assert isinstance(markers, bool), (markers, type(markers))
        assert isinstance(confirm, bool), (confirm, type(confirm))

        generate_media(topic, output_path=path, max_sections=max_sections, markers=markers, confirm=confirm)
    except podgenai.exceptions.Error as exc:
        print_error(str(exc))
        print_error(f"Failed to generate for topic: {topic}")
        exit(1)
    except KeyboardInterrupt:
        print()  # This separates "^C" from the subsequent error.
        print_error("Interrupted by user.")
        os._exit(-2)  # Plain `exit` is not used because it may not immediately terminate, with background threads potentially still running.


if __name__ == "__main__":
    main()
