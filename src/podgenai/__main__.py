from podgenai.podgenai import generate_podcast
from podgenai.content.topic import get_topic
from podgenai.util.openai import is_openai_key_available
from podgenai.util.sys import print_error


def main() -> None:  # TODO: Use cmdline arg for topic, with cmdline help also supported.
    """Generate and write podcast to file for a user-specified topic."""
    if not is_openai_key_available():
        exit(1)
    topic = get_topic()
    if not generate_podcast(topic):
        print_error(f'Failed to generate podcast for topic: {topic}')
        exit(2)


if __name__ == "__main__":
    main()
